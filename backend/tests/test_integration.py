import time
import requests

API_URL = "http://api:8000"

def wait_for_job(job_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(f"{API_URL}/jobs/{job_id}")
        if res.status_code == 200:
            data = res.json()
            if data["status"] in ["PASSED", "FAILED", "CANCELLED"]:
                return data
        time.sleep(1)
    return None

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
