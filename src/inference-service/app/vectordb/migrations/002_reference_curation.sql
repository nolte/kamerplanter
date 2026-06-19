-- Migration 002: reference-image curation flags (manual exclusion / REQ-029-A)
--
-- Adds a soft-delete quality flag so a platform admin can deselect a reference
-- image that fails the visual test. Excluded rows are KEPT for the audit trail
-- and stay reactivatable, but are filtered out of /match (WHERE is_active) so a
-- bad image can no longer skew recognition results.

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS exclusion_reason TEXT;

ALTER TABLE species_embeddings
    ADD COLUMN IF NOT EXISTS marked_at TIMESTAMPTZ;

-- Partial index: /match only ever scans active rows, so index just those.
CREATE INDEX IF NOT EXISTS idx_species_emb_active
    ON species_embeddings (species_key)
    WHERE is_active;
