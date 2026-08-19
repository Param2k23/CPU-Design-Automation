"""
Milestone 2 tests: FailureAnalyzer, analysis persistence, revalidation, attempt tracking.

All HTTP tests use an isolated in-process SQLite DB via a session-scoped fixture
so the real PostgreSQL is never touched and tests run offline.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import unittest.mock as mock

from app.database import Base, get_db
from app.main import app
from app.models.job import SimulationJob, FailureAnalysis, SimulationAttempt
from app.debugging.analyzer import RuleBasedFailureAnalyzer, LLMFailureAnalyzer
import app.main as main_module

# ---------------------------------------------------------------------------
# Shared SQLite engine (in-memory; file-based for cross-thread access)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_m2.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    """Create all tables, yield a session, then tear everything down."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def api_client(db_session, monkeypatch):
    """
    Return a TestClient that:
    - uses the isolated SQLite DB
    - has Redis enqueue stubbed out
    """
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
# Helpers
# ---------------------------------------------------------------------------
def make_failed_job(db) -> SimulationJob:
    job = SimulationJob(
        id=str(uuid.uuid4()),
        design_name="alu",
        test_name="fail",
        status="FAILED",
        attempt_count=1,
        exit_code=1,
        stdout="Assertion failed: Expected 999 but got 30",
        stderr="",
        failure_category="ASSERTION_FAILURE",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def make_passed_job(db) -> SimulationJob:
    job = SimulationJob(
        id=str(uuid.uuid4()),
        design_name="alu",
        test_name="pass",
        status="PASSED",
        attempt_count=1,
        exit_code=0,
        stdout="All assertions passed.",
        stderr="",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ===========================================================================
# Section 1: RuleBasedFailureAnalyzer – pure unit tests, zero HTTP
# ===========================================================================

def test_rule_based_analyzer_timeout():
    a = RuleBasedFailureAnalyzer()
    r = a.analyze("alu", "t1", -1, "", "", 60000)
    assert r["failure_category"] == "TIMEOUT"
    assert r["analyzer_type"] == "rule_based"
    assert r["confidence"] >= 0.9


def test_rule_based_analyzer_compile_error():
    a = RuleBasedFailureAnalyzer()
    r = a.analyze("alu", "t1", 1, "", "Error: syntax error at line 5", 100)
    assert r["failure_category"] == "COMPILE_ERROR"
    assert r["confidence"] == 1.0


def test_rule_based_analyzer_assertion():
    a = RuleBasedFailureAnalyzer()
    r = a.analyze("alu", "t1", 1, "Assertion failed in tb_alu.cpp:45", "", 100)
    assert r["failure_category"] == "ASSERTION_FAILURE"
    assert r["confidence"] == 1.0
    assert len(r["evidence"]) > 0


def test_rule_based_analyzer_simulation_error():
    a = RuleBasedFailureAnalyzer()
    r = a.analyze("alu", "t1", 2, "some output", "no match", 100)
    assert r["failure_category"] == "SIMULATION_ERROR"


def test_rule_based_analyzer_no_external_api():
    """Must work without any network call."""
    a = RuleBasedFailureAnalyzer()
    r = a.analyze("alu", "t1", 1, "", "", 0)
    assert "failure_category" in r
    assert "confidence" in r


def test_llm_failure_analyzer_stub():
    """LLMFailureAnalyzer stub returns conformant schema without an API key."""
    a = LLMFailureAnalyzer()
    r = a.analyze("alu", "t1", 1, "", "", 0)
    assert "failure_category" in r
    assert r["analyzer_type"] == "llm"


# ===========================================================================
# Section 2: POST /jobs/{id}/analyze
# ===========================================================================

def test_analyze_nonexistent_job(api_client):
    res = api_client.post("/jobs/nonexistent-id/analyze")
    assert res.status_code == 404


def test_analyze_passed_job_rejected(api_client, db_session):
    job = make_passed_job(db_session)
    res = api_client.post(f"/jobs/{job.id}/analyze")
    assert res.status_code == 400
    assert "failed" in res.json()["detail"].lower()


def test_analyze_failed_job_returns_structured_data(api_client, db_session):
    job = make_failed_job(db_session)
    res = api_client.post(f"/jobs/{job.id}/analyze")
    assert res.status_code == 200
    body = res.json()
    assert body["failure_category"] == "ASSERTION_FAILURE"
    assert body["summary"] != ""
    assert body["suspected_root_cause"] != ""
    assert isinstance(body["evidence"], list)
    assert body["recommended_fix"] != ""
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["analyzer_type"] == "rule_based"
    assert body["job_id"] == job.id


def test_analysis_is_persisted(api_client, db_session):
    job = make_failed_job(db_session)
    api_client.post(f"/jobs/{job.id}/analyze")

    records = db_session.query(FailureAnalysis).filter(
        FailureAnalysis.job_id == job.id
    ).all()
    assert len(records) == 1
    assert records[0].failure_category == "ASSERTION_FAILURE"


def test_multiple_analyses_allowed(api_client, db_session):
    job = make_failed_job(db_session)
    api_client.post(f"/jobs/{job.id}/analyze")
    api_client.post(f"/jobs/{job.id}/analyze")

    records = db_session.query(FailureAnalysis).filter(
        FailureAnalysis.job_id == job.id
    ).all()
    assert len(records) == 2


def test_analysis_never_overwrites_previous(api_client, db_session):
    job = make_failed_job(db_session)
    r1 = api_client.post(f"/jobs/{job.id}/analyze").json()
    r2 = api_client.post(f"/jobs/{job.id}/analyze").json()
    assert r1["id"] != r2["id"]


# ===========================================================================
# Section 3: GET /jobs/{id}/analyses
# ===========================================================================

def test_get_analyses_empty(api_client, db_session):
    job = make_failed_job(db_session)
    res = api_client.get(f"/jobs/{job.id}/analyses")
    assert res.status_code == 200
    assert res.json() == []


def test_get_analyses_returns_history(api_client, db_session):
    job = make_failed_job(db_session)
    api_client.post(f"/jobs/{job.id}/analyze")
    api_client.post(f"/jobs/{job.id}/analyze")

    res = api_client.get(f"/jobs/{job.id}/analyses")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_analyses_nonexistent_job(api_client):
    res = api_client.get("/jobs/bad-id/analyses")
    assert res.status_code == 404


# ===========================================================================
# Section 4: POST /jobs/{id}/revalidate
# ===========================================================================

def test_revalidate_requeues_job(api_client, db_session):
    job = make_failed_job(db_session)
    res = api_client.post(f"/jobs/{job.id}/revalidate")
    assert res.status_code == 200
    assert res.json()["status"] == "QUEUED"


def test_revalidate_nonexistent_job(api_client):
    res = api_client.post("/jobs/nonexistent/revalidate")
    assert res.status_code == 404


def test_revalidate_preserves_attempt_count_until_worker(api_client, db_session):
    """Status becomes QUEUED; attempt_count unchanged until worker runs."""
    job = make_failed_job(db_session)
    initial_count = job.attempt_count
    api_client.post(f"/jobs/{job.id}/revalidate")

    res = api_client.get(f"/jobs/{job.id}")
    assert res.json()["attempt_count"] == initial_count
    assert res.json()["status"] == "QUEUED"


# ===========================================================================
# Section 5: SimulationAttempt tracking (direct model tests)
# ===========================================================================

def test_attempt_record_created_by_worker(db_session):
    job = make_failed_job(db_session)
    attempt = SimulationAttempt(
        job_id=job.id,
        attempt_number=1,
        status="FAILED",
        exit_code=1,
        failure_category="ASSERTION_FAILURE",
    )
    db_session.add(attempt)
    db_session.commit()

    records = db_session.query(SimulationAttempt).filter(
        SimulationAttempt.job_id == job.id
    ).all()
    assert len(records) == 1
    assert records[0].attempt_number == 1
    assert records[0].failure_category == "ASSERTION_FAILURE"


def test_multiple_attempts_preserved(db_session):
    job = make_failed_job(db_session)
    for i in range(1, 4):
        db_session.add(SimulationAttempt(
            job_id=job.id,
            attempt_number=i,
            status="FAILED" if i < 3 else "PASSED",
            exit_code=1 if i < 3 else 0,
        ))
    db_session.commit()

    records = db_session.query(SimulationAttempt).filter(
        SimulationAttempt.job_id == job.id
    ).all()
    assert len(records) == 3
    statuses = [r.status for r in records]
    assert "PASSED" in statuses
    assert statuses.count("FAILED") == 2
