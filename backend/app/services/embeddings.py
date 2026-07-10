from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Baixa um modelo leve e otimizado para embeddings na primeira execução
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_embedding(self, text: str):
        text = text.replace("\n", " ")
        # Gera o vetor matemático e converte para uma lista simples do Python
        return self.model.encode(text).tolist()

embedding_service = EmbeddingService()