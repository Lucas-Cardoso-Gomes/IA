import os
from openai import OpenAI

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = "gemma3:1b"

    def get_embedding(self, text: str):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=self.model).data[0].embedding

embedding_service = EmbeddingService()
