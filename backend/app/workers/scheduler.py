import time
import os
import logging
from datetime import datetime
from app.database import SessionLocal
from app.models.job import SimulationJob, SimulationAttempt
from app.queue.redis_queue import dequeue_job
from app.simulation.verilator import run_verilator, classify_failure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKER_ID = os.getenv("HOSTNAME", "local-worker")
# Hardcode path for simplicity in MVP. Real logic might resolve this dynamically.
RTL_BASE = "/app/rtl"
TB_BASE = "/app/testbenches"
OUT_BASE = "/app/simulations/results"

def process_job(job_id: str):
    db = SessionLocal()
    job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found in DB")
        db.close()
        return

    try:
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        job.worker_id = WORKER_ID
        job.attempt_count += 1
        db.commit()

        # Map design/test names to paths
        rtl_path = os.path.join(RTL_BASE, job.design_name, f"{job.design_name}.sv")
        # Ensure tb naming convention
        tb_path = os.path.join(TB_BASE, job.design_name, f"tb_{job.design_name}_{job.test_name}.cpp")

        # Validate paths
        if not os.path.exists(rtl_path):
            raise FileNotFoundError(f"RTL file not found: {rtl_path}")
        if not os.path.exists(tb_path):
            raise FileNotFoundError(f"Testbench not found: {tb_path}")

        # Create output dir
        out_dir = os.path.join(OUT_BASE, job_id)
        os.makedirs(out_dir, exist_ok=True)

        exit_code, stdout, stderr, runtime_ms = run_verilator(rtl_path, tb_path, out_dir)

        job.exit_code = exit_code
        job.stdout = stdout
        job.stderr = stderr
        job.runtime_ms = runtime_ms
        job.completed_at = datetime.utcnow()

        if exit_code == 0:
            job.status = "PASSED"
        else:
            job.status = "FAILED"
            job.failure_category = classify_failure(exit_code, stdout, stderr)
        # Basic deterministic remediation is now handled by analyzer API, not here
        
        # Create a SimulationAttempt record
        attempt = SimulationAttempt(
            job_id=job.id,
            attempt_number=job.attempt_count,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            exit_code=job.exit_code,
            runtime_ms=job.runtime_ms,
            stdout=job.stdout,
            stderr=job.stderr,
            failure_category=job.failure_category
        )
        db.add(attempt)
        db.commit()
        logger.info(f"Job {job_id} attempt {job.attempt_count} completed with status {job.status}")

    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {e}")
        job.status = "FAILED"
        job.failure_category = "INFRASTRUCTURE_ERROR"
        job.failure_summary = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

def main():
    logger.info("Starting scheduler worker...")
    while True:
        try:
            job_data = dequeue_job(timeout=5)
            if job_data:
                job_id = job_data["job_id"]
                logger.info(f"Dequeued job {job_id}")
                process_job(job_id)
            else:
                pass # Keep polling
        except Exception as e:
            logger.error(f"Worker encountered queue error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
