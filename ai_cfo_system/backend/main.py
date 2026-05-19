"""
AI CFO System — FastAPI entry point.
Production-grade, multi-agent financial intelligence platform.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database.session import create_tables
from .api.routes import tasks, approvals, debate, stream, rag

app = FastAPI(
    title="AI CFO System",
    description=(
        "Production-grade multi-agent financial intelligence platform. "
        "GAAP (12 ASC standards) + IFRS (12 IAS/IFRS standards) compliance. "
        "LangGraph orchestration + RAG + HITL approvals."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tasks.router)
app.include_router(approvals.router)
app.include_router(debate.router)
app.include_router(stream.router)
app.include_router(rag.router)


@app.on_event("startup")
async def startup():
    create_tables()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "compliance": {
            "gaap_standards": 12,
            "ifrs_standards": 12,
            "rag_documents": 20,
        },
    }


@app.get("/")
def root():
    return {
        "service": "AI CFO System",
        "architecture": "4-Layer: Deterministic Math → Schema Enforcers → Secure Infra → RAG",
        "endpoints": {
            "POST /tasks":              "Submit financial analysis task",
            "GET  /tasks/{id}":         "Get task status + results",
            "GET  /tasks/{id}/stream":  "SSE stream for real-time updates",
            "GET  /tasks/{id}/report":  "Get final board report",
            "GET  /approvals/pending":  "Get tasks awaiting CFO approval",
            "POST /approvals/{id}":     "Submit CFO approval decision",
            "POST /debate/run":         "Run 3-round IFRS vs GAAP debate",
            "POST /rag/index":          "Index new document",
            "POST /rag/search":         "Search knowledge base",
        },
    }
