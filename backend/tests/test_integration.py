import time
import requests

API_URL = "http://api:8000"

POLL_INTERVAL = 2   # seconds between status checks
JOB_TIMEOUT = 90    # seconds; Verilator compilation + simulation takes ~22s under normal load;
                    # 90s gives ample margin for Docker scheduling latency and CI runner variance.

def wait_for_job(job_id, timeout=JOB_TIMEOUT):
    """Poll GET /jobs/{job_id} until the job reaches a terminal state or timeout expires."""
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed >= timeout:
            print(f"\n[wait_for_job] Timed out after {elapsed:.1f}s waiting for job {job_id}")
            return None
        res = requests.get(f"{API_URL}/jobs/{job_id}")
        if res.status_code == 200:
            data = res.json()
            if data["status"] in ("PASSED", "FAILED", "CANCELLED"):
                return data
        time.sleep(POLL_INTERVAL)

def test_integration_pass():
    # Submit job
    res = requests.post(f"{API_URL}/jobs", json={
        "design_name": "alu",
        "test_name": "pass"
    })
    assert res.status_code == 200
    job_id = res.json()["id"]

    # Wait for completion
    final_job = wait_for_job(job_id)
    assert final_job is not None
    assert final_job["status"] == "PASSED"
    assert final_job["exit_code"] == 0

def test_integration_fail():
    # Submit job
    res = requests.post(f"{API_URL}/jobs", json={
        "design_name": "alu",
        "test_name": "fail"
    })
    assert res.status_code == 200
    job_id = res.json()["id"]

    # Wait for completion
    final_job = wait_for_job(job_id)
    assert final_job is not None
    assert final_job["status"] == "FAILED"
    assert final_job["exit_code"] != 0
    assert final_job["failure_category"] == "ASSERTION_FAILURE"

    # Retry job
    res_retry = requests.post(f"{API_URL}/jobs/{job_id}/retry")
    assert res_retry.status_code == 200
    
    # Wait for completion again
    retry_final_job = wait_for_job(job_id)
    assert retry_final_job is not None
    assert retry_final_job["status"] == "FAILED"
    assert retry_final_job["attempt_count"] == 2
