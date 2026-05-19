from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id           = Column(String(64), primary_key=True)
    task_type    = Column(String(64), nullable=False)
    description  = Column(Text)
    company_name = Column(String(256))
    period       = Column(String(64))
    report_format = Column(String(64), default="board")
    submitted_by  = Column(String(256))
    submitted_at  = Column(DateTime, default=datetime.utcnow)
    status        = Column(String(32), default="pending")  # pending|running|awaiting_approval|complete|error

    # Results
    kpi_metrics      = Column(JSON)
    variance_table   = Column(JSON)
    gaap_results     = Column(JSON)
    ifrs_results     = Column(JSON)
    analysis_narrative = Column(Text)
    final_report     = Column(Text)
    audit_log        = Column(JSON)
    errors           = Column(JSON)

    # Cost tracking
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd    = Column(Float, default=0.0)
    processing_time_ms = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Approval(Base):
    __tablename__ = "approvals"

    id          = Column(String(64), primary_key=True)
    task_id     = Column(String(64), nullable=False)
    status      = Column(String(32), default="pending")  # pending|approved|rejected
    triggers    = Column(JSON)
    decision    = Column(String(32))
    feedback    = Column(Text)
    approved_by = Column(String(256))
    created_at  = Column(DateTime, default=datetime.utcnow)
    decided_at  = Column(DateTime)


class Document(Base):
    __tablename__ = "rag_documents"

    id         = Column(String(64), primary_key=True)
    title      = Column(String(512))
    content    = Column(Text)
    category   = Column(String(64))
    min_role   = Column(String(32), default="analyst")
    indexed_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column("metadata", JSON)
