CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE ai_vector_chunks (
    id          SERIAL PRIMARY KEY,
    source_key  TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    embedding   vector(384) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_chunks_source_type
    ON ai_vector_chunks (source_type);

CREATE INDEX idx_ai_chunks_embedding
    ON ai_vector_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10)
