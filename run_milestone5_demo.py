import time
import requests
import json

API_URL = "http://localhost:8000"

def wait_for_regression(reg_id, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(f"{API_URL}/regressions/{reg_id}")
        if res.status_code == 200:
            data = res.json()
            if data["status"] in ("PASSED", "FAILED", "CANCELLED"):
                return data
        time.sleep(2)
    return None

def main():
    print("==================================================")
    print("MILESTONE 5 REGRESSION DEMO")
    print("==================================================")

    # 1. List available designs
    print("\n1. Listing available designs (GET /designs)...")
    res = requests.get(f"{API_URL}/designs")
    designs = res.json()
    for d in designs:
        print(f"- {d['name']}: {d['description']}")

    # 2. Show tests available for ALU
    print("\n2. Discovering tests for ALU (GET /designs/alu/tests)...")
    res = requests.get(f"{API_URL}/designs/alu/tests")
    alu_tests = res.json()
    print(json.dumps(alu_tests, indent=2))

    # 3. Create a passing ALU regression (uses "pass" test)
    print("\n3. Creating passing ALU regression (POST /regressions)...")
    res = requests.post(f"{API_URL}/regressions", json={
        "name": "alu-pass-regression",
        "design_name": "alu",
        "tests": ["pass"],
        "priority": "normal"
    })
    pass_reg = res.json()
    pass_reg_id = pass_reg["id"]
    print(f"Passing Regression ID: {pass_reg_id}")
    print("Waiting for passing regression to complete...")
    wait_for_regression(pass_reg_id)

    # 4. Create a failing ALU regression (uses "pass" and "fail" tests)
    print("\n4. Creating failing ALU regression (POST /regressions)...")
    res = requests.post(f"{API_URL}/regressions", json={
        "name": "alu-fail-regression",
        "design_name": "alu",
        "tests": ["pass", "fail"],
        "priority": "normal"
    })
    fail_reg = res.json()
    fail_reg_id = fail_reg["id"]
    print(f"Failing Regression ID: {fail_reg_id}")
    print("Waiting for failing regression to complete...")
    wait_for_regression(fail_reg_id)

    # 5. Print regression status
    print("\n5. Printing Regression Status (GET /regressions/{id})...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}")
    print(json.dumps(res.json(), indent=2))

    # 6. Print individual test results
    print("\n6. Printing Regression Results (GET /regressions/{id}/results)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/results")
    print(json.dumps(res.json(), indent=2))

    # 7. Print failure categories
    print("\n7. Printing Regression Failures (GET /regressions/{id}/failures)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/failures")
    print(json.dumps(res.json(), indent=2))

    # 8. Print failure clusters
    print("\n8. Printing Failure Clusters (GET /regressions/{id}/failure-clusters)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/failure-clusters")
    print(json.dumps(res.json(), indent=2))

    # 9. Print regression summary scorecard
    print("\n9. Printing Regression Scorecard Summary (GET /regressions/{id}/summary)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/summary")
    print(json.dumps(res.json(), indent=2))

    # 10. Print generated artifacts
    print("\n10. Printing Regression Artifacts (GET /regressions/{id}/artifacts)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/artifacts")
    print(json.dumps(res.json(), indent=2))

    # 11. Print regression history
    print("\n11. Printing Regression History (GET /regressions/{id}/history)...")
    res = requests.get(f"{API_URL}/regressions/{fail_reg_id}/history")
    print(json.dumps(res.json(), indent=2))

    # 12. Print Prometheus regression metrics
    print("\n12. Printing Prometheus Regression Metrics (GET /metrics)...")
    res = requests.get(f"{API_URL}/metrics")
    for line in res.text.splitlines():
        if "regression" in line or "cluster" in line:
            print(line)

if __name__ == "__main__":
    main()
