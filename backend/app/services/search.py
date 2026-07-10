import numpy as np
from sqlalchemy.orm import Session
from ..models.models import DocumentChunk, Document
from .embeddings import embedding_service

def cosine_similarity(v1, v2):
    """Calcula a similaridade entre os vetores da IA"""
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class SearchService:
    def hybrid_search(self, db: Session, query: str, notebook_id: str = None, top_k=5):
        query_embedding = embedding_service.get_embedding(query)
        query_words = set(query.lower().split())

        # Puxa todos os fragmentos do banco
        if notebook_id:
            chunks = db.query(DocumentChunk).join(Document).filter(
                (Document.is_global == True) | (Document.notebook_id == notebook_id)
            ).all()
        else:
            chunks = db.query(DocumentChunk).join(Document).filter(Document.is_global == True).all()

        scores = {}

        for chunk in chunks:
            # 1. Busca Semântica (IA)
            semantic_score = 0
            if chunk.embedding:
                semantic_score = cosine_similarity(query_embedding, chunk.embedding)
            
            # 2. Busca Lexical (Palavras-chave)
            chunk_words = set(chunk.content.lower().split())
            overlap = len(query_words.intersection(chunk_words))
            lexical_score = overlap / len(query_words) if query_words else 0

            # Peso Final: (Semântico * 0.6) + (Lexical * 0.4)
            scores[chunk.id] = (semantic_score * 0.6) + (lexical_score * 0.4)

        # Ordena pelos melhores resultados
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_ids = [r[0] for r in sorted_ids[:top_k]]

        id_to_chunk = {chunk.id: chunk for chunk in chunks}
        return [id_to_chunk[cid] for cid in top_ids if cid in id_to_chunk]

search_service = SearchService()