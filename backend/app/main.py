from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models.job import SimulationJob, FailureAnalysis, SimulationAttempt
from app.schemas.job import JobCreate, JobResponse, JobLogResponse, FailureAnalysisResponse
from app.queue.redis_queue import enqueue_job
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
