import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cria um arquivo local do SQLite na pasta do projeto
SQLALCHEMY_DATABASE_URL = "sqlite:///./pmlogistica.db"

# connect_args é necessário para o SQLite rodar bem com o Streamlit
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()