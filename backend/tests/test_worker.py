import pytest
import redis
import json
from unittest.mock import patch, MagicMock
from app.queue.redis_queue import enqueue_job, dequeue_job, QUEUE_NORMAL

def test_enqueue_dequeue():
    # Mock redis client
    with patch("app.queue.redis_queue.redis_client") as mock_redis:
        # Test enqueue
        enqueue_job("test_job_id", priority="normal")
        mock_redis.lpush.assert_called_once_with(QUEUE_NORMAL, json.dumps({"job_id": "test_job_id", "priority": "normal"}))

        # Test dequeue with item
        mock_redis.brpop.return_value = (QUEUE_NORMAL, json.dumps({"job_id": "test_job_id", "priority": "normal"}))
        job = dequeue_job(timeout=1)
        assert job == {"job_id": "test_job_id", "priority": "normal"}

        # Test dequeue empty (simulating timeout)
        mock_redis.brpop.return_value = None
        job_empty = dequeue_job(timeout=1)
        assert job_empty is None

def test_dequeue_timeout_exception():
    with patch("app.queue.redis_queue.redis_client") as mock_redis:
        # Simulate a socket timeout exception thrown by brpop
        mock_redis.brpop.side_effect = redis.exceptions.TimeoutError("Timeout reading from socket")
        
        with pytest.raises(redis.exceptions.TimeoutError):
            dequeue_job(timeout=1)
