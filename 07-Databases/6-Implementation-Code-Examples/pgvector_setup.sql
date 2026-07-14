-- ============================================================================
-- pgvector_setup.sql
-- Schema for a production-minded RAG store using PostgreSQL + pgvector.
--
-- WHY this file exists:
--   Keeping embeddings in Postgres (instead of a separate vector service) means
--   a JOIN stays a JOIN and a transaction stays a transaction -- your embeddings
--   live next to the relational data (tenants, documents, metadata) they relate
--   to. This is the "boring, robust" default for < ~10M vectors.
--
-- Run once against your database:  psql "$DATABASE_URL" -f pgvector_setup.sql
-- ============================================================================

-- The extension ships the `vector` type plus the ANN index access methods
-- (hnsw, ivfflat). CREATE EXTENSION is idempotent with IF NOT EXISTS.
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Documents table.
-- WHY tenant_id: multi-tenant isolation. We filter on it in every query and
-- (at scale) can partition by it, so hot tenants don't blow the RAM budget.
-- WHY VECTOR(1536): must match your embedding model's output dimension exactly
-- (1536 = OpenAI text-embedding-3-small). Change this to match your model.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   BIGINT      NOT NULL,
    source      TEXT,                        -- e.g. filename / URL for citations
    chunk_index INT         NOT NULL DEFAULT 0,
    content     TEXT        NOT NULL,        -- the chunk text we return to the LLM
    embedding   VECTOR(1536) NOT NULL,       -- the semantic fingerprint of `content`
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- HNSW index for approximate nearest-neighbor search.
-- WHY HNSW over IVFFlat: higher recall at low latency and no "training" step;
--   it's the 2025-2026 default for production RAG.
-- WHY vector_cosine_ops: we normalize embeddings and compare by cosine distance
--   (the `<=>` operator). Use vector_l2_ops for Euclidean, vector_ip_ops for dot.
-- Build-time knobs:
--   m               = graph connectivity (higher = better recall, more memory)
--   ef_construction = build-time search width (higher = better graph, slower build)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- WHY this b-tree: metadata pre-filtering. pgvector 0.8+ "iterative index scans"
-- keep recall healthy even when a restrictive WHERE (tenant_id) is combined with
-- the ANN search, but a supporting index on the filter column still helps.
CREATE INDEX IF NOT EXISTS idx_documents_tenant
    ON documents (tenant_id);

-- ---------------------------------------------------------------------------
-- Query-time recall/latency knob (session-level).
--   hnsw.ef_search: higher = better recall, higher latency. Tune per SLA.
-- Set it per session/connection right before your similarity queries.
-- ---------------------------------------------------------------------------
-- Example (uncomment to try): SET hnsw.ef_search = 100;

-- ---------------------------------------------------------------------------
-- Example hybrid query: structured filter + vector similarity in ONE statement.
-- This is the whole point of pgvector -- no network hop to a second system.
-- $1 = the query embedding (a VECTOR(1536) bound as a parameter).
-- ---------------------------------------------------------------------------
-- SELECT id, source, content, 1 - (embedding <=> $1) AS cosine_similarity
-- FROM documents
-- WHERE tenant_id = 7                 -- structured pre-filter
-- ORDER BY embedding <=> $1           -- <=> = cosine distance (nearest first)
-- LIMIT 5;

-- ---------------------------------------------------------------------------
-- Security: row-level security so a tenant can only ever see its own rows,
-- even if application code forgets a WHERE clause. Defense in depth.
-- ---------------------------------------------------------------------------
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON documents;
CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.tenant_id', true)::bigint);
-- The app sets the tenant per connection:  SET app.tenant_id = '7';
