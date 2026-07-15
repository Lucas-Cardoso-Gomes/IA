from fastapi import FastAPI

app = FastAPI(title="PM Logística Backend API", version="1.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Endpoints for task polling and other features will be added here
from celery.result import AsyncResult
from backend.app.celery_app import celery_app
from fastapi import APIRouter

router = APIRouter()

@router.get("/tasks/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return result

app.include_router(router)
