from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, engine, Base
from app.models.job import SimulationJob, FailureAnalysis, SimulationAttempt, WorkerStatus, SimulationArtifact
from app.schemas.job import JobCreate, JobResponse, JobLogResponse, FailureAnalysisResponse, WorkerStatusResponse, SimulationArtifactResponse, SimulationAttemptResponse
from app.queue.redis_queue import enqueue_job, get_queue_depths
from app.debugging.analyzer import get_failure_analyzer
import os

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

    # 5. Milestone 4 Metrics
    total_artifacts = db.query(func.count(SimulationArtifact.id)).scalar() or 0
    total_artifact_bytes = db.query(func.sum(SimulationArtifact.size_bytes)).scalar() or 0
    total_analyses = db.query(func.count(FailureAnalysis.id)).scalar() or 0
    total_attempts_real = db.query(func.count(SimulationAttempt.id)).scalar() or 0
    total_runtime_seconds = (db.query(func.sum(SimulationAttempt.runtime_ms)).scalar() or 0) / 1000.0
    
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

# HELP simulations_total Total simulation runs
# TYPE simulations_total counter
simulations_total {total_jobs}

# HELP simulations_passed_total Total passed simulations
# TYPE simulations_passed_total counter
simulations_passed_total {passed_jobs}

# HELP simulations_failed_total Total failed simulations
# TYPE simulations_failed_total counter
simulations_failed_total {failed_jobs}

# HELP simulations_retried_total Total retried simulations
# TYPE simulations_retried_total counter
simulations_retried_total {retries}

# HELP simulation_runtime_seconds Total runtime of simulations in seconds
# TYPE simulation_runtime_seconds gauge
simulation_runtime_seconds {total_runtime_seconds}

# HELP simulation_attempts_total Total execution attempts across all jobs
# TYPE simulation_attempts_total counter
simulation_attempts_total {total_attempts_real}

# HELP artifacts_created_total Total artifacts created
# TYPE artifacts_created_total counter
artifacts_created_total {total_artifacts}

# HELP artifact_bytes_total Total size of artifacts in bytes
# TYPE artifact_bytes_total counter
artifact_bytes_total {total_artifact_bytes}

# HELP failure_analysis_total Total failure analyses executed
# TYPE failure_analysis_total counter
failure_analysis_total {total_analyses}
"""
    return Response(content=metrics_str, media_type="text/plain")

@app.get("/jobs/{job_id}/attempts", response_model=list[SimulationAttemptResponse])
def get_job_attempts(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    attempts = db.query(SimulationAttempt).filter(SimulationAttempt.job_id == job_id).order_by(SimulationAttempt.attempt_number.asc()).all()
    return attempts

@app.get("/jobs/{job_id}/artifacts", response_model=list[SimulationArtifactResponse])
def get_job_artifacts(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    artifacts = db.query(SimulationArtifact).filter(SimulationArtifact.job_id == job_id).all()
    return artifacts

@app.get("/artifacts/{artifact_id}")
def download_artifact(artifact_id: str, db: Session = Depends(get_db)):
    artifact = db.query(SimulationArtifact).filter(SimulationArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Resolve path and perform path traversal checks
    ARTIFACT_ROOT = os.path.realpath(os.getenv("ARTIFACT_ROOT", "./artifacts"))
    real_path = os.path.realpath(artifact.path)
    
    # Path traversal check: must start with ARTIFACT_ROOT prefix
    if not real_path.startswith(ARTIFACT_ROOT + os.sep) and real_path != ARTIFACT_ROOT:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(real_path, filename=artifact.filename)

@app.get("/jobs/{job_id}/summary")
def get_job_summary(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    total_runtime = db.query(func.sum(SimulationAttempt.runtime_ms)).filter(SimulationAttempt.job_id == job_id).scalar() or 0
    art_count = db.query(func.count(SimulationArtifact.id)).filter(SimulationArtifact.job_id == job_id).scalar() or 0
    latest_analysis = db.query(FailureAnalysis).filter(FailureAnalysis.job_id == job_id).order_by(FailureAnalysis.created_at.desc()).first()
    analysis_count = db.query(func.count(FailureAnalysis.id)).filter(FailureAnalysis.job_id == job_id).scalar() or 0

    summary = {
        "job_id": job.id,
        "design_name": job.design_name,
        "test_name": job.test_name,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "total_runtime_ms": total_runtime,
        "final_exit_code": job.exit_code,
        "failure_category": job.failure_category,
        "analysis_count": analysis_count,
        "artifact_count": art_count
    }

    if job.status == "FAILED" and latest_analysis:
        summary.update({
            "latest_analysis_summary": latest_analysis.summary,
            "suspected_root_cause": latest_analysis.suspected_root_cause,
            "recommended_fix": latest_analysis.recommended_fix,
            "confidence": latest_analysis.confidence
        })
    else:
        summary.update({
            "latest_analysis_summary": None,
            "suspected_root_cause": None,
            "recommended_fix": None,
            "confidence": None
        })

    return summary

@app.get("/jobs/{job_id}/history")
def get_job_history(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    history = []
    
    # 1. Job Created
    history.append({
        "event": "JOB_CREATED",
        "timestamp": job.created_at.isoformat() + "Z",
        "attempt": None
    })
    
    attempts = db.query(SimulationAttempt).filter(SimulationAttempt.job_id == job_id).order_by(SimulationAttempt.attempt_number.asc()).all()
    analyses = db.query(FailureAnalysis).filter(FailureAnalysis.job_id == job_id).order_by(FailureAnalysis.created_at.asc()).all()
    
    for attempt in attempts:
        # Simulation Started
        if attempt.started_at:
            history.append({
                "event": "SIMULATION_STARTED",
                "timestamp": attempt.started_at.isoformat() + "Z",
                "attempt": attempt.attempt_number
            })
        
        # Simulation Result
        if attempt.status in ("PASSED", "FAILED", "RETRYING"):
            event_name = "SIMULATION_PASSED" if attempt.status == "PASSED" else "SIMULATION_FAILED"
            evt = {
                "event": event_name,
                "timestamp": (attempt.completed_at or attempt.started_at).isoformat() + "Z",
                "attempt": attempt.attempt_number
            }
            if attempt.status in ("FAILED", "RETRYING"):
                evt["failure_category"] = attempt.failure_category
            history.append(evt)

    for analysis in analyses:
        # Try to match the analysis with the attempt it was performed on
        matching_attempt = 1
        for attempt in attempts:
            if attempt.completed_at and attempt.completed_at <= analysis.created_at:
                matching_attempt = attempt.attempt_number
        history.append({
            "event": "FAILURE_ANALYZED",
            "timestamp": analysis.created_at.isoformat() + "Z",
            "attempt": matching_attempt
        })

    # Add revalidation events
    for attempt in attempts:
        if attempt.attempt_number > 1:
            timestamp = attempt.started_at or attempt.created_at
            history.append({
                "event": "REVALIDATION_REQUESTED",
                "timestamp": timestamp.isoformat() + "Z",
                "attempt": attempt.attempt_number
            })
            
    # Sort history chronologically by timestamp
    history.sort(key=lambda x: x["timestamp"])
    return history
