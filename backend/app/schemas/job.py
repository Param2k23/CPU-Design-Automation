from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class JobCreate(BaseModel):
    design_name: str
    test_name: str
    priority: str = "normal"
    max_retries: int = 0

class JobResponse(BaseModel):
    id: str
    design_name: str
    test_name: str
    status: str
    priority: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt_count: int
    max_retries: int
    exit_code: Optional[int] = None
    runtime_ms: Optional[int] = None
    failure_category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobLogResponse(BaseModel):
    id: str
    stdout: Optional[str]
    stderr: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class SimulationAttemptResponse(BaseModel):
    id: str
    job_id: str
    attempt_number: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    runtime_ms: Optional[int] = None
    failure_category: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FailureAnalysisResponse(BaseModel):
    id: str
    job_id: str
    analyzer_type: str
    failure_category: Optional[str] = None
    summary: str
    suspected_root_cause: str
    evidence: Optional[List[str]] = None
    recommended_fix: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkerStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    concurrency_slots: int
    active_slots: int
    cpu_util: float
    mem_util: float
    last_heartbeat: datetime

    model_config = ConfigDict(from_attributes=True)

