import { useCallback, useEffect, useMemo, useState } from 'react';
import { glossaryApi } from '@/api';
import type { GlossaryExpertiseLevel, GlossaryTermAnswer } from '@/api/types';

/**
 * REQ-035 §5.1 — client-side cache for glossary answers.
 *
 * Glossary answers are quasi-static (the backend caches them 7 days), so a
 * module-level cache keyed by `slug:language:expertise` avoids re-fetching the
 * same term while navigating the tooltip stack or reopening a popover. The TTL
 * mirrors the backend (7 days).
 */
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

interface CacheEntry {
  answer: GlossaryTermAnswer;
  fetchedAt: number;
}

const answerCache = new Map<string, CacheEntry>();

function cacheKey(slug: string, language: string, expertise: GlossaryExpertiseLevel): string {
  return `${slug}:${language}:${expertise}`;
}

/** Exposed for tests — clears the module-level answer cache. */
export function clearGlossaryCache(): void {
  answerCache.clear();
}

export interface UseGlossaryTermResult {
  answer: GlossaryTermAnswer | null;
  loading: boolean;
  error: boolean;
  reload: () => void;
  /**
   * Ask the backend to produce the detailed explanation (#1460).
   *
   * Reading no longer generates, so a term whose answer arrives with
   * `is_fallback: true` stays on the curated short definition until somebody
   * with the grower role asks for this. Resolves once the answer (generated or
   * refused) has been applied.
   */
  generate: () => Promise<void>;
  generating: boolean;
}

/**
 * Fetch (and cache) one glossary term explanation. Returns a stable object
 * (useMemo) so consumers can safely spread it into effect deps.
 *
 * @param slug        Canonical or alias slug; `null` disables fetching.
 * @param language    Answer language (`de`/`en`).
 * @param expertise   Experience level driving the RAG prompt variant.
 */
export function useGlossaryTerm(
  slug: string | null,
  language: 'de' | 'en',
  expertise: GlossaryExpertiseLevel,
): UseGlossaryTermResult {
  const [answer, setAnswer] = useState<GlossaryTermAnswer | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<boolean>(false);
  const [reloadToken, setReloadToken] = useState<number>(0);
  const [generating, setGenerating] = useState<boolean>(false);

  const reload = useCallback(() => {
    if (slug) answerCache.delete(cacheKey(slug, language, expertise));
    setReloadToken((token) => token + 1);
  }, [slug, language, expertise]);

  const generate = useCallback(async () => {
    if (!slug) return;
    setGenerating(true);
    try {
      const result = await glossaryApi.generateTerm(slug, expertise, language);
      answerCache.set(cacheKey(slug, language, expertise), {
        answer: result,
        fetchedAt: Date.now(),
      });
      setAnswer(result);
    } catch {
      // The read surface stays: the caller already has the curated short
      // definition, and clearing it would turn a refused generation into the
      // loss of the answer too.
    } finally {
      setGenerating(false);
    }
  }, [slug, language, expertise]);

  useEffect(() => {
    if (!slug) {
      setAnswer(null);
      setLoading(false);
      setError(false);
      return;
    }

    const key = cacheKey(slug, language, expertise);
    const cached = answerCache.get(key);
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
      setAnswer(cached.answer);
      setLoading(false);
      setError(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(false);
    glossaryApi
      .getTerm(slug, expertise, language)
      .then((result) => {
        if (cancelled) return;
        answerCache.set(key, { answer: result, fetchedAt: Date.now() });
        setAnswer(result);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [slug, language, expertise, reloadToken]);

  return useMemo(
    () => ({ answer, loading, error, reload, generate, generating }),
    [answer, loading, error, reload, generate, generating],
  );
}
