import redis
from rq import Queue, Worker
from rq.job import Job
from typing import Callable, Any
import uuid
import json

# Redis连接配置
REDIS_URL = "redis://localhost:6379/0"
redis_conn = redis.Redis.from_url(REDIS_URL)
queue = Queue("fusion", connection=redis_conn)

def enqueue_task(func: Callable, *args, **kwargs) -> str:
    job = queue.enqueue(func, *args, **kwargs)
    return job.get_id()

def get_task_status(task_id: str) -> dict:
    job = Job.fetch(task_id, connection=redis_conn)
    return {
        "id": job.id,
        "status": job.get_status(),
        "result": job.result,
        "exc_info": job.exc_info
    }

def cancel_task(task_id: str) -> bool:
    try:
        job = Job.fetch(task_id, connection=redis_conn)
        job.cancel()
        return True
    except Exception:
        return False

def list_tasks(status: str = None, limit: int = 20) -> list:
    jobs = queue.jobs
    result = []
    for job in jobs[:limit]:
        if status and job.get_status() != status:
            continue
        result.append({
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "exc_info": job.exc_info
        })
    return result
