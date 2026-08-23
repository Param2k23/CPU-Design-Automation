import pytest
import os
import json
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app, METRICS
from app.models.job import SimulationJob, SimulationAttempt, FailureAnalysis, WorkerStatus, SimulationArtifact, Design, RegressionRun
import app.main as main_module
from app.debugging.analyzer import RuleBasedFailureAnalyzer, LLMFailureAnalyzer, HybridFailureAnalyzer, collect_evidence
from app.debugging.llm_provider import GenericLLMProvider, get_llm_provider

# Isolated DB for Milestone 6 tests
TEST_DB_URL = "sqlite:///./test_m6.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed default designs
        for d_name in ["alu", "fifo", "register_file", "cache"]:
            design = Design(
                name=d_name,
                description=f"Standard {d_name.upper()} design",
                rtl_path=f"rtl/{d_name}/{d_name}.sv",
                testbench_path=f"testbenches/{d_name}",
                enabled=True
            )
            db.add(design)
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def api_client(db_session, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(main_module, "enqueue_job", lambda job_id, priority=None: None)
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture()
def mock_llm(monkeypatch):
    def mock_analyze(self, evidence: dict):
        return {
            "failure_category": "ASSERTION_FAILURE",
            "summary": "Mock LLM Summary of assertion failure",
            "suspected_root_cause": "Expected value did not match RTL output",
            "evidence": ["Assertion failed: expected 5, got 0"],
            "recommended_fix": "Fix ALU addition logic in alu.sv",
            "confidence": 0.85,
            "affected_component": "ALU",
            "suggested_next_test": "tb_alu_pass.cpp"
        }
    monkeypatch.setattr(GenericLLMProvider, "analyze_failure", mock_analyze)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("LLM_API_KEY", "mock-secret-key")


# 1. Rule-based analyzer still works
def test_rule_based_analyzer_works():
    analyzer = RuleBasedFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Assertion failed at line 42",
        runtime_ms=100
    )
    assert res["failure_category"] == "ASSERTION_FAILURE"
    assert res["confidence"] == 1.0
    assert "Assertion failed at line 42" in res["evidence"]


# 2. LLM analyzer returns valid structured output
def test_llm_analyzer_success(mock_llm):
    analyzer = LLMFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Assertion failed at line 42",
        runtime_ms=100
    )
    assert res["failure_category"] == "ASSERTION_FAILURE"
    assert res["confidence"] == 0.85
    assert res["analyzer_type"] == "llm"
    assert res["affected_component"] == "ALU"
    assert res["suggested_next_test"] == "tb_alu_pass.cpp"
    assert res["analysis_status"] == "SUCCESS"


# 3. Invalid LLM output falls back safely
def test_llm_analyzer_invalid_format_fallback(monkeypatch):
    def mock_invalid_analyze(self, evidence: dict):
        return {
            "failure_category": "INVALID_CATEGORY_NAME_NOT_IN_LITERAL",
            "summary": "Bad",
            "suspected_root_cause": "Unknown",
            "evidence": [],
            "recommended_fix": "Fix",
            "confidence": 1.5, # Out of range
            "affected_component": "ALU",
            "suggested_next_test": "test"
        }
    monkeypatch.setattr(GenericLLMProvider, "analyze_failure", mock_invalid_analyze)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "mock-key")

    analyzer = LLMFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Assertion failed at line 42",
        runtime_ms=100
    )
    # Falls back to deterministic (Rule-based)
    assert res["failure_category"] == "ASSERTION_FAILURE"
    assert res["confidence"] == 1.0
    assert res["analysis_status"] == "FAILED"


# 4. LLM disabled -> deterministic fallback
def test_llm_disabled_fallback(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    analyzer = LLMFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=-1,
        stdout="Timeout",
        stderr="Timeout after 1000s",
        runtime_ms=1000
    )
    assert res["failure_category"] == "TIMEOUT"
    assert res["analysis_status"] == "FAILED"


# 5. Missing API key -> deterministic fallback
def test_llm_missing_api_key_fallback(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    analyzer = LLMFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Error",
        stderr="Verilator syntax error",
        runtime_ms=50
    )
    assert res["failure_category"] == "COMPILE_ERROR"
    assert res["analysis_status"] == "FAILED"


