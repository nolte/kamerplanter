-- Migration 003: Add language and ts_config columns for multilingual RAG support
--
-- Enables per-chunk language tagging and language-specific full-text stemming.
-- Existing rows default to German ('de' / 'german').

ALTER TABLE ai_vector_chunks ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT 'de';
ALTER TABLE ai_vector_chunks ADD COLUMN IF NOT EXISTS ts_config TEXT NOT NULL DEFAULT 'german';

CREATE INDEX IF NOT EXISTS idx_ai_chunks_language ON ai_vector_chunks (language);
