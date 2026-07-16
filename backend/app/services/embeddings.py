from sentence_transformers import SentenceTransformer
import gc
from typing import List

class EmbeddingService:
    def __init__(self):
        # Baixa um modelo leve e otimizado para embeddings na primeira execução
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_embedding(self, text: str):
        text = str(text or "").replace("\n", " ")
        # Gera o vetor matemático e converte para uma lista simples do Python
        embedding = self.model.encode(text).tolist()
        return embedding

    def get_embeddings_batch(self, texts: List[str]):
        cleaned_texts = [str(text or "").replace("\n", " ") for text in texts]
        embeddings = self.model.encode(cleaned_texts).tolist()

        # Otimização de RAM
        gc.collect()

        return embeddings

embedding_service = EmbeddingService()