import os
from sqlalchemy.orm import Session
from ..models.models import Document, DocumentChunk
from .parser import parser_service
from .embeddings import embedding_service
import uuid

class IngestionService:
    async def ingest_document(self, db: Session, file_path: str, filename: str, notebook_id=None, is_global=False):
        doc = Document(
            notebook_id=notebook_id,
            filename=filename,
            storage_path=file_path,
            is_global=is_global
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        parsed_docs = await parser_service.parse_file(file_path)

        for i, p_doc in enumerate(parsed_docs):
            content = p_doc.text
            page_number = p_doc.metadata.get("page_number", i + 1)
            embedding = embedding_service.get_embedding(content)

            chunk = DocumentChunk(
                document_id=doc.id,
                content=content,
                embedding=embedding,
                page_number=page_number,
                bounding_box=p_doc.metadata.get("bounding_box", {})
            )
            db.add(chunk)
        
        db.commit()
        return doc

ingestion_service = IngestionService()
