import time
import requests
import json

API_URL = "http://localhost:8000"

def wait_for_job(job_id, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(f"{API_URL}/jobs/{job_id}")
        if res.status_code == 200:
            data = res.json()
            if data["status"] in ("PASSED", "FAILED"):
                return data
        time.sleep(2)
    return None

def main():
    print("==================================================")
    print("MILESTONE 4 MANUAL DEMO")
    print("==================================================")

    # ---------------------------------------------------------------------------
    # PASSING ALU JOB
    # ---------------------------------------------------------------------------
    print("\n1. Submitting a PASSING ALU job...")
    res = requests.post(f"{API_URL}/jobs", json={
        "design_name": "alu",
        "test_name": "pass"
    })
    if res.status_code != 200:
        print(f"Error submitting job: {res.text}")
        return
    job_id = res.json()["id"]
    print(f"Job ID: {job_id}")

    print("Waiting for job to complete...")
    job_data = wait_for_job(job_id)
    if not job_data:
        print("Job timed out!")
        return

    print(f"Status: {job_data['status']}")
    print(f"Attempt Count: {job_data['attempt_count']}")

    # Get Attempts
    print("\nFetching attempt history (GET /jobs/{job_id}/attempts)...")
    res_att = requests.get(f"{API_URL}/jobs/{job_id}/attempts")
    print(json.dumps(res_att.json(), indent=2))

    # Get Artifacts
    print("\nFetching generated artifacts (GET /jobs/{job_id}/artifacts)...")
    res_art = requests.get(f"{API_URL}/jobs/{job_id}/artifacts")
    artifacts = res_art.json()
    print(json.dumps(artifacts, indent=2))

    # Download stdout artifact
    stdout_artifact = next((a for a in artifacts if a["artifact_type"] == "stdout"), None)
    if stdout_artifact:
        art_id = stdout_artifact["id"]
        print(f"\nDownloading stdout artifact (GET /artifacts/{art_id})...")
        res_dl = requests.get(f"{API_URL}/artifacts/{art_id}")
        print("--- stdout.txt content snippet ---")
        print("\n".join(res_dl.text.splitlines()[:10]))
        print("---------------------------------")
        print(f"SHA-256 Checksum: {stdout_artifact['checksum']}")

    # Get summary
    print("\nFetching verification summary (GET /jobs/{job_id}/summary)...")
    res_sum = requests.get(f"{API_URL}/jobs/{job_id}/summary")
    print(json.dumps(res_sum.json(), indent=2))

    # Get history
    print("\nFetching event history (GET /jobs/{job_id}/history)...")
    res_hist = requests.get(f"{API_URL}/jobs/{job_id}/history")
    print(json.dumps(res_hist.json(), indent=2))

    # ---------------------------------------------------------------------------
    # FAILING ALU JOB
    # ---------------------------------------------------------------------------
    print("\n==================================================")
    print("2. Submitting an INTENTIONALLY FAILING ALU job...")
    print("==================================================")
    res_fail = requests.post(f"{API_URL}/jobs", json={
        "design_name": "alu",
        "test_name": "fail"
    })
    fail_job_id = res_fail.json()["id"]
    print(f"Job ID: {fail_job_id}")

    print("Waiting for job to fail...")
    fail_job_data = wait_for_job(fail_job_id)
    print(f"Status: {fail_job_data['status']}")

    # Run Failure Analysis
    print("\nRunning failure analysis (POST /jobs/{job_id}/analyze)...")
    res_anal = requests.post(f"{API_URL}/jobs/{fail_job_id}/analyze")
    print(json.dumps(res_anal.json(), indent=2))

    # Revalidate
    print("\nRevalidating the job (POST /jobs/{job_id}/revalidate)...")
    res_reval = requests.post(f"{API_URL}/jobs/{fail_job_id}/revalidate")
    print(f"Reval status: {res_reval.json()['status']}")

    print("Waiting for second attempt to complete...")
    # wait a bit for worker to dequeue
    time.sleep(2)
    final_fail_job_data = wait_for_job(fail_job_id)
    print(f"Final status: {final_fail_job_data['status']}")
    print(f"Final attempt count: {final_fail_job_data['attempt_count']}")

    # Show both attempts
    print("\nFetching both attempts...")
    res_both_att = requests.get(f"{API_URL}/jobs/{fail_job_id}/attempts")
    print(json.dumps(res_both_att.json(), indent=2))

    # Show artifacts for both attempts
    print("\nFetching artifacts for both attempts...")
    res_both_art = requests.get(f"{API_URL}/jobs/{fail_job_id}/artifacts")
    print(json.dumps(res_both_art.json(), indent=2))

    # Show final summary
    print("\nFetching final verification summary...")
    res_final_sum = requests.get(f"{API_URL}/jobs/{fail_job_id}/summary")
    print(json.dumps(res_final_sum.json(), indent=2))

if __name__ == "__main__":
    main()
