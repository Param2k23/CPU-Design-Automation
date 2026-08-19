from fastapi import FastAPI, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, engine, Base
from app.models.job import SimulationJob, FailureAnalysis, SimulationAttempt, WorkerStatus
from app.schemas.job import JobCreate, JobResponse, JobLogResponse, FailureAnalysisResponse, WorkerStatusResponse
from app.queue.redis_queue import enqueue_job, get_queue_depths
from app.debugging.analyzer import get_failure_analyzer

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CPU Design Automation API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/jobs", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = SimulationJob(
        design_name=job.design_name,
        test_name=job.test_name,
        priority=job.priority,
        max_retries=job.max_retries
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    enqueue_job(db_job.id, priority=job.priority)

    return db_job

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/jobs/{job_id}/logs", response_model=JobLogResponse)
def get_job_logs(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")

    job.status = "QUEUED"
    db.commit()
    db.refresh(job)

    enqueue_job(job.id, priority=job.priority)

    return job

@app.post("/jobs/{job_id}/analyze", response_model=FailureAnalysisResponse)
def analyze_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "FAILED":
        raise HTTPException(status_code=400, detail="Only failed jobs can be analyzed")
        
    analyzer = get_failure_analyzer()
    result = analyzer.analyze(
        design_name=job.design_name,
        test_name=job.test_name,
        exit_code=job.exit_code,
        stdout=job.stdout,
        stderr=job.stderr,
        runtime_ms=job.runtime_ms
    )
    
    analysis = FailureAnalysis(
        job_id=job.id,
        analyzer_type=result["analyzer_type"],
        failure_category=result["failure_category"],
        summary=result["summary"],
        suspected_root_cause=result["suspected_root_cause"],
        evidence=result["evidence"],
        recommended_fix=result["recommended_fix"],
        confidence=result["confidence"]
    )
    db.add(analysis)
    
    # Store recommended remediation on job for quick reference
    job.remediation = result["recommended_fix"]
    db.commit()
    db.refresh(analysis)
    
    return analysis

@app.get("/jobs/{job_id}/analyses", response_model=list[FailureAnalysisResponse])
def get_job_analyses(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    analyses = db.query(FailureAnalysis).filter(FailureAnalysis.job_id == job_id).order_by(FailureAnalysis.created_at.desc()).all()
    return analyses

@app.post("/jobs/{job_id}/revalidate", response_model=JobResponse)
def revalidate_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "QUEUED"
    db.commit()
    db.refresh(job)
    
    enqueue_job(job.id, priority=job.priority)
    return job

@app.get("/workers", response_model=list[WorkerStatusResponse])
def get_workers(db: Session = Depends(get_db)):
    workers = db.query(WorkerStatus).all()
    return workers

@app.get("/queue/depth")
def get_queue_depth():
    return get_queue_depths()

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    # 1. Total jobs
    total_jobs = db.query(func.count(SimulationJob.id)).scalar() or 0
    passed_jobs = db.query(func.count(SimulationJob.id)).filter(SimulationJob.status == "PASSED").scalar() or 0
    failed_jobs = db.query(func.count(SimulationJob.id)).filter(SimulationJob.status == "FAILED").scalar() or 0
    
    # 2. Retries
    total_attempts = db.query(func.sum(SimulationJob.attempt_count)).scalar() or 0
    retries = max(0, total_attempts - total_jobs)
    
    # 3. Workers
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(seconds=20)
    active_workers = db.query(func.count(WorkerStatus.id)).filter(WorkerStatus.last_heartbeat > cutoff).scalar() or 0
    active_slots = db.query(func.sum(WorkerStatus.active_slots)).scalar() or 0
    
    # 4. Queue depths
    depths = get_queue_depths()
    
    # Format Prometheus metrics response
    metrics_str = f"""# HELP simulation_jobs_total Total simulation jobs submitted
# TYPE simulation_jobs_total counter
simulation_jobs_total {total_jobs}

# HELP simulation_jobs_success_total Total successful simulation jobs
# TYPE simulation_jobs_success_total counter
simulation_jobs_success_total {passed_jobs}

# HELP simulation_jobs_failed_total Total failed simulation jobs
# TYPE simulation_jobs_failed_total counter
simulation_jobs_failed_total {failed_jobs}

# HELP simulation_retries_total Total job retries
# TYPE simulation_retries_total counter
simulation_retries_total {retries}

# HELP worker_jobs_active Active simulation worker slots
# TYPE worker_jobs_active gauge
worker_jobs_active {active_slots}

# HELP simulation_queue_depth Current depth of priority queues
# TYPE simulation_queue_depth gauge
simulation_queue_depth{{priority="high"}} {depths['high']}
simulation_queue_depth{{priority="normal"}} {depths['normal']}
simulation_queue_depth{{priority="low"}} {depths['low']}
simulation_queue_depth{{priority="delayed"}} {depths['delayed']}

# HELP worker_count Number of active workers
# TYPE worker_count gauge
worker_count {active_workers}
"""
    return Response(content=metrics_str, media_type="text/plain")

