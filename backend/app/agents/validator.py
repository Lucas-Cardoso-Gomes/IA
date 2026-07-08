from sqlalchemy.orm import Session
from ..services.search import search_service
from openai import OpenAI
import os
import asyncio

class AuditorAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run_challenger_query(self, content, check_type):
        """Simula um agente desafiador para uma verificação específica"""
        prompt = f"Analise o seguinte conteúdo para {check_type}: {content}. Retorne apenas as divergências encontradas."
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def audit_notebook(self, db: Session, notebook_id: str):
        from ..models.models import Document, DocumentChunk
        docs = db.query(Document).filter(Document.notebook_id == notebook_id).all()
        doc_ids = [str(d.id) for d in docs]
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).all()
        full_context = "\n".join([f"Doc: {c.document_id} Content: {c.content}" for c in chunks])

        # Parallel Inference Pattern (LLM Challenger)
        # In a real scenario, we would trigger multiple LLM calls in parallel
        check_tasks = [
            self.run_challenger_query(full_context, "Consistência de Pesos (Bruto vs Líquido)"),
            self.run_challenger_query(full_context, "Validação de NCM vs Descrição Comercial")
        ]
        
        # Simulating parallel execution results
        # results = await asyncio.gather(*check_tasks)

        prompt = f"""
        Você é o Auditor Chefe da PM Logística. Consolide os resultados da auditoria documental.
        Documentos: {full_context}
        
        Verificações Requeridas:
        1. Pesos: Compare Invoice, Packing List e CRT.
        2. NCM: Valide se a NCM condiz com a descrição.
        
        Retorne um JSON estritamente com:
        {{
            "divergencias": ["lista de strings"],
            "riscos_aduaneiros": ["lista de strings"],
            "status": "APROVADO" ou "ATENÇÃO"
        }}
        """

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )

        return response.choices[0].message.content

auditor_agent = AuditorAgent()
