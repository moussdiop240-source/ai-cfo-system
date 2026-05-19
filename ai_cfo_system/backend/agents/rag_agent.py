"""
RAG Agent — retrieves context BEFORE every LLM call.
Deterministic query construction + pgvector cosine similarity search.
"""
from datetime import datetime
from .state import CFOAgentState
from ..rag.pipeline import RAGPipeline, format_rag_context
import os


def rag_agent_node(state: CFOAgentState) -> CFOAgentState:
    """LangGraph node — builds query deterministically and retrieves RAG context."""
    errors  = list(state.get("errors", []))
    audit   = list(state.get("audit_log", []))

    db_url = os.getenv("DATABASE_URL")
    pipeline = RAGPipeline(db_url=db_url)

    query = pipeline.build_rag_query(state)
    user_role = state.get("submitted_by_role", "analyst")
    chunks = pipeline.retrieve(query, top_k=5, user_role=user_role)
    sources = list({c.title for c in chunks})

    audit.append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "rag_agent",
        "action": "retrieval_complete",
        "query": query[:100],
        "chunks_retrieved": len(chunks),
        "sources": sources,
    })

    return {
        **state,
        "rag_chunks": [c.to_dict() for c in chunks],
        "rag_query_used": query,
        "rag_sources_cited": sources,
        "retrieval_confidence": round(sum(c.score for c in chunks) / len(chunks), 3) if chunks else 0.0,
        "agent_statuses": {**state.get("agent_statuses", {}), "rag_agent": "complete"},
        "audit_log": audit,
        "errors": errors,
    }
