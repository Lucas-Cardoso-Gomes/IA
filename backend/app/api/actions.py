from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..agents.validator import auditor_agent
from ..integrations.siscomex import siscomex_client
import json

router = APIRouter()

@router.post("/audit/{notebook_id}")
async def audit_process(notebook_id: str, db: Session = Depends(get_db)):
    result = await auditor_agent.audit_notebook(db, notebook_id)
    return json.loads(result)

@router.post("/generate-due")
async def create_due(data: dict):
    payload = siscomex_client.generate_due_payload(data)
    result = siscomex_client.register_due(payload)
    return result
