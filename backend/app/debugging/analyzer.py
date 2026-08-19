from abc import ABC, abstractmethod
from typing import Dict, Any, List
import os

class FailureAnalyzer(ABC):
    @abstractmethod
    def analyze(self, design_name: str, test_name: str, exit_code: int, stdout: str, stderr: str, runtime_ms: int) -> Dict[str, Any]:
        """
        Analyze a failed simulation and return a structured dictionary containing:
        - failure_category: str
        - summary: str
        - suspected_root_cause: str
        - evidence: List[str]
        - recommended_fix: str
        - confidence: float
        - analyzer_type: str
        """
        pass

class RuleBasedFailureAnalyzer(FailureAnalyzer):
    def analyze(self, design_name: str, test_name: str, exit_code: int, stdout: str, stderr: str, runtime_ms: int) -> Dict[str, Any]:
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
            
            # Extract evidence
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
            "analyzer_type": "rule_based"
        }

class LLMFailureAnalyzer(FailureAnalyzer):
    def analyze(self, design_name: str, test_name: str, exit_code: int, stdout: str, stderr: str, runtime_ms: int) -> Dict[str, Any]:
        # This is a stub for the LLM analyzer to demonstrate the abstraction without requiring an external API key.
        return {
            "failure_category": "UNKNOWN",
            "summary": "LLM Analysis Stub",
            "suspected_root_cause": "The LLM provider is not fully implemented in this prototype.",
            "evidence": ["LLM Provider Mock"],
            "recommended_fix": "Implement the actual LLM API call.",
            "confidence": 0.5,
            "analyzer_type": "llm"
        }

def get_failure_analyzer() -> FailureAnalyzer:
    analyzer_type = os.getenv("FAILURE_ANALYZER", "rule_based").lower()
    if analyzer_type == "llm":
        return LLMFailureAnalyzer()
    return RuleBasedFailureAnalyzer()
