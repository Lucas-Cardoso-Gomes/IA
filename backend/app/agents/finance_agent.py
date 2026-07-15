from backend.app.agents.base_agent import BaseAgent

class FinanceAgent(BaseAgent):
    async def analyze(self, content: str) -> dict:
        prompt = f"""
        Você é o Agente Financeiro e Fiscal Aduaneiro.
        Analise o texto: {content}

        Sua função é conferir pesos, valores e cruzar informações entre Invoice e Packing List.
        Retorne um JSON com:
        {{ "divergencias_financeiras": ["lista de divergências"] }}
        """
        response = self.client.chat.completions.create(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        import json
        return json.loads(response.choices[0].message.content)
