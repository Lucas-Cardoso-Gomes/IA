from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.models import DocumentChunk, Document
from .embeddings import embedding_service

class SearchService:
    def rrf(self, results_list, k=60):
        scores = {}
        for results in results_list:
            for rank, doc_id in enumerate(results):
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += 1.0 / (k + rank + 1)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores

    def hybrid_search(self, db: Session, query: str, notebook_id: str = None, top_k=5):
        query_embedding = embedding_service.get_embedding(query)
        
        # 1. Semantic Search (Vector)
        semantic_query = text("""
            SELECT dc.id, 1 - (dc.embedding <=> :embedding) as score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.is_global = TRUE OR d.notebook_id = :notebook_id
            ORDER BY dc.embedding <=> :embedding
            LIMIT :limit
        """)
        
        semantic_results = db.execute(semantic_query, {
            "embedding": str(query_embedding),
            "notebook_id": notebook_id,
            "limit": top_k * 5
        }).fetchall()

        # 2. Lexical Search
        lexical_query = text("""
            SELECT dc.id, ts_rank_cd(to_tsvector('portuguese', dc.content), plainto_tsquery('portuguese', :query)) as score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE (d.is_global = TRUE OR d.notebook_id = :notebook_id)
            AND to_tsvector('portuguese', dc.content) @@ plainto_tsquery('portuguese', :query)
            LIMIT :limit
        """)
        
        lexical_results = db.execute(lexical_query, {
            "query": query,
            "notebook_id": notebook_id,
            "limit": top_k * 5
        }).fetchall()

        # Weighted Score Implementation: (Semantic * 0.6) + (Lexical * 0.4)
        scores = {}
        
        # Normalize and add semantic scores
        for row in semantic_results:
            scores[row[0]] = float(row[1]) * 0.6
            
        # Normalize and add lexical scores
        for row in lexical_results:
            if row[0] in scores:
                scores[row[0]] += float(row[1]) * 0.4
            else:
                scores[row[0]] = float(row[1]) * 0.4
        
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_ids = [r[0] for r in sorted_ids[:top_k]]

        if not top_ids:
            return []
            
        chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(top_ids)).all()
        id_to_chunk = {chunk.id: chunk for chunk in chunks}
        return [id_to_chunk[id] for id in top_ids if id in id_to_chunk]

search_service = SearchService()
