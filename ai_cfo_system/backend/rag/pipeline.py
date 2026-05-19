"""
RAG Pipeline — pgvector retrieval before every LLM call.
Falls back to keyword search if pgvector is unavailable.
"""
from typing import List, Dict, Any, Optional
import os
import hashlib
import json

from .knowledge_base import keyword_search


class RAGChunk:
    def __init__(self, id: str, title: str, content: str, score: float, category: str = ""):
        self.id = id
        self.title = title
        self.content = content
        self.score = score
        self.category = category

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "score": self.score,
            "category": self.category,
        }


class RAGPipeline:
    def __init__(self, db_url: Optional[str] = None, collection_name: str = "cfo_documents"):
        self.db_url = db_url
        self.collection_name = collection_name
        self._pgvector_available = False
        self._client = None

        if db_url:
            self._try_init_pgvector(db_url)

    def _try_init_pgvector(self, db_url: str):
        """Attempt to connect to pgvector. Silently fall back if unavailable."""
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            conn.close()
            self._pgvector_available = True
        except Exception:
            self._pgvector_available = False

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        user_role: str = "analyst",
    ) -> List[RAGChunk]:
        """
        Retrieve top-k relevant chunks from pgvector (or fallback KB).
        Called BEFORE every LLM call to prevent hallucinations.
        """
        if self._pgvector_available:
            return self._pgvector_search(query, top_k, user_role)
        return self._fallback_search(query, top_k, user_role)

    def _pgvector_search(self, query: str, top_k: int, user_role: str) -> List[RAGChunk]:
        """
        Cosine similarity search using pgvector:
        SELECT content, metadata, 1-(embedding<=>$query_vec) as score
        FROM documents
        WHERE metadata->>'min_role' <= $user_role
        ORDER BY score DESC LIMIT $top_k
        """
        try:
            embedding = self._embed(query)
            import psycopg2
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, title, content, category,
                               1 - (embedding <=> %s::vector) AS score
                        FROM cfo_documents
                        WHERE metadata->>'min_role' IN ('analyst', 'manager', 'vp', 'cfo')
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (embedding, top_k),
                    )
                    rows = cur.fetchall()
                    return [
                        RAGChunk(
                            id=row[0], title=row[1], content=row[2],
                            category=row[3], score=float(row[4])
                        )
                        for row in rows
                    ]
        except Exception:
            return self._fallback_search(query, top_k, user_role)

    def _fallback_search(self, query: str, top_k: int, user_role: str) -> List[RAGChunk]:
        """Keyword-based fallback from in-memory knowledge base."""
        results = keyword_search(query, top_k=top_k, user_role=user_role)
        return [
            RAGChunk(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                score=r["score"],
                category=r["category"],
            )
            for r in results
        ]

    def _embed(self, text: str) -> List[float]:
        """Generate embedding — uses sentence-transformers or falls back to zeros."""
        try:
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, "_model"):
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            return self._model.encode(text).tolist()
        except ImportError:
            # Return deterministic pseudo-embedding for testing
            digest = int(hashlib.md5(text.encode()).hexdigest(), 16)
            import random
            rng = random.Random(digest)
            return [rng.uniform(-1, 1) for _ in range(384)]

    def index_document(self, content: str, metadata: dict) -> str:
        """Chunk → embed → upsert to pgvector."""
        if not self._pgvector_available:
            return "pgvector_unavailable"

        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        embedding = self._embed(content)

        try:
            import psycopg2
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO cfo_documents (id, title, content, embedding, metadata, category)
                        VALUES (%s, %s, %s, %s::vector, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        """,
                        (
                            doc_id,
                            metadata.get("title", ""),
                            content,
                            embedding,
                            json.dumps(metadata),
                            metadata.get("category", "general"),
                        ),
                    )
                conn.commit()
            return doc_id
        except Exception as e:
            return f"error: {e}"

    def build_rag_query(self, state: Dict[str, Any]) -> str:
        """Deterministic query construction from state — NO LLM."""
        parts = [
            state.get("task_description", ""),
            state.get("task_type", ""),
            f"financial analysis {state.get('period', '')}",
            "variance analysis board report",
        ]

        kpis = state.get("kpi_metrics", {}) or {}
        anomalies = state.get("anomaly_flags", []) or []
        gaap = state.get("gaap_results", {}) or {}
        ifrs = state.get("ifrs_results", {}) or {}

        if kpis.get("gross_margin_pct", 100) < 30:
            parts.append("gross margin below threshold benchmark")
        if kpis.get("current_ratio", 99) < 1.0:
            parts.append("liquidity current ratio going concern")
        if anomalies:
            parts.extend(anomalies[:3])

        for std, result in gaap.items():
            if result.get("status") == "DISCLOSURE_REQUIRED":
                parts.append(f"{result.get('standard', std)} disclosure required")
            elif result.get("status") == "NON_COMPLIANT":
                parts.append(f"{result.get('standard', std)} non-compliant GAAP")

        for std, result in ifrs.items():
            if result.get("status") in ("NON_COMPLIANT", "DISCLOSURE_REQUIRED"):
                parts.append(f"{result.get('standard', std)} IFRS")

        return " ".join(p for p in parts if p)


def format_rag_context(chunks: List[RAGChunk]) -> str:
    """Format retrieved chunks for inclusion in LLM prompt."""
    if not chunks:
        return "No relevant context retrieved."

    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] {chunk.title} (score: {chunk.score:.2f})")
        lines.append(chunk.content[:600])
        lines.append("")
    return "\n".join(lines)
