import pytest
import os
import re
import uuid
import tempfile
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.job import SimulationJob, SimulationAttempt, FailureAnalysis, WorkerStatus, SimulationArtifact, Design, RegressionRun
from app.schemas.job import JobCreate, JobResponse
import app.main as main_module

# Isolated DB for Milestone 5 tests
TEST_DB_URL = "sqlite:///./test_m5.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Re-seed default designs in test database
    try:
        # Resolve project root dynamically
        current_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = None
        while True:
            if os.path.exists(os.path.join(current_dir, "rtl")) and os.path.exists(os.path.join(current_dir, "testbenches")):
                project_root = current_dir
                break
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        if not project_root:
            project_root = os.path.abspath(".")

        for d_name in ["alu", "fifo", "register_file", "cache"]:
            rtl_p = os.path.abspath(os.path.join(project_root, "rtl", d_name, f"{d_name}.sv"))
            tb_p = os.path.abspath(os.path.join(project_root, "testbenches", d_name))
            design = Design(
                name=d_name,
                description=f"Standard {d_name.upper()} design",
                rtl_path=rtl_p,
                testbench_path=tb_p,
                enabled=True
            )
            db.add(design)
        db.commit()
    except Exception:
        db.rollback()
        
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


def test_design_creation(api_client, db_session):
    # 1. Design creation
    # Create temp directory for validation
    temp_dir = tempfile.mkdtemp()
    try:
        # Create temp rtl and tb files inside project root to pass validation
        # Resolve project root dynamically
        current_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = None
        while True:
            if os.path.exists(os.path.join(current_dir, "rtl")) and os.path.exists(os.path.join(current_dir, "testbenches")):
                project_root = current_dir
                break
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        if not project_root:
            project_root = os.path.abspath(".")
            
        rel_rtl = "rtl/alu/alu.sv"
        rel_tb = "testbenches/alu"
        
        response = api_client.post("/designs", json={
            "name": "custom_alu",
            "description": "Custom ALU test",
            "rtl_path": rel_rtl,
            "testbench_path": rel_tb,
            "enabled": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "custom_alu"
        assert data["rtl_path"].endswith("rtl/alu/alu.sv")

        # 2. Duplicate design prevention
        response_dup = api_client.post("/designs", json={
            "name": "custom_alu",
            "rtl_path": rel_rtl,
            "testbench_path": rel_tb,
            "enabled": True
        })
        assert response_dup.status_code == 400
        assert "already exists" in response_dup.json()["detail"]

        # 3. Design listing
        response_list = api_client.get("/designs")
        assert response_list.status_code == 200
        designs = response_list.json()
        assert len(designs) >= 5  # 4 seeded + 1 created
        names = [d["name"] for d in designs]
        assert "custom_alu" in names
        assert "alu" in names

        # 4. Design lookup
        response_lookup = api_client.get("/designs/custom_alu")
        assert response_lookup.status_code == 200
        assert response_lookup.json()["name"] == "custom_alu"
        
        response_not_found = api_client.get("/designs/nonexistent")
        assert response_not_found.status_code == 404

        # 5. Invalid design path rejection (traversal / non-existent)
        response_invalid = api_client.post("/designs", json={
            "name": "invalid_design",
            "rtl_path": "../invalid.sv",
            "testbench_path": "testbenches/alu",
            "enabled": True
        })
        assert response_invalid.status_code == 400
        
        response_nonexistent = api_client.post("/designs", json={
            "name": "nonexistent_paths",
            "rtl_path": "rtl/nonexistent.sv",
            "testbench_path": "testbenches/nonexistent",
            "enabled": True
        })
        assert response_nonexistent.status_code == 400

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_test_discovery(api_client):
    # 6. Test discovery
    response = api_client.get("/designs/alu/tests")
    assert response.status_code == 200
    data = response.json()
    assert data["design"] == "alu"
    tests = data["tests"]
    assert len(tests) >= 2
    names = [t["name"] for t in tests]
    assert "pass" in names
    assert "fail" in names


def test_existing_job_api_compatible(api_client, db_session):
    # 7. Existing job API remains compatible
    response = api_client.post("/jobs", json={
        "design_name": "alu",
        "test_name": "pass"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["design_name"] == "alu"
    assert data["test_name"] == "pass"
    assert data["status"] == "QUEUED"
    assert data["configuration"] is None

    # Parameterized job with configuration
    response_param = api_client.post("/jobs", json={
        "design_name": "alu",
        "test_name": "pass",
        "priority": "high",
        "configuration": {"waves": True}
    })
    assert response_param.status_code == 200
    data_param = response_param.json()
    assert data_param["priority"] == "high"
    assert data_param["configuration"] == {"waves": True}


def test_regression_management(api_client, db_session):
    # 8. Regression creation
    response = api_client.post("/regressions", json={
        "name": "alu-reg",
        "design_name": "alu",
        "tests": ["pass", "fail"],
        "priority": "high",
        "configuration": {"waves": True}
    })
    assert response.status_code == 200
    reg = response.json()
    reg_id = reg["id"]
    assert reg["name"] == "alu-reg"
    assert reg["status"] == "QUEUED"
    assert reg["total_jobs"] == 2
    assert len(reg["job_ids"]) == 2

    # 9. Invalid regression design rejection
    response_invalid_design = api_client.post("/regressions", json={
        "name": "invalid-reg",
        "design_name": "nonexistent_design",
        "tests": ["pass"]
    })
    assert response_invalid_design.status_code == 400

    # 10. Invalid regression test rejection
    response_invalid_test = api_client.post("/regressions", json={
        "name": "invalid-reg-test",
        "design_name": "alu",
        "tests": ["nonexistent_test_name"]
    })
    assert response_invalid_test.status_code == 400

    # 11 & 12. Regression creates jobs and enqueues them
    # Check SimulationJob table
    jobs = db_session.query(SimulationJob).filter(SimulationJob.regression_id == reg_id).all()
    assert len(jobs) == 2
    for job in jobs:
        assert job.priority == "high"
        assert job.configuration == {"waves": True}
        assert job.status == "QUEUED"

    # 13. Regression status
    response_status = api_client.get(f"/regressions/{reg_id}")
    assert response_status.status_code == 200
    status_data = response_status.json()
    assert status_data["id"] == reg_id
    assert status_data["status"] == "QUEUED"
    assert status_data["total_jobs"] == 2
    assert status_data["completion_percentage"] == 0

    # Simulate running and completed jobs to verify status calculation
    job_ids = reg["job_ids"]
    jobs[0].status = "PASSED"
    jobs[0].runtime_ms = 1200
    jobs[0].attempt_count = 1
    jobs[1].status = "FAILED"
    jobs[1].runtime_ms = 1500
    jobs[1].attempt_count = 1
    jobs[1].failure_category = "ASSERTION_FAILURE"
    jobs[1].stderr = "Assertion failed: Expected 100 but got 25"
    db_session.commit()

    response_status_updated = api_client.get(f"/regressions/{reg_id}")
    assert response_status_updated.status_code == 200
    updated_data = response_status_updated.json()
    assert updated_data["status"] == "FAILED"
    assert updated_data["passed_jobs"] == 1
    assert updated_data["failed_jobs"] == 1
    assert updated_data["completion_percentage"] == 100
    assert updated_data["total_runtime_ms"] == 2700

    # 14. Regression results
    response_results = api_client.get(f"/regressions/{reg_id}/results")
    assert response_results.status_code == 200
    results = response_results.json()
    assert len(results) == 2
    assert results[0]["status"] == "PASSED"
    assert results[1]["status"] == "FAILED"
    assert results[1]["failure_category"] == "ASSERTION_FAILURE"

    # 15. Regression failure summary
    response_failures = api_client.get(f"/regressions/{reg_id}/failures")
    assert response_failures.status_code == 200
    failures = response_failures.json()
    assert failures["total_failures"] == 1
    assert failures["categories"]["ASSERTION_FAILURE"] == 1
    assert len(failures["affected_jobs"]) == 1
    assert failures["affected_jobs"][0]["job_id"] == job_ids[1]

    # 16. Failure clustering
    # Add another failed job to regression to test clustering
    new_failed_job = SimulationJob(
        design_name="alu",
        test_name="fail",
        priority="high",
        status="FAILED",
        runtime_ms=1000,
        attempt_count=1,
        failure_category="ASSERTION_FAILURE",
        stderr="Assertion failed: Expected 999 but got 30",
        regression_id=reg_id
    )
    db_session.add(new_failed_job)
    db_session.commit()

    response_clusters = api_client.get(f"/regressions/{reg_id}/failure-clusters")
    assert response_clusters.status_code == 200
    clusters = response_clusters.json()
    # Both "Expected 100 but got 25" and "Expected 999 but got 30" should normalize to the same cluster
    assert len(clusters) == 1
    assert clusters[0]["failure_category"] == "ASSERTION_FAILURE"
    assert clusters[0]["failure_count"] == 2
    assert len(clusters[0]["affected_jobs"]) == 2

    # 17. Regression summary (verification scorecard)
    response_summary = api_client.get(f"/regressions/{reg_id}/summary")
    assert response_summary.status_code == 200
    summary = response_summary.json()
    assert summary["regression_id"] == reg_id
    assert summary["status"] == "FAILED"
    assert summary["total_tests"] == 3
    assert len(summary["top_failure_clusters"]) == 1

    # 18. Regression artifacts
    # Create fake artifacts in DB
    attempt = SimulationAttempt(
        job_id=jobs[0].id,
        attempt_number=1,
        status="PASSED"
    )
    db_session.add(attempt)
    db_session.commit()
    
    art = SimulationArtifact(
        job_id=jobs[0].id,
        attempt_id=attempt.id,
        artifact_type="stdout",
        filename="stdout.txt",
        path="/app/artifacts/dummy/stdout.txt",
        size_bytes=100,
        checksum="abcd"
    )
    db_session.add(art)
    db_session.commit()

    response_artifacts = api_client.get(f"/regressions/{reg_id}/artifacts")
    assert response_artifacts.status_code == 200
    artifacts = response_artifacts.json()
    assert len(artifacts) == 1
    assert artifacts[0]["filename"] == "stdout.txt"
    assert "path" not in artifacts[0]  # Check security: path is not exposed

    # 19. Regression history
    response_history = api_client.get(f"/regressions/{reg_id}/history")
    assert response_history.status_code == 200
    history = response_history.json()
    events = [h["event"] for h in history]
    assert "REGRESSION_CREATED" in events
    assert "JOB_CREATED" in events


def test_ai_analyzer_interface(api_client, db_session):
    # 20 & 21. AI analyzer receives extended context & Rule-based analyzer works
    job = SimulationJob(
        design_name="alu",
        test_name="fail",
        status="FAILED",
        exit_code=1,
        stdout="Assertion failed",
        stderr="Assertion failed in alu",
        runtime_ms=100
    )
    db_session.add(job)
    db_session.commit()

    # Trigger analyze endpoint
    response = api_client.post(f"/jobs/{job.id}/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job.id
    assert data["failure_category"] == "ASSERTION_FAILURE"


def test_prometheus_metrics(api_client, db_session):
    # 22. Prometheus regression metrics
    response = api_client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    assert "regressions_total" in metrics_text
    assert "regressions_completed_total" in metrics_text
    assert "failure_clusters_total" in metrics_text


def test_independent_regressions(api_client, db_session):
    # 23. Multiple regressions can run independently
    response1 = api_client.post("/regressions", json={
        "name": "reg1",
        "design_name": "alu",
        "tests": ["pass"]
    })
    response2 = api_client.post("/regressions", json={
        "name": "reg2",
        "design_name": "fifo",
        "tests": ["pass"]
    })
    assert response1.status_code == 200
    assert response2.status_code == 200
    reg1_id = response1.json()["id"]
    reg2_id = response2.json()["id"]
    assert reg1_id != reg2_id
