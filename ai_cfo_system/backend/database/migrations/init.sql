-- AI CFO System — PostgreSQL + pgvector schema
-- Run once to initialize production database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id                  VARCHAR(64) PRIMARY KEY,
    task_type           VARCHAR(64) NOT NULL,
    description         TEXT,
    company_name        VARCHAR(256),
    period              VARCHAR(64),
    report_format       VARCHAR(64) DEFAULT 'board',
    submitted_by        VARCHAR(256),
    submitted_at        TIMESTAMP DEFAULT NOW(),
    status              VARCHAR(32) DEFAULT 'pending',
    kpi_metrics         JSONB,
    variance_table      JSONB,
    gaap_results        JSONB,
    ifrs_results        JSONB,
    analysis_narrative  TEXT,
    final_report        TEXT,
    audit_log           JSONB,
    errors              JSONB,
    total_tokens_used   INTEGER DEFAULT 0,
    total_cost_usd      FLOAT DEFAULT 0,
    processing_time_ms  INTEGER DEFAULT 0,
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
    id          VARCHAR(64) PRIMARY KEY,
    task_id     VARCHAR(64) NOT NULL REFERENCES tasks(id),
    status      VARCHAR(32) DEFAULT 'pending',
    triggers    JSONB,
    decision    VARCHAR(32),
    feedback    TEXT,
    approved_by VARCHAR(256),
    created_at  TIMESTAMP DEFAULT NOW(),
    decided_at  TIMESTAMP
);

-- RAG documents with pgvector embedding (384-dim for all-MiniLM-L6-v2)
CREATE TABLE IF NOT EXISTS cfo_documents (
    id          VARCHAR(64) PRIMARY KEY,
    title       VARCHAR(512),
    content     TEXT,
    embedding   vector(384),
    category    VARCHAR(64),
    min_role    VARCHAR(32) DEFAULT 'analyst',
    indexed_at  TIMESTAMP DEFAULT NOW(),
    metadata    JSONB
);

-- Cosine similarity index for fast ANN search
CREATE INDEX IF NOT EXISTS cfo_documents_embedding_idx
    ON cfo_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Indexes
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks(status);
CREATE INDEX IF NOT EXISTS approvals_task_idx ON approvals(task_id);
CREATE INDEX IF NOT EXISTS approvals_status_idx ON approvals(status);
CREATE INDEX IF NOT EXISTS cfo_documents_category_idx ON cfo_documents(category);
