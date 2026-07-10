-- Migration 004: user-contribution provenance (SEC-001/SEC-005, issue #447)
--
-- Interactive user reference contributions (POST /identification/reference,
-- source = 'user_contributed') must be attributable so the GDPR erasure
-- pipeline (REQ-025 Phase 0.5) can remove a single user's / tenant's vectors
-- without touching curated references, and so the platform-admin curation view
-- knows who supplied a pending row.
--
-- These columns are NULL for the license-clean acquisition pipeline (GBIF /
-- Wikimedia) rows — they only carry a value for user contributions.

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS contributed_by TEXT;

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS tenant_key TEXT;

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS contributed_at TIMESTAMPTZ;

-- Erasure targets a user's contributions by (contributed_by[, tenant_key]);
-- index just the contributed rows so the scan stays cheap.
CREATE INDEX IF NOT EXISTS idx_species_emb_contributed_by
    ON species_embeddings (contributed_by)
    WHERE contributed_by IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_species_emb_tenant_key
    ON species_embeddings (tenant_key)
    WHERE tenant_key IS NOT NULL;
