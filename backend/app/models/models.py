from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
import uuid
from ..database import Base

def gen_uuid():
    return str(uuid.uuid4())

class Notebook(Base):
    __tablename__ = "notebooks"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, nullable=False)

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=gen_uuid)
    notebook_id = Column(String, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String, nullable=False)
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"))
    content = Column(String, nullable=False)
    embedding = Column(JSON) # Trocamos de Vector(1536) para JSON nativo do SQLite
    page_number = Column(Integer)
    bounding_box = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())