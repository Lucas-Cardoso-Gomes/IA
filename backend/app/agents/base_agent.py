import os
from openai import OpenAI
from backend.app.config import settings

class BaseAgent:
    def __init__(self):
        if settings.OPENAI_TELEMETRY.lower() == 'false':
            os.environ["OPENAI_TELEMETRY"] = "0"
            os.environ["OPENAI_DISABLE_TELEMETRY"] = "1"
        self.client = OpenAI(base_url=settings.OLLAMA_BASE_URL, api_key=settings.OLLAMA_API_KEY)

    async def analyze(self, content: str) -> str:
        raise NotImplementedError
