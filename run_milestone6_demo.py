import time
import httpx
import os
import sys

API_URL = os.getenv("API_URL", "http://localhost:8000")

def wait_for_job(client, job_id, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = client.get(f"/jobs/{job_id}")
        assert res.status_code == 200
        data = res.json()
        if data["status"] not in ("QUEUED", "RUNNING"):
            return data
        time.sleep(1)
    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")

def wait_for_regression(client, reg_id, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = client.get(f"/regressions/{reg_id}")
        assert res.status_code == 200
        data = res.json()
        if data["status"] not in ("QUEUED", "RUNNING"):
            return data
        time.sleep(1)
    raise TimeoutError(f"Regression {reg_id} did not complete in {timeout}s")

def main():
    print("=" * 60)
    print("        MILESTONE 6 — AI-ASSISTED VERIFICATION DEMO")
    print("=" * 60)
    
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        # Check health
        try:
            health = client.get("/health").json()
            print(f"API Health check: {health}")
        except Exception as e:
            print(f"Could not connect to API at {API_URL}: {e}")
            sys.exit(1)

        # 1. Submit passing ALU job
        print("\n[1] Submitting a passing ALU job...")
        pass_resp = client.post("/jobs", json={
            "design_name": "alu",
            "test_name": "pass"
        })
        assert pass_resp.status_code == 200
        pass_job = pass_resp.json()
        print(f"Submitted ALU pass job, ID: {pass_job['id']}")
        
        print("Waiting for passing job to complete...")
        pass_job_res = wait_for_job(client, pass_job["id"])
        print(f"ALU pass job completed with status: {pass_job_res['status']}")

        # 2. Submit intentionally failing ALU job
        print("\n[2] Submitting a failing ALU job...")
        fail_resp = client.post("/jobs", json={
            "design_name": "alu",
            "test_name": "fail"
        })
        assert fail_resp.status_code == 200
        fail_job = fail_resp.json()
        print(f"Submitted ALU fail job, ID: {fail_job['id']}")
        
        print("Waiting for failing job to complete...")
        fail_job_res = wait_for_job(client, fail_job["id"])
        print(f"ALU fail job completed with status: {fail_job_res['status']}, exit_code: {fail_job_res['exit_code']}")

        # 3. Run deterministic analysis
        print("\n[3] Running deterministic (rule-based) analysis on the failed job...")
        rule_resp = client.post(f"/jobs/{fail_job['id']}/analyze", json={"analyzer": "rule_based"})
        assert rule_resp.status_code == 200
        rule_analysis = rule_resp.json()
        print(f"Analyzer used: {rule_analysis['analyzer_type']}")
        print(f"Failure Category: {rule_analysis['failure_category']}")
        print(f"Summary: {rule_analysis['summary']}")
        print(f"Suspected Root Cause: {rule_analysis['suspected_root_cause']}")

        # 4. Run hybrid analysis
        print("\n[4] Running hybrid analysis on the failed job...")
        hybrid_resp = client.post(f"/jobs/{fail_job['id']}/analyze", json={"analyzer": "hybrid"})
        assert hybrid_resp.status_code == 200
        hybrid_analysis = hybrid_resp.json()
        print(f"Analyzer used: {hybrid_analysis['analyzer_type']}")
        print(f"Failure Category: {hybrid_analysis['failure_category']}")
        print(f"Summary: {hybrid_analysis['summary']}")
        print(f"Suspected Root Cause: {hybrid_analysis['suspected_root_cause']}")
        print(f"Confidence score: {hybrid_analysis['confidence']}")
        print(f"Affected component: {hybrid_analysis.get('affected_component')}")
        print(f"Suggested next test: {hybrid_analysis.get('suggested_next_test')}")

        # 5. Display structured root cause, evidence and recommended fix
        print("\n[5-7] Detailed Diagnostic Info:")
        print(f"Recommended Fix: {hybrid_analysis['recommended_fix']}")
        print("Collected Evidence details:")
        for ev in hybrid_analysis.get("evidence", []):
            print(f" - {ev}")

        # 8. Show analysis history
        print("\n[8] Getting analysis history for the job...")
        history_resp = client.get(f"/jobs/{fail_job['id']}/analyses")
        assert history_resp.status_code == 200
        analyses = history_resp.json()
        print(f"Total analyses run on this job: {len(analyses)}")
        for idx, a in enumerate(reversed(analyses)):
            print(f"  {idx + 1}. Time: {a['created_at']}, Type: {a['analyzer_type']}, Category: {a['failure_category']}")

        # 9. Revalidate the failed job
        print("\n[9] Revalidating the failed job using triggering analysis ID...")
        reval_resp = client.post(f"/jobs/{fail_job['id']}/revalidate", json={"triggering_analysis_id": hybrid_analysis["id"]})
        assert reval_resp.status_code == 200
        reval_job = reval_resp.json()
        print(f"Revalidated job status: {reval_job['status']}")
        
        print("Waiting for revalidated job to finish execution...")
        reval_job_res = wait_for_job(client, fail_job["id"])
        print(f"Revalidated job finished with status: {reval_job_res['status']}")

        # 10. Display attempt history
        print("\n[10] Showing execution attempt history for the job...")
        attempts_resp = client.get(f"/jobs/{fail_job['id']}/attempts")
        assert attempts_resp.status_code == 200
        attempts = attempts_resp.json()
        print(f"Total execution attempts: {len(attempts)}")
        for att in attempts:
            print(f"  Attempt {att['attempt_number']}: status={att['status']}, triggering_analysis_id={att.get('triggering_analysis_id')}")

        # 11. Run a small regression
        print("\n[11] Running a small regression with pass/fail tests...")
        reg_resp = client.post("/regressions", json={
            "name": "m6-demo-regression",
            "design_name": "alu",
            "tests": ["pass", "fail"]
        })
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        print(f"Submitted regression '{reg_data['name']}' with ID: {reg_data['id']}")
        
        print("Waiting for regression to complete...")
        wait_for_regression(client, reg_data["id"])
        print("Regression run completed!")

        # Perform analysis on the failed jobs in the regression to trigger intelligence
        reg_jobs_resp = client.get(f"/regressions/{reg_data['id']}/results")
        for j in reg_jobs_resp.json():
            if j["status"] == "FAILED":
                client.post(f"/jobs/{j['job_id']}/analyze", json={"analyzer": "hybrid"})

        # 12. Display regression intelligence
        print("\n[12] Showing regression intelligence analysis:")
        intel_resp = client.get(f"/regressions/{reg_data['id']}/intelligence")
        assert intel_resp.status_code == 200
        intel = intel_resp.json()
        print(f"Regression ID: {intel['regression_id']}")
        print(f"Total Failures: {intel['total_failures']}")
        print(f"Unique Failure Clusters: {intel['unique_failure_clusters']}")
        print(f"Failure Categories: {intel['failure_categories']}")
        print(f"Affected Designs: {intel['affected_designs']}")
        print(f"Top Root Causes: {intel['top_root_causes']}")
        print(f"Recommended Actions: {intel['recommended_actions']}")

        # 13. Display AI/analysis Prometheus metrics
        print("\n[13] Displaying AI/analysis Prometheus metrics:")
        metrics_resp = client.get("/metrics")
        assert metrics_resp.status_code == 200
        for line in metrics_resp.text.splitlines():
            if "cpu_verification_" in line:
                print(line)

    print("\n" + "=" * 60)
    print("               DEMO COMPLETE SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
