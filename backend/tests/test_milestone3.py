import pytest
import time
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.job import SimulationJob, WorkerStatus, SimulationAttempt
import app.main as main_module
import app.queue.redis_queue as rq

# ---------------------------------------------------------------------------
# Isolation DB Setup
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_m3.db"
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
# Redis Priority Queue Tests
# ---------------------------------------------------------------------------
def test_priority_scheduling():
    """Verify high priority jobs are dequeued before normal and low."""
    with patch("app.queue.redis_queue.redis_client") as mock_redis:
        mock_redis.brpop.return_value = (rq.QUEUE_HIGH, json.dumps({"job_id": "job_high", "priority": "high"}))
        job = rq.dequeue_job(timeout=1)
        assert job["job_id"] == "job_high"
        
        mock_redis.brpop.assert_called_once_with(
            [rq.QUEUE_HIGH, rq.QUEUE_NORMAL, rq.QUEUE_LOW],
            timeout=1
        )

def test_delayed_queue_exponential_backoff():
    """Verify zadd is called with timestamp for delayed queue."""
    with patch("app.queue.redis_queue.redis_client") as mock_redis:
        rq.enqueue_delayed_job("job_retry", 10, "normal")
        mock_redis.zadd.assert_called_once()
        args, kwargs = mock_redis.zadd.call_args
        assert args[0] == rq.DELAYED_JOBS

# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_queue_depth(api_client, monkeypatch):
    """Verify GET /queue/depth returns queue depths."""
    monkeypatch.setattr(main_module, "get_queue_depths", lambda: {"high": 5, "normal": 10, "low": 1, "delayed": 2})
    res = api_client.get("/queue/depth")
    assert res.status_code == 200
    assert res.json() == {"high": 5, "normal": 10, "low": 1, "delayed": 2}

def test_api_workers(api_client, db_session):
    """Verify GET /workers returns active workers."""
    worker = WorkerStatus(
        id="worker-test",
        name="worker-test",
        status="AVAILABLE",
        concurrency_slots=4,
        active_slots=1,
        cpu_util=12.5,
        mem_util=45.0
    )
    db_session.add(worker)
    db_session.commit()

    res = api_client.get("/workers")
    assert res.status_code == 200
    workers = res.json()
    assert len(workers) == 1
    assert workers[0]["id"] == "worker-test"
    assert workers[0]["cpu_util"] == 12.5

def test_api_metrics(api_client):
    """Verify GET /metrics returns prometheus metrics format."""
    res = api_client.get("/metrics")
    assert res.status_code == 200
    assert "simulation_jobs_total" in res.text
    assert "worker_jobs_active" in res.text

# ---------------------------------------------------------------------------
# Concurrency & Duplicate-Job Prevention Tests
# ---------------------------------------------------------------------------
def test_duplicate_job_prevention_state_machine(db_session):
    """Verify that multiple worker threads trying to update status to RUNNING only succeeds for one."""
    job = SimulationJob(
        id="job-dup",
        design_name="alu",
        test_name="pass",
        status="QUEUED"
    )
    db_session.add(job)
    db_session.commit()

    db1 = TestingSessionLocal()
    db2 = TestingSessionLocal()

    # Worker 1 takes it
    updated1 = db1.query(SimulationJob).filter(
        SimulationJob.id == "job-dup",
        SimulationJob.status == "QUEUED"
    ).update({"status": "RUNNING"})
    db1.commit()

    # Worker 2 tries to take it simultaneously
    updated2 = db2.query(SimulationJob).filter(
        SimulationJob.id == "job-dup",
        SimulationJob.status == "QUEUED"
    ).update({"status": "RUNNING"})
    db2.commit()

    db1.close()
    db2.close()

    assert updated1 == 1
    assert updated2 == 0  # Atomic query returned 0 rows updated, preventing duplicate execution!
