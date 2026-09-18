import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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

/**
 * What the generation attempt is doing right now.
 *
 * A tri-state rather than two booleans (review SCR-001): `failed` and `idle`
 * must be distinguishable, because the first version collapsed them — a 403, a
 * 429 or a 502 all ended in an empty `catch {}` and the user saw a button that
 * did nothing at all.
 */
export type GlossaryGenerateStatus = 'idle' | 'generating' | 'failed';

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
   * refused) has been applied; the outcome is in `generateStatus`.
   */
  generate: () => Promise<void>;
  generateStatus: GlossaryGenerateStatus;
  /** The raw failure, for `resolveAiErrorMessage` to turn into a sentence. */
  generateError: unknown;
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
  // Which term/language/level the hook is currently showing. Read by `generate`
  // after its await to decide whether its answer is still wanted (SCR-005).
  const cacheKeyRef = useRef<string | null>(null);
  cacheKeyRef.current = slug ? cacheKey(slug, language, expertise) : null;
  const [answer, setAnswer] = useState<GlossaryTermAnswer | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<boolean>(false);
  const [reloadToken, setReloadToken] = useState<number>(0);
  const [generateStatus, setGenerateStatus] = useState<GlossaryGenerateStatus>('idle');
  const [generateError, setGenerateError] = useState<unknown>(null);

  const reload = useCallback(() => {
    if (slug) answerCache.delete(cacheKey(slug, language, expertise));
    setReloadToken((token) => token + 1);
  }, [slug, language, expertise]);

  const generate = useCallback(async () => {
    if (!slug) return;
    // The key is captured BEFORE the await (review SCR-005). A related-term chip
    // switches `slug` while the request is in flight, and applying the answer to
    // whatever term is open by then would show one term's explanation under
    // another's heading.
    const key = cacheKey(slug, language, expertise);
    setGenerateStatus('generating');
    setGenerateError(null);
    try {
      const result = await glossaryApi.generateTerm(slug, expertise, language);
      answerCache.set(key, { answer: result, fetchedAt: Date.now() });
      if (key !== cacheKeyRef.current) return;
      setAnswer(result);
      setGenerateStatus('idle');
    } catch (err) {
      // The read surface stays: the caller already has the curated short
      // definition, and clearing it would turn a refused generation into the
      // loss of the answer too. But the failure is reported — a 403 (viewer, KI
      // disabled, missing consent), a 429 or a 502 used to end here silently and
      // the user saw a button that did nothing.
      if (key !== cacheKeyRef.current) return;
      setGenerateError(err);
      setGenerateStatus('failed');
    }
  }, [slug, language, expertise]);

  useEffect(() => {
    if (!slug) {
      setAnswer(null);
      setLoading(false);
      setError(false);
      setGenerateStatus('idle');
      setGenerateError(null);
      return;
    }

    setGenerateStatus('idle');
    setGenerateError(null);

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
    () => ({
      answer,
      loading,
      error,
      reload,
      generate,
      generateStatus,
      generateError,
      generating: generateStatus === 'generating',
    }),
    [answer, loading, error, reload, generate, generateStatus, generateError],
  );
}
