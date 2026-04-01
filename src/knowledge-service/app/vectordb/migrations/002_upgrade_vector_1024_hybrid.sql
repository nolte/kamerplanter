-- Migration 002: Upgrade to 768-dim embeddings (multilingual-e5-base) + hybrid search
--
-- Changes:
--   1. Resize embedding column from vector(384) to vector(768)
--   2. Replace IVFFlat index with HNSW (better for higher dimensions)
--   3. Add search_text tsvector column for BM25 full-text search
--   4. Create GIN index on search_text
--   5. Populate search_text from existing data
--
-- IMPORTANT: After running this migration, ALL existing embeddings must be
-- re-generated with the new model. Run the knowledge ingest endpoint:
--   POST /api/v1/knowledge/ingest

-- Step 1: Drop old index, truncate stale 384-dim data, resize to 768 dimensions
DROP INDEX IF EXISTS idx_ai_chunks_embedding;
TRUNCATE TABLE ai_vector_chunks;
ALTER TABLE ai_vector_chunks ALTER COLUMN embedding TYPE vector(768);

-- Step 2: Create HNSW index (better for higher dimensions)

CREATE INDEX IF NOT EXISTS idx_ai_chunks_embedding
    ON ai_vector_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Step 3: Add search_text column for full-text search (BM25)
ALTER TABLE ai_vector_chunks ADD COLUMN IF NOT EXISTS search_text tsvector;

-- Step 4: Create GIN index on search_text
CREATE INDEX IF NOT EXISTS idx_ai_chunks_search_text
    ON ai_vector_chunks USING gin(search_text);

-- Step 5: Populate search_text from existing title + content
-- Note: Full umlaut/digraph dual-indexing happens at upsert time in the repository.
-- This migration only does a basic populate; the reindex task will rebuild properly.
UPDATE ai_vector_chunks
SET search_text = to_tsvector('german', title || ' ' || content);
