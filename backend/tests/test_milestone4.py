import pytest
import os
import time
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.job import SimulationJob, SimulationAttempt, FailureAnalysis, WorkerStatus, SimulationArtifact
from app.utils.checksum import calculate_sha256
import app.main as main_module
import app.queue.redis_queue as rq

# ---------------------------------------------------------------------------
# Isolation DB Setup
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_m4.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
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

# ---------------------------------------------------------------------------
# Milestone 4 Tests
# ---------------------------------------------------------------------------

def test_checksum_generation():
    """Verify SHA-256 checksum generation utility."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"cpu-design-automation")
        tmp_path = tmp.name
    try:
        chk = calculate_sha256(tmp_path)
        # sha256("cpu-design-automation")
        assert chk == "c26118414fc10a9e8761f03c0b988dc6e5cd3cf960155c9d2011109f01b48abe"
    finally:
        os.remove(tmp_path)

def test_artifact_model_creation(db_session):
    """Verify SimulationArtifact model is created successfully in DB."""
    job = SimulationJob(id="job-art", design_name="alu", test_name="pass")
    db_session.add(job)
    db_session.commit()
    
    attempt = SimulationAttempt(
        job_id=job.id,
        attempt_number=1,
        status="PASSED"
    )
    db_session.add(attempt)
    db_session.commit()

    artifact = SimulationArtifact(
        job_id=job.id,
        attempt_id=attempt.id,
        artifact_type="waveform",
        filename="waveform.vcd",
        path="/path/to/waveform.vcd",
        size_bytes=100,
        checksum="abcd"
    )
    db_session.add(artifact)
    db_session.commit()

    db_art = db_session.query(SimulationArtifact).filter_by(job_id=job.id).first()
    assert db_art is not None
    assert db_art.filename == "waveform.vcd"
    assert db_art.size_bytes == 100

def test_get_attempts_endpoint(api_client, db_session):
    """Verify GET /jobs/{job_id}/attempts endpoint."""
    job = SimulationJob(id="job-att", design_name="alu", test_name="pass")
    db_session.add(job)
    db_session.commit()
    
    att1 = SimulationAttempt(job_id=job.id, attempt_number=1, status="FAILED", runtime_ms=500)
    att2 = SimulationAttempt(job_id=job.id, attempt_number=2, status="PASSED", runtime_ms=600)
    db_session.add_all([att1, att2])
    db_session.commit()

    # Success case
    res = api_client.get(f"/jobs/{job.id}/attempts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["attempt_number"] == 1
    assert data[1]["attempt_number"] == 2

    # Nonexistent job
    res_404 = api_client.get("/jobs/nonexistent-job-id/attempts")
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Job not found"

def test_get_artifacts_endpoint(api_client, db_session):
    """Verify GET /jobs/{job_id}/artifacts endpoint."""
    job = SimulationJob(id="job-art-list", design_name="alu", test_name="pass")
    db_session.add(job)
    db_session.commit()
    
    att = SimulationAttempt(job_id=job.id, attempt_number=1, status="PASSED")
    db_session.add(att)
    db_session.commit()

    art1 = SimulationArtifact(job_id=job.id, attempt_id=att.id, artifact_type="stdout", filename="stdout.txt", path="/path/1", size_bytes=10, checksum="c1")
    art2 = SimulationArtifact(job_id=job.id, attempt_id=att.id, artifact_type="waveform", filename="waveform.vcd", path="/path/2", size_bytes=20, checksum="c2")
    db_session.add_all([art1, art2])
    db_session.commit()

    # Success case
    res = api_client.get(f"/jobs/{job.id}/artifacts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["filename"] == "stdout.txt"
    assert data[1]["filename"] == "waveform.vcd"
    assert "path" not in data[0] # Verify path is NOT exposed

    # Nonexistent job
    res_404 = api_client.get("/jobs/nonexistent/artifacts")
    assert res_404.status_code == 404

def test_artifact_download_and_path_traversal(api_client, db_session, tmp_path, monkeypatch):
    """Verify artifact download and path traversal security controls."""
    # Set mock ARTIFACT_ROOT to a tmp directory
    artifact_root = tmp_path / "artifacts"
    os.makedirs(artifact_root, exist_ok=True)
    monkeypatch.setenv("ARTIFACT_ROOT", str(artifact_root))

    job = SimulationJob(id="job-dl", design_name="alu", test_name="pass")
    db_session.add(job)
    db_session.commit()
    
    att = SimulationAttempt(job_id=job.id, attempt_number=1, status="PASSED")
    db_session.add(att)
    db_session.commit()

    # Valid file inside ARTIFACT_ROOT
    valid_file = artifact_root / "stdout.txt"
    valid_file.write_text("simulation log output")
    
    art_valid = SimulationArtifact(
        id="art-valid-id",
        job_id=job.id,
        attempt_id=att.id,
        artifact_type="stdout",
        filename="stdout.txt",
        path=str(valid_file),
        size_bytes=len("simulation log output"),
        checksum="c1"
    )
    
    # Traversal file outside ARTIFACT_ROOT
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("secret content")
    art_traversal = SimulationArtifact(
        id="art-traversal-id",
        job_id=job.id,
        attempt_id=att.id,
        artifact_type="stdout",
        filename="secret.txt",
        path=str(outside_file),
        size_bytes=len("secret content"),
        checksum="c2"
    )
    
    db_session.add_all([art_valid, art_traversal])
    db_session.commit()

    # Valid download
    res = api_client.get("/artifacts/art-valid-id")
    assert res.status_code == 200
    assert res.text == "simulation log output"

    # Block path traversal attempt
    res_traversal = api_client.get("/artifacts/art-traversal-id")
    assert res_traversal.status_code == 403
    assert res_traversal.json()["detail"] == "Access denied"

    # Nonexistent artifact
    res_404 = api_client.get("/artifacts/nonexistent-artifact-id")
    assert res_404.status_code == 404

def test_verification_summary_endpoint(api_client, db_session):
    """Verify GET /jobs/{job_id}/summary returns full details for passed and failed jobs."""
    # 1. Passed Job
    job_pass = SimulationJob(id="job-pass-sum", design_name="alu", test_name="pass", status="PASSED", attempt_count=1, exit_code=0)
    db_session.add(job_pass)
    db_session.commit()
    att_pass = SimulationAttempt(job_id=job_pass.id, attempt_number=1, status="PASSED", runtime_ms=500)
    db_session.add(att_pass)
    db_session.commit()

    res = api_client.get(f"/jobs/{job_pass.id}/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["status"] == "PASSED"
    assert summary["total_runtime_ms"] == 500
    assert summary["latest_analysis_summary"] is None

    # 2. Failed Job
    job_fail = SimulationJob(id="job-fail-sum", design_name="alu", test_name="fail", status="FAILED", attempt_count=1, exit_code=1, failure_category="ASSERTION_FAILURE")
    db_session.add(job_fail)
    db_session.commit()
    att_fail = SimulationAttempt(job_id=job_fail.id, attempt_number=1, status="FAILED", runtime_ms=400)
    db_session.add(att_fail)
    
    analysis = FailureAnalysis(
        job_id=job_fail.id,
        analyzer_type="rule_based",
        failure_category="ASSERTION_FAILURE",
        summary="Test assert failed",
        suspected_root_cause="ALU mismatch",
        recommended_fix="Check ALU SV file",
        confidence=1.0
    )
    db_session.add(analysis)
    db_session.commit()

    res_fail = api_client.get(f"/jobs/{job_fail.id}/summary")
    assert res_fail.status_code == 200
    summary_fail = res_fail.json()
    assert summary_fail["status"] == "FAILED"
    assert summary_fail["failure_category"] == "ASSERTION_FAILURE"
    assert summary_fail["latest_analysis_summary"] == "Test assert failed"
    assert summary_fail["recommended_fix"] == "Check ALU SV file"

def test_verification_history(api_client, db_session):
    """Verify chronological event history mapping."""
    job = SimulationJob(id="job-hist", design_name="alu", test_name="fail", status="FAILED", created_at=time_from_offset(-10))
    db_session.add(job)
    db_session.commit()

    att1 = SimulationAttempt(job_id=job.id, attempt_number=1, status="FAILED", started_at=time_from_offset(-8), completed_at=time_from_offset(-7), created_at=time_from_offset(-8))
    analysis = FailureAnalysis(job_id=job.id, analyzer_type="rule_based", failure_category="ASSERTION_FAILURE", summary="mismatch", suspected_root_cause="x", recommended_fix="y", confidence=1.0, created_at=time_from_offset(-5))
    att2 = SimulationAttempt(job_id=job.id, attempt_number=2, status="PASSED", started_at=time_from_offset(-3), completed_at=time_from_offset(-2), created_at=time_from_offset(-3))
    
    db_session.add_all([att1, analysis, att2])
    db_session.commit()

    res = api_client.get(f"/jobs/{job.id}/history")
    assert res.status_code == 200
    history = res.json()
    
    # Assert event names
    events = [h["event"] for h in history]
    assert "JOB_CREATED" in events
    assert "SIMULATION_STARTED" in events
    assert "SIMULATION_FAILED" in events
    assert "FAILURE_ANALYZED" in events
    assert "REVALIDATION_REQUESTED" in events

def test_prometheus_expanded_metrics(api_client, db_session):
    """Verify expanded Prometheus metrics exist in GET /metrics endpoint."""
    res = api_client.get("/metrics")
    assert res.status_code == 200
    assert "simulations_total" in res.text
    assert "simulations_passed_total" in res.text
    assert "simulations_failed_total" in res.text
    assert "simulation_runtime_seconds" in res.text
    assert "artifacts_created_total" in res.text
    assert "artifact_bytes_total" in res.text

# ---------------------------------------------------------------------------
# Helper function
# ---------------------------------------------------------------------------
def time_from_offset(seconds_offset):
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(seconds=seconds_offset)
