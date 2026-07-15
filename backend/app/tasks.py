from backend.app.celery_app import celery_app
import asyncio
import json
from backend.app.database import SessionLocal

@celery_app.task(name="ingest_document_task")
def ingest_document_task(file_path: str, filename: str, notebook_id=None, is_global=False):
    from backend.app.services.ingestion import ingestion_service
    db = SessionLocal()
    try:
        # Run the async ingestion service synchronously
        loop = asyncio.get_event_loop()
        doc = loop.run_until_complete(
            ingestion_service.ingest_document(db, file_path, filename, notebook_id, is_global)
        )
        return {"status": "success", "document_id": str(doc.id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="audit_notebook_task")
def audit_notebook_task(notebook_id: str):
    from backend.app.agents.validator import auditor_agent
    db = SessionLocal()
    try:
        loop = asyncio.get_event_loop()
        result_str = loop.run_until_complete(
            auditor_agent.audit_notebook(db, notebook_id)
        )
        return json.loads(result_str)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