# 6. Evidence truncation works
def test_evidence_truncation():
    long_log = "X" * 5000
    evidence = collect_evidence(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout=long_log,
        stderr="Error",
        runtime_ms=10
    )
    assert len(evidence["stdout"]) < 2500
    assert "[TRUNCATED DUE TO SIZE]" in evidence["stdout"]


# 7. Sensitive values are not exposed
def test_evidence_sanitization():
    evidence = collect_evidence(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Normal output",
        stderr="Error message",
        runtime_ms=10,
        regression_context={"LLM_API_KEY": "secret-12345", "password": "mypassword"}
    )
    assert "LLM_API_KEY" not in evidence["regression_context"]
    assert "password" not in evidence["regression_context"]


# 8. Analysis is persisted
def test_analysis_persistence(api_client, db_session, mock_llm):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Error in ALU behavior",
        runtime_ms=100
    )
    db_session.add(job)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/analyze", json={"analyzer": "llm"})
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job.id
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4o"
    assert data["affected_component"] == "ALU"
    assert data["analysis_status"] == "SUCCESS"

    db_analysis = db_session.query(FailureAnalysis).filter(FailureAnalysis.job_id == job.id).first()
    assert db_analysis is not None
    assert db_analysis.provider == "openai"
    assert db_analysis.model == "gpt-4o"
    assert db_analysis.analysis_source == "ORIGINAL"


# 9. Multiple analyses are preserved
def test_multiple_analyses_preserved(api_client, db_session, mock_llm):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Error in ALU behavior",
        runtime_ms=100
    )
    db_session.add(job)
    db_session.commit()

    # Trigger first analysis
    api_client.post(f"/jobs/{job.id}/analyze", json={"analyzer": "rule_based"})
    # Trigger second analysis
    api_client.post(f"/jobs/{job.id}/analyze", json={"analyzer": "llm"})

    analyses = db_session.query(FailureAnalysis).filter(FailureAnalysis.job_id == job.id).all()
    assert len(analyses) == 2
    types = [a.analyzer_type for a in analyses]
    assert "rule_based" in types
    assert "llm" in types


# 10. Hybrid analyzer chooses deterministic analysis when confidence is high
def test_hybrid_analyzer_high_confidence(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "mock")
    analyzer = HybridFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="syntax error",
        stderr="verilator syntax error at line 5",
        runtime_ms=50
    )
    # High confidence (1.0) on compile error, does not need LLM
    assert res["failure_category"] == "COMPILE_ERROR"
    assert res["analyzer_type"] == "hybrid"
    assert res["provider"] is None


# 11. Hybrid analyzer invokes LLM for ambiguous failures
def test_hybrid_analyzer_invokes_llm_for_ambiguous(mock_llm):
    analyzer = HybridFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Strange output",
        stderr="Simulation crashed unexpectedly",
        runtime_ms=200
    )
    # Ambiguous category and low rule-based confidence (0.8 or 0.1) -> invokes LLM
    assert res["failure_category"] == "ASSERTION_FAILURE" # from LLM mock
    assert res["analyzer_type"] == "hybrid"
    assert res["provider"] == "openai"


# 12. LLM failure does not crash the worker
def test_llm_failure_does_not_crash(monkeypatch):
    def mock_raise_error(self, evidence: dict):
        raise RuntimeError("API Timeout")
    monkeypatch.setattr(GenericLLMProvider, "analyze_failure", mock_raise_error)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "mock")

    analyzer = LLMFailureAnalyzer()
    res = analyzer.analyze(
        design_name="alu",
        test_name="fail",
        exit_code=1,
        stdout="Crash log",
        stderr="Error",
        runtime_ms=10
    )
    assert res["failure_category"] == "SIMULATION_ERROR" # rule-based fallback
    assert res["analysis_status"] == "FAILED"


# 13. Debug endpoint works
def test_debug_endpoint_works(api_client, db_session, mock_llm):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Error in ALU behavior",
        runtime_ms=100
    )
    db_session.add(job)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/debug", json={"analyzer": "llm", "auto_revalidate": False})
    assert response.status_code == 200
    data = response.json()
    assert data["job_status"] == "FAILED"
    assert data["revalidated"] is False
    assert data["analysis"]["suspected_root_cause"] == "Expected value did not match RTL output"


