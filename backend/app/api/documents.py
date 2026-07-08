from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from ...database import get_db
from ...services.ingestion import ingestion_service
from ...models.models import Document, Notebook
import shutil
import os
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), notebook_id: Optional[str] = Form(None), is_global: bool = Form(False), db: Session = Depends(get_db)):
    temp_dir = "temp_storage"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    nb_id = uuid.UUID(notebook_id) if notebook_id else None
    doc = await ingestion_service.ingest_document(db, file_path, file.filename, notebook_id=nb_id, is_global=is_global)
    return {"id": doc.id, "filename": doc.filename}

@router.get("/")
async def list_documents(notebook_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if notebook_id: query = query.filter(Document.notebook_id == notebook_id)
    else: query = query.filter(Document.is_global == True)
    return query.all()

@router.post("/notebooks")
async def create_notebook(title: str, user_id: str, db: Session = Depends(get_db)):
    notebook = Notebook(title=title, user_id=uuid.UUID(user_id))
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook
