import { tenantClient } from '../client';
import type {
  GlossaryExpertiseLevel,
  GlossaryTermAnswer,
  GlossaryTermSummary,
} from '../types';

/**
 * REQ-035 KI-Fachbegriff-Glossar API layer.
 *
 * All calls go through the tenant client (`/t/{slug}/glossary/...`); it works in
 * both full and light mode (light mode auto-resolves the `mein-garten` tenant).
 * The endpoints use no tenant data — the Knowledge-Service call runs strictly
 * with `context=null` (§3.1). Frontend caching is handled by the RTK-Query-less
 * in-memory cache in the glossary hook (7-day quasi-static answers).
 */

/** List active glossary terms (slug + localised label + category). */
export async function listTerms(
  category?: string,
  language: 'de' | 'en' = 'de',
): Promise<GlossaryTermSummary[]> {
  const { data } = await tenantClient.get<GlossaryTermSummary[]>('/glossary/terms', {
    params: { category: category ?? undefined, language },
  });
  return data;
}

/**
 * Read the prepared explanation of one term at the requested level (§4.1).
 *
 * A read: since #1460 it never calls the Knowledge Service. When nothing has
 * been prepared for this term/language/level, the answer is the curated
 * editorial short definition with `is_fallback: true` — `generateTerm` is what
 * produces the detailed one.
 */
export async function getTerm(
  slug: string,
  expertise: GlossaryExpertiseLevel = 'beginner',
  language: 'de' | 'en' = 'de',
): Promise<GlossaryTermAnswer> {
  const { data } = await tenantClient.get<GlossaryTermAnswer>(
    `/glossary/term/${encodeURIComponent(slug)}`,
    { params: { expertise, language } },
  );
  return data;
}

/**
 * Ask the Knowledge Service for this term's explanation and cache it (§4.1).
 *
 * Requires the grower role: it spends an LLM call on the installation's behalf.
 * Idempotent while a cached entry is still valid.
 */
export async function generateTerm(
  slug: string,
  expertise: GlossaryExpertiseLevel = 'beginner',
  language: 'de' | 'en' = 'de',
): Promise<GlossaryTermAnswer> {
  const { data } = await tenantClient.post<GlossaryTermAnswer>(
    `/glossary/term/${encodeURIComponent(slug)}/generate`,
    null,
    { params: { expertise, language } },
  );
  return data;
}
