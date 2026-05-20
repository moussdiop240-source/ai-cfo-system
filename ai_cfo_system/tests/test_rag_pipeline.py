"""Tests for the RAG pipeline (no pgvector required — uses fallback KB)."""
import sys

import pytest

sys.path.insert(0, ".")

from backend.rag.knowledge_base import KNOWLEDGE_BASE, keyword_search
from backend.rag.pipeline import RAGPipeline, format_rag_context


class TestKnowledgeBase:
    def test_20_documents_present(self):
        assert len(KNOWLEDGE_BASE) == 20

    def test_categories_covered(self):
        cats = {d["category"] for d in KNOWLEDGE_BASE}
        assert "finance" in cats
        assert "gaap" in cats
        assert "ifrs" in cats

    def test_all_have_required_fields(self):
        for doc in KNOWLEDGE_BASE:
            assert "id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "category" in doc

    def test_ids_are_unique(self):
        ids = [d["id"] for d in KNOWLEDGE_BASE]
        assert len(ids) == len(set(ids))


class TestKeywordSearch:
    def test_returns_top_k(self):
        results = keyword_search("revenue recognition ASC 606", top_k=3)
        assert len(results) <= 3

    def test_gaap_query_returns_gaap_docs(self):
        results = keyword_search("ASC 606 revenue recognition 5-step model", top_k=5)
        categories = [r["category"] for r in results]
        assert "gaap" in categories

    def test_ifrs_query_returns_ifrs_docs(self):
        results = keyword_search("IFRS 15 IFRS 16 leases performance obligations", top_k=5)
        categories = [r["category"] for r in results]
        assert "ifrs" in categories

    def test_results_have_score(self):
        results = keyword_search("goodwill impairment", top_k=3)
        for r in results:
            assert "score" in r
            assert 0 <= r["score"] <= 1


class TestRAGPipeline:
    @pytest.fixture
    def pipeline(self):
        return RAGPipeline()  # No pgvector — uses fallback

    def test_retrieve_returns_chunks(self, pipeline):
        chunks = pipeline.retrieve("ASC 842 leases ROU asset", top_k=3)
        assert len(chunks) >= 1

    def test_chunks_have_required_attrs(self, pipeline):
        chunks = pipeline.retrieve("GAAP revenue recognition", top_k=2)
        for chunk in chunks:
            assert hasattr(chunk, "id")
            assert hasattr(chunk, "title")
            assert hasattr(chunk, "content")
            assert hasattr(chunk, "score")

    def test_to_dict_works(self, pipeline):
        chunks = pipeline.retrieve("IFRS provisions", top_k=2)
        for chunk in chunks:
            d = chunk.to_dict()
            assert isinstance(d, dict)
            assert "id" in d

    def test_format_rag_context_non_empty(self, pipeline):
        chunks = pipeline.retrieve("variance analysis board report", top_k=3)
        ctx = format_rag_context(chunks)
        assert len(ctx) > 50
        assert "[1]" in ctx

    def test_format_empty_chunks(self):
        ctx = format_rag_context([])
        assert "No relevant context" in ctx

    def test_build_rag_query_deterministic(self, pipeline):
        state = {
            "task_description": "Q1 variance analysis",
            "task_type": "full_report",
            "period": "Q1 2025",
            "kpi_metrics": {"gross_margin_pct": 28.0},  # below 30% triggers extra term
            "anomaly_flags": ["WARNING: Current ratio below 1.5"],
            "gaap_results": {"asc606": {"status": "DISCLOSURE_REQUIRED", "standard": "ASC 606"}},
            "ifrs_results": {},
        }
        query = pipeline.build_rag_query(state)
        assert "Q1 variance analysis" in query
        assert "gross margin below threshold" in query
        assert "ASC 606" in query
