from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import json
import logging
from pydantic import BaseModel, Field, ValidationError
from typing import Literal

from app.debugging.llm_provider import get_llm_provider

logger = logging.getLogger("analyzer")

# Truncation limits for logs
MAX_STDOUT_CHARS = 2000
MAX_STDERR_CHARS = 2000
MAX_COMPILE_LOG_CHARS = 2000
MAX_SIMULATION_LOG_CHARS = 2000

class LLMDiagnosis(BaseModel):
    failure_category: Literal["TIMEOUT", "COMPILE_ERROR", "ASSERTION_FAILURE", "SIMULATION_ERROR", "UNKNOWN"]
    summary: str
    suspected_root_cause: str
    evidence: List[str]
    recommended_fix: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    affected_component: str
    suggested_next_test: str

class FailureAnalyzer(ABC):
    @abstractmethod
    def analyze(
        self,
        design_name: str,
        test_name: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        runtime_ms: int,
        rtl_path: Optional[str] = None,
        testbench_path: Optional[str] = None,
        compile_logs: Optional[str] = None,
        simulation_logs: Optional[str] = None,
        failure_category: Optional[str] = None,
        artifact_metadata: Optional[List[Dict[str, Any]]] = None,
        attempt_number: int = 1,
        regression_context: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze a failed simulation and return a structured dictionary containing:
        - failure_category: str
        - summary: str
        - suspected_root_cause: str
        - evidence: List[str]
        - recommended_fix: str
        - confidence: float
        - analyzer_type: str
        - affected_component: Optional[str]
        - suggested_next_test: Optional[str]
        - analysis_status: str (e.g. "SUCCESS", "FAILED")
        - provider: Optional[str]
        - model: Optional[str]
        """
        pass

def safe_truncate(text: Optional[str], max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n... [TRUNCATED DUE TO SIZE] ...\n" + text[-half:]

def collect_evidence(
    design_name: str,
    test_name: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    runtime_ms: int,
    rtl_path: Optional[str] = None,
    testbench_path: Optional[str] = None,
    compile_logs: Optional[str] = None,
    simulation_logs: Optional[str] = None,
    failure_category: Optional[str] = None,
    artifact_metadata: Optional[List[Dict[str, Any]]] = None,
    attempt_number: int = 1,
    regression_context: Optional[Dict[str, Any]] = None,
    previous_analyses: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Construct a bounded, serializable JSON evidence package.
    """
    # Check waveform availability in artifact metadata
    waveform_available = False
    if artifact_metadata:
        for a in artifact_metadata:
            fname = (a.get("filename") or "").lower()
            atype = (a.get("artifact_type") or "").lower()
            if "vcd" in fname or "wave" in fname or "wave" in atype or "vcd" in atype:
                waveform_available = True
                break

    # Construct the evidence dict
    evidence = {
        "design_name": design_name,
        "test_name": test_name,
        "exit_code": exit_code,
        "runtime_ms": runtime_ms,
        "failure_category": failure_category or "UNKNOWN",
        "attempt_number": attempt_number,
        "waveform_available": waveform_available,
        "stdout": safe_truncate(stdout, MAX_STDOUT_CHARS),
        "stderr": safe_truncate(stderr, MAX_STDERR_CHARS),
        "compile_logs": safe_truncate(compile_logs, MAX_COMPILE_LOG_CHARS),
        "simulation_logs": safe_truncate(simulation_logs, MAX_SIMULATION_LOG_CHARS),
        "artifact_metadata": artifact_metadata or [],
        "regression_context": regression_context or {},
        "previous_analyses": previous_analyses or []
    }
    
    # Sanitize evidence: remove sensitive keys if any
    sensitive_keys = ["API_KEY", "SECRET", "PASSWORD", "CREDENTIALS", "TOKEN"]
    
    def sanitize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items() if not any(sk in k.upper() for sk in sensitive_keys)}
        elif isinstance(obj, list):
            return [sanitize(x) for x in obj]
        elif isinstance(obj, str):
            # Mask paths that contain sensitive names, or just pass
            return obj
        return obj

    return sanitize(evidence)

