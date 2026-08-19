import os
import redis
import json

import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# For blocking operations like brpop, socket_timeout must be greater than the brpop timeout.
redis_client = redis.Redis.from_url(
    REDIS_URL,
    socket_timeout=10,
    socket_connect_timeout=5,
    health_check_interval=30
)

import time

QUEUE_HIGH = "queue:high"
QUEUE_NORMAL = "queue:normal"
QUEUE_LOW = "queue:low"
DELAYED_JOBS = "delayed_jobs"

def enqueue_job(job_id: str, priority: str = "normal"):
    priority = (priority or "normal").lower()
    if priority == "high":
        queue_name = QUEUE_HIGH
    elif priority == "low":
        queue_name = QUEUE_LOW
    else:
        queue_name = QUEUE_NORMAL
        
    job_data = {"job_id": job_id, "priority": priority}
    redis_client.lpush(queue_name, json.dumps(job_data))

def dequeue_job(timeout: int = 5):
    # brpop from high, then normal, then low in priority order
    result = redis_client.brpop([QUEUE_HIGH, QUEUE_NORMAL, QUEUE_LOW], timeout=timeout)
    if result:
        queue_name, data = result
        return json.loads(data)
    return None

def enqueue_delayed_job(job_id: str, delay_seconds: int, priority: str = "normal"):
    run_at = time.time() + delay_seconds
    job_data = {"job_id": job_id, "priority": priority}
    redis_client.zadd(DELAYED_JOBS, {json.dumps(job_data): run_at})

def process_delayed_jobs():
    now = time.time()
    # Fetch all jobs ready to run
    jobs = redis_client.zrangebyscore(DELAYED_JOBS, 0, now)
    for job_str in jobs:
        # Atomic check and remove
        if redis_client.zrem(DELAYED_JOBS, job_str) > 0:
            job_data = json.loads(job_str)
            enqueue_job(job_data["job_id"], job_data["priority"])

def get_queue_depths():
    return {
        "high": redis_client.llen(QUEUE_HIGH),
        "normal": redis_client.llen(QUEUE_NORMAL),
        "low": redis_client.llen(QUEUE_LOW),
        "delayed": redis_client.zcard(DELAYED_JOBS)
    }

