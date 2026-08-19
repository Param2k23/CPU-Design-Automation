import asyncio
import httpx
import time
import sys
import numpy as np

API_URL = "http://localhost:8000"

async def submit_job(client, design, test, priority="normal", max_retries=1):
    url = f"{API_URL}/jobs"
    payload = {
        "design_name": design,
        "test_name": test,
        "priority": priority,
        "max_retries": max_retries
    }
    try:
        res = await client.post(url, json=payload)
        if res.status_code == 200:
            return res.json()["id"]
    except Exception as e:
        print(f"Error submitting job: {e}")
    return None

async def poll_job(client, job_id, timeout=300):
    url = f"{API_URL}/jobs/{job_id}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                if data["status"] in ("PASSED", "FAILED"):
                    # Calculate latency
                    latency = time.time() - start
                    return {
                        "id": job_id,
                        "status": data["status"],
                        "attempt_count": data["attempt_count"],
                        "latency": latency
                    }
        except Exception:
            pass
        await asyncio.sleep(1)
    return {
        "id": job_id,
        "status": "TIMEOUT",
        "attempt_count": 0,
        "latency": timeout
    }

async def run_benchmark(num_jobs=50):
    print(f"Starting benchmark with {num_jobs} workloads...")
    
    # We will mix different designs and tests
    workloads = [
        ("alu", "pass", "high"),
        ("alu", "fail", "normal"),
        ("fifo", "pass", "normal"),
        ("fifo", "fail", "low"),
        ("register_file", "pass", "high"),
        ("register_file", "fail", "normal"),
        ("cache", "pass", "normal"),
        ("cache", "fail", "low")
    ]
    
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        start_time = time.time()
        
        # Submit tasks
        submit_tasks = []
        for i in range(num_jobs):
            design, test, priority = workloads[i % len(workloads)]
            submit_tasks.append(submit_job(client, design, test, priority))
            
        job_ids = await asyncio.gather(*submit_tasks)
        job_ids = [jid for jid in job_ids if jid is not None]
        print(f"Successfully submitted {len(job_ids)}/{num_jobs} jobs. Polling for completion...")
        
        # Poll tasks
        poll_tasks = [poll_job(client, jid) for jid in job_ids]
        results = await asyncio.gather(*poll_tasks)
        
        total_time = time.time() - start_time
        
        # Calculate stats
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        timed_out = sum(1 for r in results if r["status"] == "TIMEOUT")
        retries = sum(r["attempt_count"] - 1 for r in results if r["attempt_count"] > 0)
        
        latencies = [r["latency"] for r in results if r["status"] in ("PASSED", "FAILED")]
        avg_latency = np.mean(latencies) if latencies else 0.0
        p95_latency = np.percentile(latencies, 95) if latencies else 0.0
        
        throughput = len(results) / total_time if total_time > 0 else 0
        reliability = ((passed + failed) / len(results) * 100) if results else 0
        
        # Fetch worker info
        worker_util = "N/A"
        try:
            w_res = await client.get(f"{API_URL}/workers")
            if w_res.status_code == 200:
                workers = w_res.json()
                if workers:
                    avg_cpu = np.mean([w["cpu_util"] for w in workers])
                    worker_util = f"{avg_cpu:.1f}%"
        except Exception:
            pass

        print("\n================ BENCHMARK RESULTS ================")
        print(f"Total Jobs Submitted:         {num_jobs}")
        print(f"Successful Jobs:              {passed}")
        print(f"Failed Jobs:                  {failed}")
        print(f"Timed Out Jobs:               {timed_out}")
        print(f"Throughput (jobs/sec):        {throughput:.2f}")
        print(f"Average Latency (sec):        {avg_latency:.2f}")
        print(f"p95 Latency (sec):            {p95_latency:.2f}")
        print(f"Total Retries Triggered:      {retries}")
        print(f"Average Worker Utilization:   {worker_util}")
        print(f"Job Completion Reliability:   {reliability:.1f}%")
        print("===================================================\n")

if __name__ == "__main__":
    jobs = 50
    if len(sys.argv) > 1:
        try:
            jobs = int(sys.argv[1])
        except ValueError:
            pass
    asyncio.run(run_benchmark(jobs))
