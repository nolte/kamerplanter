-- Migration 004: Upgrade to 1024-dim embeddings (multilingual-e5-large)
--
-- Changes:
--   1. Resize embedding column from vector(768) to vector(1024)
--   2. Recreate HNSW index for 1024 dimensions
--
-- IMPORTANT: After running this migration, ALL existing embeddings must be
-- re-generated with the new model. Run the knowledge ingest endpoint:
--   POST /ingest

-- Step 1: Drop old index, truncate stale 768-dim data, resize to 1024 dimensions
DROP INDEX IF EXISTS idx_ai_chunks_embedding_hnsw;
TRUNCATE TABLE ai_vector_chunks;
ALTER TABLE ai_vector_chunks ALTER COLUMN embedding TYPE vector(1024);

-- Step 2: Recreate HNSW index for 1024 dimensions
CREATE INDEX idx_ai_chunks_embedding_hnsw
    ON ai_vector_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);
