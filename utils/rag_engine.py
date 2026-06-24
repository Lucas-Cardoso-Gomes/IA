import os
import io
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.document_parser import extract_text_from_file

# Initialize embeddings globally to avoid reloading
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
persist_directory = "./data/chroma_db"

def get_vector_store():
    """Returns the Chroma vector store instance."""
    return Chroma(
        collection_name="admin_knowledge_base",
        embedding_function=embeddings_model,
        persist_directory=persist_directory
    )

def ingest_document(file_obj, filename):
    """
    Extracts text from a document, splits it, and adds it to the vector store.
    """
    text = extract_text_from_file(file_obj, filename)
    if not text or text.startswith("Error"):
        return False, text
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_text(text)
    
    # Store chunks in Chroma
    vector_store = get_vector_store()
    
    # Optional metadata
    metadatas = [{"source": filename} for _ in chunks]
    
    vector_store.add_texts(texts=chunks, metadatas=metadatas)
    
    return True, f"Successfully ingested {len(chunks)} chunks from {filename}."

def get_retriever():
    """Returns a retriever for the vector store."""
    vector_store = get_vector_store()
    return vector_store.as_retriever(search_kwargs={"k": 3})
