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

QUEUE_NAME = "job_queue"

def enqueue_job(job_id: str, priority: str = "normal"):
    # Real priority queues are more complex, but for MVP we use a single list
    job_data = {"job_id": job_id, "priority": priority}
    redis_client.lpush(QUEUE_NAME, json.dumps(job_data))

def dequeue_job(timeout: int = 5):
    result = redis_client.brpop(QUEUE_NAME, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None
