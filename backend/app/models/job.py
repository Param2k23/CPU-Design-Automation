import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
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
