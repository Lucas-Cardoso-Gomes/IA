from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ...database import get_db
from ...services.search import search_service
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    notebook_id: Optional[str] = None
    history: List[dict] = []

@router.post("/query")
async def query_notebook(req: ChatRequest, db: Session = Depends(get_db)):
    context_chunks = search_service.hybrid_search(db, req.message, req.notebook_id)
    system_prompt = "Você é um assistente especialista em logística aduaneira da PM Logística. Use as fontes fornecidas para responder."
    context_text = "\n\n".join([f"Fonte: {c.document_id} Pág: {c.page_number}\n{c.content}" for c in context_chunks])
    messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"Contexto Recueperado:\n{context_text}"}]
    messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})
    response = client.chat.completions.create(model="gpt-4-turbo-preview", messages=messages)
    answer = response.choices[0].message.content
    citations = [{"document_id": str(c.document_id), "page": c.page_number, "bounding_box": c.bounding_box} for c in context_chunks]
    return {"answer": answer, "citations": citations}