# 14. Debug endpoint rejects non-failed jobs
def test_debug_endpoint_rejects_non_failed(api_client, db_session):
    job = SimulationJob(
        design_name="alu",
        test_name="pass",
        status="PASSED",
        exit_code=0
    )
    db_session.add(job)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/debug", json={"analyzer": "hybrid"})
    assert response.status_code == 400
    assert "Only failed jobs can be debugged" in response.json()["detail"]


# 15. Revalidation remains functional
def test_revalidation_remains_functional(api_client, db_session):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1
    )
    db_session.add(job)
    db_session.commit()

    analysis = FailureAnalysis(
        job_id=job.id,
        analyzer_type="rule_based",
        summary="A",
        suspected_root_cause="B",
        recommended_fix="C",
        confidence=0.9
    )
    db_session.add(analysis)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/revalidate", json={"triggering_analysis_id": analysis.id})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    
    # Verify in DB
    db_job = db_session.query(SimulationJob).filter(SimulationJob.id == job.id).first()
    assert db_job.triggering_analysis_id == analysis.id


# 16. Regression intelligence works
def test_regression_intelligence(api_client, db_session):
    reg = RegressionRun(
        name="test-intel-reg",
        status="FAILED",
        total_jobs=2
    )
    db_session.add(reg)
    db_session.commit()

    job1 = SimulationJob(
        design_name="alu",
        test_name="fail1",
        status="FAILED",
        exit_code=1,
        failure_category="ASSERTION_FAILURE",
        stderr="Assertion failed: expected 5, got 0",
        regression_id=reg.id
    )
    job2 = SimulationJob(
        design_name="alu",
        test_name="fail2",
        status="FAILED",
        exit_code=1,
        failure_category="TIMEOUT",
        stderr="Timeout occurred",
        regression_id=reg.id
    )
    db_session.add(job1)
    db_session.add(job2)
    db_session.commit()

    response = api_client.get(f"/regressions/{reg.id}/intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["total_failures"] == 2
    assert data["unique_failure_clusters"] == 2
    assert "ASSERTION_FAILURE" in data["failure_categories"]
    assert "TIMEOUT" in data["failure_categories"]
    assert "alu" in data["affected_designs"]


# 17. Duplicate failure clusters avoid duplicate LLM analysis
def test_failure_cluster_analysis_reuse(api_client, db_session, mock_llm):
    # Reset in-memory metric
    METRICS["analysis_reused_total"] = 0

    job1 = SimulationJob(
        design_name="alu",
        test_name="fail1",
        status="FAILED",
        exit_code=1,
        failure_category="ASSERTION_FAILURE",
        stderr="Assertion failed at line 10"
    )
    job2 = SimulationJob(
        design_name="alu",
        test_name="fail2",
        status="FAILED",
        exit_code=1,
        failure_category="ASSERTION_FAILURE",
        stderr="Assertion failed at line 99" # Different message but normalizes to same error
    )
    db_session.add(job1)
    db_session.add(job2)
    db_session.commit()

    # Analyze first job - will be ORIGINAL
    resp1 = api_client.post(f"/jobs/{job1.id}/analyze", json={"analyzer": "llm"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["analysis_source"] == "ORIGINAL"

    # Analyze second job - will be REUSED from cache
    resp2 = api_client.post(f"/jobs/{job2.id}/analyze", json={"analyzer": "llm"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["analysis_source"] == "REUSED"
    assert data2["summary"] == data1["summary"]
    
    assert METRICS["analysis_reused_total"] == 1


# 18. Analyses endpoints
def test_analyses_endpoints(api_client, db_session):
    job = SimulationJob(
        design_name="fifo",
        test_name="fail",
        status="FAILED",
        exit_code=1
    )
    db_session.add(job)
    db_session.commit()

    analysis = FailureAnalysis(
        job_id=job.id,
        analyzer_type="rule_based",
        summary="Summary test",
        suspected_root_cause="Cause test",
        recommended_fix="Fix test",
        confidence=0.8
    )
    db_session.add(analysis)
    db_session.commit()

    # Test GET list
    resp_list = api_client.get(f"/jobs/{job.id}/analyses")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1

    # Test GET single
    resp_single = api_client.get(f"/jobs/{job.id}/analyses/{analysis.id}")
    assert resp_single.status_code == 200
    assert resp_single.json()["summary"] == "Summary test"


# 19. Prometheus metrics exposed
def test_prometheus_ai_metrics(api_client):
    METRICS["analysis_total"] = 5
    METRICS["analysis_reused_total"] = 2
    METRICS["auto_revalidation_total"] = 1

    response = api_client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "cpu_verification_analysis_total 5" in text
    assert "cpu_verification_analysis_reused_total 2" in text
    assert "cpu_verification_auto_revalidation_total 1" in text


# 20. Triggering analysis associated to SimulationAttempt
def test_attempt_triggering_analysis_association(db_session, monkeypatch):
    job = SimulationJob(
        id=str(uuid.uuid4()),
        design_name="alu",
        test_name="pass",
        status="QUEUED",
        priority="normal",
        triggering_analysis_id="mock-analysis-id"
    )
    db_session.add(job)
    db_session.commit()

    # Mock verilator run to complete successfully
    import app.workers.scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module, "run_verilator", lambda r, t, o, coverage_enabled=False: (0, "Success", "", 100))
    
    # We will simulate the worker scheduler processing the job directly:
    from app.workers.scheduler import process_job
    monkeypatch.setattr(scheduler_module, "SessionLocal", TestingSessionLocal)
    # Set worker id in env
    monkeypatch.setenv("WORKER_CONCURRENCY", "1")
    
    # Trigger process job (which usually runs in worker thread)
    process_job(job.id)
    
    # Re-fetch attempt from DB
    db_session.expire_all()
    attempt = db_session.query(SimulationAttempt).filter(SimulationAttempt.job_id == job.id).first()
    assert attempt is not None
    assert attempt.triggering_analysis_id == "mock-analysis-id"

# 21. Revalidation without triggering_analysis_id still works
def test_revalidation_without_analysis_id(api_client, db_session):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1
    )
    db_session.add(job)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/revalidate", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    assert data["triggering_analysis_id"] is None

# 22. Invalid triggering analysis ID is handled safely (returns 400)
def test_revalidation_invalid_analysis_id(api_client, db_session):
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1
    )
    db_session.add(job)
    db_session.commit()

    response = api_client.post(f"/jobs/{job.id}/revalidate", json={"triggering_analysis_id": "nonexistent-id"})
    assert response.status_code == 400
    assert "Triggering analysis not found" in response.json()["detail"]

# 23. Genuinely different failure clusters do not reuse analysis
def test_different_failure_clusters_do_not_reuse(api_client, db_session, mock_llm):
    # Reset in-memory metric
    METRICS["analysis_reused_total"] = 0

    job1 = SimulationJob(
        design_name="alu",
        test_name="fail1",
        status="FAILED",
        exit_code=1,
        failure_category="ASSERTION_FAILURE",
        stderr="Assertion failed: expected 5, got 0"
    )
    job2 = SimulationJob(
        design_name="alu",
        test_name="fail2",
        status="FAILED",
        exit_code=-1, # TIMEOUT - different failure cluster!
        failure_category="TIMEOUT",
        stderr="Simulation timeout after 500s"
    )
    db_session.add(job1)
    db_session.add(job2)
    db_session.commit()

    # Analyze first job - will be ORIGINAL
    resp1 = api_client.post(f"/jobs/{job1.id}/analyze", json={"analyzer": "llm"})
    assert resp1.status_code == 200
    assert resp1.json()["analysis_source"] == "ORIGINAL"

    # Analyze second job - should NOT reuse from cache, because category and norm_err are totally different!
    resp2 = api_client.post(f"/jobs/{job2.id}/analyze", json={"analyzer": "llm"})
    assert resp2.status_code == 200
    assert resp2.json()["analysis_source"] == "ORIGINAL" # Should not be REUSED
    assert METRICS["analysis_reused_total"] == 0

