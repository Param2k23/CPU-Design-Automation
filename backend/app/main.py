from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models.job import SimulationJob
from app.schemas.job import JobCreate, JobResponse, JobLogResponse
from app.queue.redis_queue import enqueue_job

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
