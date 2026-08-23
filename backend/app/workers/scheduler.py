import time
import os
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.database import SessionLocal
from app.models.job import SimulationJob, SimulationAttempt, WorkerStatus
from app.queue.redis_queue import dequeue_job, enqueue_delayed_job, process_delayed_jobs
from app.simulation.verilator import run_verilator, classify_failure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKER_ID = os.getenv("HOSTNAME", f"worker-{os.getpid()}")
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
RTL_BASE = "/app/rtl"
TB_BASE = "/app/testbenches"
OUT_BASE = "/app/simulations/results"

# Thread-local storage or lock to update active slots safely
active_slots_lock = threading.Lock()
active_slots = 0

def get_system_stats():
    """Get basic system stats. Fallback to dummy values to prevent dependency issues."""
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        return cpu, mem
    except ImportError:
        # Fallback CPU and Memory usage simulation
        return 15.0, 45.0

def run_heartbeat():
    """Background heartbeat loop that reports status to PostgreSQL."""
    logger.info("Heartbeat thread started.")
    while True:
        db = SessionLocal()
        try:
            cpu, mem = get_system_stats()
            with active_slots_lock:
                current_active = active_slots

            status_str = "AVAILABLE" if current_active < WORKER_CONCURRENCY else "BUSY"
            
            # Upsert worker status
            worker = db.query(WorkerStatus).filter(WorkerStatus.id == WORKER_ID).first()
            if not worker:
                worker = WorkerStatus(
                    id=WORKER_ID,
                    name=WORKER_ID,
                    status=status_str,
                    concurrency_slots=WORKER_CONCURRENCY,
                    active_slots=current_active,
                    cpu_util=cpu,
                    mem_util=mem,
                    last_heartbeat=datetime.utcnow()
                )
                db.add(worker)
            else:
                worker.status = status_str
                worker.active_slots = current_active
                worker.cpu_util = cpu
                worker.mem_util = mem
                worker.last_heartbeat = datetime.utcnow()
                
            db.commit()
        except Exception as e:
            logger.error(f"Error in heartbeat: {e}")
            db.rollback()
        finally:
            db.close()
        time.sleep(5)

def run_delayed_jobs_manager():
    """Background loop that moves delayed jobs to active queues when due."""
    logger.info("Delayed jobs manager started.")
    while True:
        try:
            process_delayed_jobs()
        except Exception as e:
            logger.error(f"Error processing delayed jobs: {e}")
        time.sleep(1)

