-- Migration 001: species_embeddings reference index (REQ-029-A 5.1)
--
-- Stores ONE row per reference image: the DINOv2 embedding plus full
-- provenance/licence metadata. NO original image is ever persisted (REQ-029-A
-- 4.4 / AE-5) -- only the vector and the attribution needed to honour CC-BY.
--
-- Architecture note (D-2): the reference index lives in pgvector (PostgreSQL),
-- NOT ArangoDB. The inference-service owns this table exclusively.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS species_embeddings (
    id               SERIAL PRIMARY KEY,
    species_key      TEXT        NOT NULL,
    scientific_name  TEXT        NOT NULL,
    organ            TEXT,
    embedding        vector(384) NOT NULL,
    model            TEXT        NOT NULL DEFAULT 'dinov2_vits14',
    source           TEXT        NOT NULL,
    source_record_id TEXT,
    license          TEXT,
    attribution      TEXT,
    source_url       TEXT,
    indexed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (species_key, source, source_record_id)
);

CREATE INDEX IF NOT EXISTS idx_species_emb_species_key
    ON species_embeddings (species_key);

CREATE INDEX IF NOT EXISTS idx_species_emb_model
    ON species_embeddings (model);

-- HNSW with cosine ops -- embeddings are L2-normalised, so cosine distance
-- (<=>) is the correct metric. m/ef_construction tuned for the small index
-- (~210 species x ~20 refs ~= 4200 vectors).
CREATE INDEX IF NOT EXISTS idx_species_emb_embedding
    ON species_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
