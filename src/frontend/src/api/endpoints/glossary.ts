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

/** Explain one term at the requested experience level (cache-first, §4.1). */
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
