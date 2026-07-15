from backend.app.agents.base_agent import BaseAgent

class ComplianceAgent(BaseAgent):
    async def analyze(self, content: str) -> dict:
        prompt = f"""
        Você é o Agente de Compliance Aduaneiro.
        Analise o texto: {content}

        Sua função é cruzar descrições físicas e encontrar riscos regulamentares (ex: restrições de NCM).
        Retorne um JSON com:
        {{ "riscos": ["lista de riscos de compliance"] }}
        """
        response = self.client.chat.completions.create(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        import json
        return json.loads(response.choices[0].message.content)
