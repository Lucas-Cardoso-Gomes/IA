"""
Continuous Vector Database & Lifelong Memory RAG for Jarvis.
Stores all conversation turns, visual scene summaries, embeddings, timestamps,
and tags on the dedicated fast Intel Optane storage path using LanceDB.
"""

import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from config import VECTOR_DB_PATH, RAG_TOP_K, EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)


class ContinuousMemoryRAG:
    """
    Lifelong continuous memory store based on LanceDB.
    Persists user speech transcripts, AI replies, screen scene descriptions, and metadata.
    """

    def __init__(
        self,
        db_path: Path = VECTOR_DB_PATH,
        table_name: str = "continuous_memory",
        top_k: int = RAG_TOP_K,
    ) -> None:
        """
        Initialize LanceDB vector database on fast storage path.

        Args:
            db_path: Fast storage directory path (Optane DB directory).
            table_name: Table name for continuous memory records.
            top_k: Default number of top context matches to retrieve.
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.table_name = table_name
        self.top_k = top_k
        self._db = None
        self._table = None
        self._embedder = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize LanceDB and embedding model with fallback memory support."""
        try:
            import lancedb

            self._db = lancedb.connect(str(self.db_path))
            logger.info(f"Connected to LanceDB at fast path: {self.db_path}")

            # Check existing tables using list_tables / table_names
            if hasattr(self._db, "table_names"):
                existing_tables = self._db.table_names()
            elif hasattr(self._db, "list_tables"):
                existing_tables = self._db.list_tables()
            else:
                existing_tables = []

            if self.table_name in existing_tables:
                self._table = self._db.open_table(self.table_name)
                logger.info(f"Opened existing memory table '{self.table_name}'")
            else:
                self._table = None
        except Exception as e:
            logger.warning(f"LanceDB init warning: {e}. Memory store running with in-memory fallback list.")
            self._db = None
            self._fallback_records: List[Dict[str, Any]] = []

    def _get_embedding(self, text: str) -> List[float]:
        """
        Compute dense vector embedding for input text.

        Args:
            text: Input text string.

        Returns:
            List of float embedding vector values (384 dimensional).
        """
        if not text:
            return [0.0] * 384

        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
                logger.info(f"Loaded embedding model '{EMBEDDING_MODEL_NAME}'")
            except Exception as err:
                logger.debug(f"SentenceTransformer not available ({err}); using fast deterministic hashing vector.")
                self._embedder = "mock"

        if self._embedder == "mock":
            # Fast deterministic mock embedding vector for fallback environments
            rng = np.random.RandomState(abs(hash(text)) % (2**32))
            vec = rng.randn(384)
            norm = np.linalg.norm(vec)
            return (vec / (norm if norm > 0 else 1.0)).tolist()

        try:
            vector = self._embedder.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            return [0.0] * 384

    def add_memory(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        context_tags: str = "general",
    ) -> None:
        """
        Save a new continuous memory record (conversation turn or visual observation).

        Args:
            text: Memory content (text transcript, screen description, or reply).
            metadata: Additional metadata dictionary (e.g., sender, frame_path, confidence).
            context_tags: Space/comma separated tags (e.g., 'visual', 'conversation', 'game_character').
        """
        if not text or not text.strip():
            return

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        embedding = self._get_embedding(text)
        meta_str = str(metadata) if metadata else ""

        record = {
            "conversation_turn": text.strip(),
            "vector": embedding,
            "timestamp": timestamp,
            "context_tags": context_tags,
            "metadata": meta_str,
        }

        if self._db is not None:
            try:
                # Refresh table reference if not open
                if self._table is None:
                    if hasattr(self._db, "table_names") and self.table_name in self._db.table_names():
                        self._table = self._db.open_table(self.table_name)
                    else:
                        self._table = self._db.create_table(self.table_name, data=[record])
                        logger.info(f"Created new memory table '{self.table_name}' in LanceDB.")
                        return

                self._table.add([record])
                logger.info(f"Memory added to LanceDB: '{text[:40]}...' (tags={context_tags})")
                return
            except Exception as err:
                logger.error(f"Failed to add record to LanceDB table: {err}")

        # Fallback memory store
        if not hasattr(self, "_fallback_records"):
            self._fallback_records = []
        self._fallback_records.append(record)
        logger.info(f"Memory added to fallback store: '{text[:40]}...'")

    def query_memory(self, query_text: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve top_k most relevant historical context records based on vector similarity search.

        Args:
            query_text: Query text string.
            top_k: Number of memory results to return (defaults to self.top_k).

        Returns:
            List of memory record dictionaries sorted by relevance.
        """
        if not query_text or not query_text.strip():
            return []

        limit = top_k or self.top_k
        query_vec = self._get_embedding(query_text)

        if self._table is not None:
            try:
                results = self._table.search(query_vec).limit(limit).to_list()
                return results
            except Exception as err:
                logger.error(f"LanceDB query error: {err}")

        # Fallback memory search
        if hasattr(self, "_fallback_records") and self._fallback_records:
            def cosine_sim(a: List[float], b: List[float]) -> float:
                arr_a, arr_b = np.array(a), np.array(b)
                denom = (np.linalg.norm(arr_a) * np.linalg.norm(arr_b))
                return float(np.dot(arr_a, arr_b) / (denom if denom > 0 else 1e-8))

            scored = [
                (cosine_sim(query_vec, rec["vector"]), rec)
                for rec in self._fallback_records
            ]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [rec for _, rec in scored[:limit]]

        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rag = ContinuousMemoryRAG()
    rag.add_memory("Meu personagem favorito no jogo é o Radahn", context_tags="gaming visual")
    rag.add_memory("Semana passada estudamos fisica quantica", context_tags="conversation study")

    results = rag.query_memory("Quem é o personagem do jogo?")
    print(f"Memory query results count: {len(results)}")
    for r in results:
        print("Match:", r.get("conversation_turn"), "Tags:", r.get("context_tags"))
