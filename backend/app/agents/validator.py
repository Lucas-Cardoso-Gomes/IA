from sqlalchemy.orm import Session
from ..services.search import search_service
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.compliance_agent import ComplianceAgent
from backend.app.agents.finance_agent import FinanceAgent
import json
import asyncio

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.compliance_agent = ComplianceAgent()
        self.finance_agent = FinanceAgent()

    async def analyze_context(self, content):
        """Passo 1: Analisa os documentos para identificar o tipo e as informações presentes (ex: se tem peso, valores, etc)"""
        prompt = f"""
        Você é um analista de triagem de documentos de logística aduaneira.
        Analise o seguinte conteúdo dos documentos anexados:

        Documentos: {content}

        Sua tarefa é identificar quais tipos de documentos estão presentes e, o mais importante, quais informações ESTRUTURAIS existem neles.
        Por exemplo: existem informações de peso? Existem valores? Existe NCM listada? Existem informações do consignatário/remetente?

        Não invente nada, apenas resuma o que realmente foi encontrado no texto, limitando-se estritamente aos dados presentes.
        """
        response = self.client.chat.completions.create(
            model="gemma3:1b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content

    async def generate_audit_prompt(self, analysis_result):
        """Passo 2: Cria um prompt personalizado com as verificações que fazem sentido para o contexto"""
        prompt = f"""
        Com base na seguinte análise dos documentos presentes em um processo aduaneiro:

        Análise Inicial: {analysis_result}

        Crie uma lista de "Verificações Requeridas" para uma auditoria aduaneira.
        A regra de ouro é: SÓ INCLUA UMA VERIFICAÇÃO SE OS DADOS NECESSÁRIOS PARA ELA ESTIVEREM PRESENTES.
        Por exemplo, não peça para verificar consistência de peso se não houver peso no documento. Não peça validação de NCM se não houver NCM.

        Retorne APENAS a lista enumerada das verificações a serem feitas, sem nenhum outro texto antes ou depois.
        """
        response = self.client.chat.completions.create(
            model="gemma3:1b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content

    async def audit_notebook(self, db: Session, notebook_id: str):
        from ..models.models import Document, DocumentChunk
        docs = db.query(Document).filter(Document.notebook_id == notebook_id).all()
        doc_ids = [str(d.id) for d in docs]
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).all()
        full_context = "\n".join([f"Doc: {c.document_id} Content: {c.content}" for c in chunks])

        # Passo 1: Analisa o conteúdo
        analysis_result = await self.analyze_context(full_context)
        
        # Passo 2: Gera o prompt de auditoria personalizado
        custom_checks = await self.generate_audit_prompt(analysis_result)

        # Passo 3: Auditoria final baseada apenas no que existe
        prompt = f"""
        Você é o Auditor Chefe da PM Logística. Sua função é analisar EXCLUSIVAMENTE os documentos fornecidos e apontar problemas reais, sem inventar informações.

        Documentos: {full_context}
        
        Faça rigorosamente APENAS as seguintes verificações:
        {custom_checks}

        Se algo solicitado não puder ser verificado devido à falta de informação nos documentos, não considere como erro, apenas ignore ou informe que não consta.
        NUNCA invente dados como "peso não bate" se não houver peso no documento.
        
        Retorne um JSON estritamente com:
        {{
            "divergencias": ["lista de strings com divergências reais baseadas apenas no texto"],
            "riscos_aduaneiros": ["lista de strings com riscos encontrados"],
            "status": "APROVADO" ou "ATENÇÃO"
        }}
        """

        response = self.client.chat.completions.create(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.0
        )

        base_result = json.loads(response.choices[0].message.content)

        # Consolidação com os agentes especialistas (executados em paralelo)
        compliance_task = asyncio.create_task(self.compliance_agent.analyze(full_context))
        finance_task = asyncio.create_task(self.finance_agent.analyze(full_context))

        comp_res, fin_res = await asyncio.gather(compliance_task, finance_task)

        # Mesclando os resultados
        base_result["riscos_aduaneiros"].extend(comp_res.get("riscos", []))
        base_result["divergencias"].extend(fin_res.get("divergencias_financeiras", []))

        return json.dumps(base_result)

auditor_agent = AuditorAgent()
