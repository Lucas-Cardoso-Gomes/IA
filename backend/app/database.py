import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
import chromadb

# Configuração do VectorDB (ChromaDB)
chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)

def get_vector_collection():
    return chroma_client.get_or_create_collection(name="documents_collection")

# Configuração do Banco de Dados Relacional (SQL)
SQLALCHEMY_DATABASE_URL = settings.DB_CONNECTION

# connect_args é necessário para o SQLite rodar bem com o Streamlit se usando SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()