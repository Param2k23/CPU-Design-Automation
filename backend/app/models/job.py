import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON, ForeignKey, Boolean
from app.database import Base

class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    design_name = Column(String, nullable=False)
    test_name = Column(String, nullable=False)
    rtl_path = Column(String, nullable=True)
    testbench_path = Column(String, nullable=True)
    status = Column(String, default="QUEUED", nullable=False)
    priority = Column(String, default="normal")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String, nullable=True)
    attempt_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=0)
    exit_code = Column(Integer, nullable=True)
    runtime_ms = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    failure_category = Column(String, nullable=True)
    failure_summary = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    result_artifact_path = Column(String, nullable=True)
    regression_id = Column(String, ForeignKey("regression_runs.id"), nullable=True)
    configuration = Column(JSON, nullable=True)

class SimulationAttempt(Base):
    __tablename__ = "simulation_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("simulation_jobs.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String, default="QUEUED", nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    runtime_ms = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    failure_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class FailureAnalysis(Base):
    __tablename__ = "failure_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("simulation_jobs.id"), nullable=False)
    analyzer_type = Column(String, nullable=False)
    failure_category = Column(String, nullable=True)
    summary = Column(Text, nullable=False)
    suspected_root_cause = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    recommended_fix = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WorkerStatus(Base):
    __tablename__ = "worker_statuses"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, default="AVAILABLE", nullable=False)
    concurrency_slots = Column(Integer, default=4, nullable=False)
    active_slots = Column(Integer, default=0, nullable=False)
    cpu_util = Column(Float, default=0.0, nullable=False)
    mem_util = Column(Float, default=0.0, nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)

class SimulationArtifact(Base):
    __tablename__ = "simulation_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("simulation_jobs.id"), nullable=False)
    attempt_id = Column(String, ForeignKey("simulation_attempts.id"), nullable=False)
    artifact_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    checksum = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Design(Base):
    __tablename__ = "designs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    rtl_path = Column(String, nullable=False)
    testbench_path = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class RegressionRun(Base):
    __tablename__ = "regression_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(String, default="QUEUED", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_jobs = Column(Integer, default=0, nullable=False)
    passed_jobs = Column(Integer, default=0, nullable=False)
    failed_jobs = Column(Integer, default=0, nullable=False)
    skipped_jobs = Column(Integer, default=0, nullable=False)
    priority = Column(String, default="normal", nullable=False)
    configuration = Column(JSON, nullable=True)


