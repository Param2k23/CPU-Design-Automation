import httpx
import time

job = httpx.post('http://localhost:8000/jobs', json={'design_name':'alu','test_name':'fail'}).json()
job_id = job["id"]
print('Job created:', job_id)

time.sleep(8)

job_failed = httpx.get(f'http://localhost:8000/jobs/{job_id}').json()
print('Status:', job_failed['status'])

analysis = httpx.post(f'http://localhost:8000/jobs/{job_id}/analyze').json()
print('Analysis:', analysis)

analyses = httpx.get(f'http://localhost:8000/jobs/{job_id}/analyses').json()
print('Analyses count:', len(analyses))

revalidate = httpx.post(f'http://localhost:8000/jobs/{job_id}/revalidate').json()
print('Revalidate status:', revalidate['status'])

time.sleep(8)
final = httpx.get(f'http://localhost:8000/jobs/{job_id}').json()
print('Final Status:', final['status'])
print('Final Attempt Count:', final['attempt_count'])