def process_job(job_id: str):
    global active_slots
    db = SessionLocal()
    
    # State-machine transition: transition from QUEUED to RUNNING.
    # This prevents duplicate execution if multiple workers dequeue the same ID.
    try:
        updated = db.query(SimulationJob).filter(
            SimulationJob.id == job_id,
            SimulationJob.status.in_(["QUEUED", "RETRYING"])
        ).update({
            "status": "RUNNING",
            "started_at": datetime.utcnow(),
            "worker_id": WORKER_ID
        }, synchronize_session=False)
        db.commit()
        
        if updated == 0:
            logger.warning(f"Job {job_id} already taken or not in QUEUED state. Skipping.")
            db.close()
            return
            
        # Re-fetch the job record
        job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
        job.attempt_count += 1
        db.commit()
        
    except Exception as e:
        logger.error(f"Error locking job {job_id}: {e}")
        db.rollback()
        db.close()
        return

    # Increment active slots
    with active_slots_lock:
        active_slots += 1

    try:
        # Map design/test names to paths
        rtl_path = job.rtl_path or os.path.join(RTL_BASE, job.design_name, f"{job.design_name}.sv")
        tb_path = job.testbench_path or os.path.join(TB_BASE, job.design_name, f"tb_{job.design_name}_{job.test_name}.cpp")

        # Validate paths
        if not os.path.exists(rtl_path):
            raise FileNotFoundError(f"RTL file not found: {rtl_path}")
        if not os.path.exists(tb_path):
            raise FileNotFoundError(f"Testbench not found: {tb_path}")

        # Create output dir
        out_dir = os.path.join(OUT_BASE, job_id)
        os.makedirs(out_dir, exist_ok=True)

        # Check if coverage is enabled in configuration
        coverage_enabled = False
        if job.configuration and isinstance(job.configuration, dict):
            coverage_enabled = job.configuration.get("coverage", False)

        exit_code, stdout, stderr, runtime_ms = run_verilator(rtl_path, tb_path, out_dir, coverage_enabled=coverage_enabled)

        job.exit_code = exit_code
        job.stdout = stdout
        job.stderr = stderr
        job.runtime_ms = runtime_ms
        job.completed_at = datetime.utcnow()

        if exit_code == 0:
            job.status = "PASSED"
        else:
            job.failure_category = classify_failure(exit_code, stdout, stderr)
            # Handle Retry with Exponential Backoff
            if job.attempt_count <= job.max_retries:
                job.status = "RETRYING"
                db.commit()
                # Exponential Backoff delay: 2s, 4s, 8s, 16s...
                delay_seconds = 2 ** (job.attempt_count - 1) * 2
                logger.info(f"Scheduling retry for job {job_id} in {delay_seconds}s (attempt {job.attempt_count}/{job.max_retries})")
                enqueue_delayed_job(job.id, delay_seconds, job.priority)
            else:
                job.status = "FAILED"

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
            failure_category=job.failure_category,
            triggering_analysis_id=job.triggering_analysis_id
        )
        db.add(attempt)
        # Clear consumed triggering_analysis_id
        job.triggering_analysis_id = None
        db.commit()

        # Collect and save artifacts
        try:
            from app.utils.checksum import calculate_sha256
            from app.models.job import SimulationArtifact
            import shutil

            ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", "./artifacts")
            attempt_dir = os.path.join(ARTIFACT_ROOT, job_id, f"attempt-{job.attempt_count}")
            os.makedirs(attempt_dir, exist_ok=True)

            def save_artifact(content, filename, artifact_type):
                if content is None:
                    content = ""
                file_path = os.path.join(attempt_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                size = os.path.getsize(file_path)
                chk = calculate_sha256(file_path)
                art = SimulationArtifact(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    artifact_type=artifact_type,
                    filename=filename,
                    path=file_path,
                    size_bytes=size,
                    checksum=chk
                )
                db.add(art)

            compile_stdout = ""
            sim_stdout = ""
            if job.stdout:
                parts = job.stdout.split("--- SIMULATION STDOUT ---")
                if len(parts) >= 2:
                    compile_stdout = parts[0].replace("--- COMPILE STDOUT ---", "").strip()
                    sim_stdout = parts[1].strip()
                else:
                    compile_stdout = job.stdout

            compile_stderr = ""
            sim_stderr = ""
            if job.stderr:
                parts = job.stderr.split("--- SIMULATION STDERR ---")
                if len(parts) >= 2:
                    compile_stderr = parts[0].replace("--- COMPILE STDERR ---", "").strip()
                    sim_stderr = parts[1].strip()
                else:
                    compile_stderr = job.stderr

            save_artifact(job.stdout, "stdout.txt", "stdout")
            save_artifact(job.stderr, "stderr.txt", "stderr")
            save_artifact(f"--- COMPILE STDOUT ---\n{compile_stdout}\n\n--- COMPILE STDERR ---\n{compile_stderr}", "compile.log", "compile_log")
            save_artifact(f"--- SIMULATION STDOUT ---\n{sim_stdout}\n\n--- SIMULATION STDERR ---\n{sim_stderr}", "simulation.log", "simulation_log")

            # Capture optional waveform.vcd if generated
            sim_waveform_path = os.path.join(out_dir, "waveform.vcd")
            if os.path.exists(sim_waveform_path):
                dest_waveform_path = os.path.join(attempt_dir, "waveform.vcd")
                shutil.copy2(sim_waveform_path, dest_waveform_path)
                size = os.path.getsize(dest_waveform_path)
                chk = calculate_sha256(dest_waveform_path)
                art = SimulationArtifact(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    artifact_type="waveform",
                    filename="waveform.vcd",
                    path=dest_waveform_path,
                    size_bytes=size,
                    checksum=chk
                )
                db.add(art)

            # Capture optional coverage.dat if generated
            coverage_file = os.path.join(out_dir, "coverage.dat")
            if not os.path.exists(coverage_file):
                coverage_file = os.path.join(out_dir, "logs", "coverage.dat")
            if not os.path.exists(coverage_file):
                import glob
                dat_files = glob.glob(os.path.join(out_dir, "**", "*.dat"), recursive=True)
                if dat_files:
                    coverage_file = dat_files[0]

            if os.path.exists(coverage_file):
                dest_cov_path = os.path.join(attempt_dir, os.path.basename(coverage_file))
                shutil.copy2(coverage_file, dest_cov_path)
                size = os.path.getsize(dest_cov_path)
                chk = calculate_sha256(dest_cov_path)
                art = SimulationArtifact(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    artifact_type="coverage",
                    filename=os.path.basename(dest_cov_path),
                    path=dest_cov_path,
                    size_bytes=size,
                    checksum=chk
                )
                db.add(art)

            db.commit()
            # Clean up the temp out_dir to save disk space
            try:
                shutil.rmtree(out_dir)
            except Exception:
                pass
        except Exception as ae:
            logger.error(f"Error collecting artifacts for job {job_id}: {ae}")

        logger.info(f"Job {job_id} attempt {job.attempt_count} completed with status {job.status}")

    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {e}")
        job.status = "FAILED"
        job.failure_category = "INFRASTRUCTURE_ERROR"
        job.failure_summary = str(e)
        job.completed_at = datetime.utcnow()
        
        attempt = SimulationAttempt(
            job_id=job.id,
            attempt_number=job.attempt_count,
            status="FAILED",
            started_at=job.started_at,
            completed_at=job.completed_at,
            exit_code=-1,
            runtime_ms=0,
            stdout="",
            stderr=str(e),
            failure_category="INFRASTRUCTURE_ERROR",
            triggering_analysis_id=job.triggering_analysis_id
        )
        db.add(attempt)
        # Clear consumed triggering_analysis_id
        job.triggering_analysis_id = None
        db.commit()
    finally:
        with active_slots_lock:
            active_slots -= 1
        db.close()

def worker_slot_loop():
    """Single slot loop that continuously dequeues and runs jobs."""
    while True:
        try:
            job_data = dequeue_job(timeout=5)
            if job_data:
                job_id = job_data["job_id"]
                logger.info(f"Dequeued job {job_id}")
                process_job(job_id)
        except Exception as e:
            logger.error(f"Worker slot encountered error: {e}")
            time.sleep(5)

def main():
    logger.info(f"Starting scheduler worker {WORKER_ID} with concurrency {WORKER_CONCURRENCY}...")
    
    # Start heartbeat thread
    hb_thread = threading.Thread(target=run_heartbeat, daemon=True)
    hb_thread.start()
    
    # Start delayed jobs manager thread
    delayed_thread = threading.Thread(target=run_delayed_jobs_manager, daemon=True)
    delayed_thread.start()
    
    # Run the worker slot loops inside a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKER_CONCURRENCY) as executor:
        for _ in range(WORKER_CONCURRENCY):
            executor.submit(worker_slot_loop)

if __name__ == "__main__":
    main()
