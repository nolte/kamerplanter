CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pest_embeddings (
    id               SERIAL PRIMARY KEY,
    label            TEXT        NOT NULL,
    category         TEXT        NOT NULL,
    embedding        vector(384) NOT NULL,
    model            TEXT        NOT NULL DEFAULT 'dinov2_vits14',
    source           TEXT        NOT NULL,
    source_record_id TEXT,
    license          TEXT,
    attribution      TEXT,
    source_url       TEXT,
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    indexed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (label, source, source_record_id)
);

CREATE INDEX IF NOT EXISTS idx_pest_emb_label
    ON pest_embeddings (label);

CREATE INDEX IF NOT EXISTS idx_pest_emb_model
    ON pest_embeddings (model);

CREATE INDEX IF NOT EXISTS idx_pest_emb_embedding
    ON pest_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_pest_emb_active
    ON pest_embeddings (label)
    WHERE is_active;
