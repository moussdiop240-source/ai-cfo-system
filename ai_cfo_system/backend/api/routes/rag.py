import os

from fastapi import APIRouter
from pydantic import BaseModel

from ...rag.knowledge_base import KNOWLEDGE_BASE
from ...rag.pipeline import RAGPipeline

router = APIRouter(prefix="/rag", tags=["rag"])


class IndexRequest(BaseModel):
    title:    str
    content:  str
    category: str  = "finance"
    min_role: str  = "analyst"


class SearchRequest(BaseModel):
    query:     str
    top_k:     int = 5
    user_role: str = "analyst"


@router.post("/index")
def index_document(request: IndexRequest):
    """Index a new document into pgvector."""
    db_url = os.getenv("DATABASE_URL")
    pipeline = RAGPipeline(db_url=db_url)

    doc_id = pipeline.index_document(
        content=request.content,
        metadata={
            "title":    request.title,
            "category": request.category,
            "min_role": request.min_role,
        },
    )

    return {"doc_id": doc_id, "indexed": True}


@router.post("/search")
def search(request: SearchRequest):
    """Search the knowledge base."""
    db_url = os.getenv("DATABASE_URL")
    pipeline = RAGPipeline(db_url=db_url)
    chunks = pipeline.retrieve(request.query, top_k=request.top_k, user_role=request.user_role)

    return {
        "query": request.query,
        "results": [c.to_dict() for c in chunks],
        "total": len(chunks),
    }


@router.get("/knowledge-base")
def list_knowledge_base():
    """List all 20 built-in knowledge base documents."""
    return {
        "total": len(KNOWLEDGE_BASE),
        "documents": [
            {
                "id": d["id"],
                "title": d["title"],
                "category": d["category"],
                "preview": d["content"][:200],
            }
            for d in KNOWLEDGE_BASE
        ],
    }