class RuleBasedFailureAnalyzer(FailureAnalyzer):
    def analyze(
        self,
        design_name: str,
        test_name: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        runtime_ms: int,
        rtl_path: Optional[str] = None,
        testbench_path: Optional[str] = None,
        compile_logs: Optional[str] = None,
        simulation_logs: Optional[str] = None,
        failure_category: Optional[str] = None,
        artifact_metadata: Optional[List[Dict[str, Any]]] = None,
        attempt_number: int = 1,
        regression_context: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        stdout_lower = stdout.lower() if stdout else ""
        stderr_lower = stderr.lower() if stderr else ""

        category = "UNKNOWN"
        summary = "An unknown error occurred during simulation."
        cause = "Unable to determine cause deterministically."
        evidence = []
        fix = "Manually inspect the simulation logs and waveforms."
        confidence = 0.1

        if exit_code == -1 or exit_code == -2 or "timeout" in stderr_lower or "timeout" in stdout_lower:
            category = "TIMEOUT"
            summary = "The simulation timed out."
            cause = "The simulation ran longer than the allowed time limit. This could be an infinite loop or a hanging testbench."
            evidence = ["Exit code indicates timeout or 'timeout' found in logs."]
            fix = "Check for infinite loops in state machines or un-triggered assertions in the testbench."
            confidence = 0.95
        elif "syntax error" in stderr_lower or "error:" in stderr_lower and "verilator" in stderr_lower:
            category = "COMPILE_ERROR"
            summary = "The RTL failed to compile."
            cause = "There is a syntax error or a structural issue in the SystemVerilog code."
            
            lines = stderr.splitlines()
            for line in lines:
                if "error" in line.lower():
                    evidence.append(line.strip())
                    
            if not evidence:
                evidence = ["Compilation exited with non-zero status but no explicit 'error' string found."]
                
            fix = "Fix the syntax error at the line indicated in the evidence."
            confidence = 1.0
        elif "assert" in stderr_lower or "assert" in stdout_lower or "assertion" in stderr_lower or "assertion" in stdout_lower:
            category = "ASSERTION_FAILURE"
            summary = "A testbench assertion failed."
            cause = "The RTL produced an output that did not match the expected value in the testbench."
            
            lines = (stdout + "\n" + stderr).splitlines()
            for line in lines:
                if "assert" in line.lower() or "fail" in line.lower():
                    evidence.append(line.strip())
                    
            fix = "Investigate the failing scenario in the RTL (e.g., check ALU operation). Run the simulation with waveform dumping enabled to trace the logic."
            confidence = 1.0
        elif exit_code != 0:
            category = "SIMULATION_ERROR"
            summary = "The simulation process crashed or exited with a non-zero code."
            cause = f"Process exited with code {exit_code}."
            evidence = [f"Exit code: {exit_code}"]
            fix = "Check if the testbench explicitly calls exit() with a non-zero status or if there is a segmentation fault."
            confidence = 0.8

        return {
            "failure_category": category,
            "summary": summary,
            "suspected_root_cause": cause,
            "evidence": evidence,
            "recommended_fix": fix,
            "confidence": confidence,
            "analyzer_type": "rule_based",
            "affected_component": design_name.upper(),
            "suggested_next_test": None,
            "analysis_status": "SUCCESS",
            "provider": None,
            "model": None,
            "prompt_id": None
        }

class LLMFailureAnalyzer(FailureAnalyzer):
    def analyze(
        self,
        design_name: str,
        test_name: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        runtime_ms: int,
        rtl_path: Optional[str] = None,
        testbench_path: Optional[str] = None,
        compile_logs: Optional[str] = None,
        simulation_logs: Optional[str] = None,
        failure_category: Optional[str] = None,
        artifact_metadata: Optional[List[Dict[str, Any]]] = None,
        attempt_number: int = 1,
        regression_context: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        provider = get_llm_provider()
        
        # Bounded evidence package
        evidence_pkg = collect_evidence(
            design_name=design_name,
            test_name=test_name,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            runtime_ms=runtime_ms,
            rtl_path=rtl_path,
            testbench_path=testbench_path,
            compile_logs=compile_logs,
            simulation_logs=simulation_logs,
            failure_category=failure_category,
            artifact_metadata=artifact_metadata,
            attempt_number=attempt_number,
            regression_context=regression_context,
            previous_analyses=previous_analyses
        )

        if not provider:
            # Fall back to RuleBasedFailureAnalyzer
            logger.info("LLM provider unavailable. Falling back to Rule-Based analysis.")
            rule_analyzer = RuleBasedFailureAnalyzer()
            res = rule_analyzer.analyze(
                design_name=design_name,
                test_name=test_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                runtime_ms=runtime_ms,
                rtl_path=rtl_path,
                testbench_path=testbench_path,
                compile_logs=compile_logs,
                simulation_logs=simulation_logs,
                failure_category=failure_category,
                artifact_metadata=artifact_metadata,
                attempt_number=attempt_number,
                regression_context=regression_context,
                previous_analyses=previous_analyses,
                **kwargs
            )
            res["analyzer_type"] = "llm"
            res["analysis_status"] = "FAILED"  # Mark that LLM failed/fallback was used
            return res

        try:
            # Invoke LLM
            llm_result = provider.analyze_failure(evidence_pkg)
            
            # Validate response schema
            diagnosis = LLMDiagnosis(**llm_result)
            
            return {
                "failure_category": diagnosis.failure_category,
                "summary": diagnosis.summary,
                "suspected_root_cause": diagnosis.suspected_root_cause,
                "evidence": diagnosis.evidence,
                "recommended_fix": diagnosis.recommended_fix,
                "confidence": diagnosis.confidence,
                "analyzer_type": "llm",
                "affected_component": diagnosis.affected_component,
                "suggested_next_test": diagnosis.suggested_next_test,
                "analysis_status": "SUCCESS",
                "provider": provider.provider,
                "model": provider.model,
                "prompt_id": "v1"
            }
        except Exception as e:
            logger.error(f"LLM failure analysis encountered error: {str(e)}")
            # Fallback to rule-based
            rule_analyzer = RuleBasedFailureAnalyzer()
            res = rule_analyzer.analyze(
                design_name=design_name,
                test_name=test_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                runtime_ms=runtime_ms,
                rtl_path=rtl_path,
                testbench_path=testbench_path,
                compile_logs=compile_logs,
                simulation_logs=simulation_logs,
                failure_category=failure_category,
                artifact_metadata=artifact_metadata,
                attempt_number=attempt_number,
                regression_context=regression_context,
                previous_analyses=previous_analyses,
                **kwargs
            )
            res["analyzer_type"] = "llm"
            res["analysis_status"] = "FAILED"
            return res

class HybridFailureAnalyzer(FailureAnalyzer):
    def analyze(
        self,
        design_name: str,
        test_name: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        runtime_ms: int,
        rtl_path: Optional[str] = None,
        testbench_path: Optional[str] = None,
        compile_logs: Optional[str] = None,
        simulation_logs: Optional[str] = None,
        failure_category: Optional[str] = None,
        artifact_metadata: Optional[List[Dict[str, Any]]] = None,
        attempt_number: int = 1,
        regression_context: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # 1. Run RuleBasedFailureAnalyzer first
        rule_analyzer = RuleBasedFailureAnalyzer()
        rule_result = rule_analyzer.analyze(
            design_name=design_name,
            test_name=test_name,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            runtime_ms=runtime_ms,
            rtl_path=rtl_path,
            testbench_path=testbench_path,
            compile_logs=compile_logs,
            simulation_logs=simulation_logs,
            failure_category=failure_category,
            artifact_metadata=artifact_metadata,
            attempt_number=attempt_number,
            regression_context=regression_context,
            previous_analyses=previous_analyses,
            **kwargs
        )
        
        # 2. Check confidence
        # If confidence is high (e.g. >= 0.95) and category is known, return deterministic result
        if rule_result["confidence"] >= 0.95 and rule_result["failure_category"] != "UNKNOWN":
            rule_result["analyzer_type"] = "hybrid"
            return rule_result
            
        # 3. Otherwise, invoke LLM analyzer if enabled
        llm_analyzer = LLMFailureAnalyzer()
        llm_result = llm_analyzer.analyze(
            design_name=design_name,
            test_name=test_name,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            runtime_ms=runtime_ms,
            rtl_path=rtl_path,
            testbench_path=testbench_path,
            compile_logs=compile_logs,
            simulation_logs=simulation_logs,
            failure_category=failure_category,
            artifact_metadata=artifact_metadata,
            attempt_number=attempt_number,
            regression_context=regression_context,
            previous_analyses=previous_analyses,
            **kwargs
        )
        
        if llm_result["analysis_status"] == "SUCCESS":
            # Successfully got LLM result, change type to hybrid and merge
            llm_result["analyzer_type"] = "hybrid"
            # Merge rule-based evidence if not already present
            merged_evidence = list(set(rule_result["evidence"] + llm_result["evidence"]))
            llm_result["evidence"] = merged_evidence
            return llm_result
        else:
            # LLM failed, return the rule-based result marked as hybrid type
            rule_result["analyzer_type"] = "hybrid"
            return rule_result

def get_failure_analyzer(analyzer_name: str = "hybrid") -> FailureAnalyzer:
    name = analyzer_name.lower()
    if name == "rule_based" or name == "deterministic":
        return RuleBasedFailureAnalyzer()
    elif name == "llm":
        return LLMFailureAnalyzer()
    else:
        return HybridFailureAnalyzer()
