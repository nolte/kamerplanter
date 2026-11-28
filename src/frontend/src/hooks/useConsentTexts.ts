import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LOCALES, loadFeatureNamespaces, type SupportedLocale } from '@/i18n/i18n';

/** The texts a consent decision is made to (UI-NFR-013 CB-007, CB-008, CK-004). */
const CONSENT_TEXT_KEYS = [
  'consent.banner.intro',
  'consent.banner.summary',
  'consent.banner.accept_all',
  'consent.banner.necessary',
  'consent.banner.confirm_body',
  'consent.banner.category.browser_error_reports.description',
] as const;

/** A failed load of the text bundle is retried this often while the component is mounted. */
export const CONSENT_TEXT_RETRY_MS = 15_000;

function localeOf(language: string | undefined): SupportedLocale {
  const base = (language ?? 'de').split('-')[0];
  return (SUPPORTED_LOCALES as readonly string[]).includes(base!)
    ? (base as SupportedLocale)
    : 'de';
}

/**
 * Whether the consent texts are loaded (UI-NFR-013 v1.4 CB-007).
 *
 * They live in the lazily loaded `pages` namespace; if that chunk failed to
 * load, the banner would show raw keys and still take a decision — a consent to
 * a text nobody saw. Until the texts are there, callers render no decision
 * controls. Meanwhile the bundle is loaded again (retry every
 * {@link CONSENT_TEXT_RETRY_MS}), and the component re-renders as soon as a
 * bundle arrives (`added` on the resource store).
 */
export function useConsentTexts(): boolean {
  const { i18n } = useTranslation();
  const [, setRevision] = useState(0);
  const ready = CONSENT_TEXT_KEYS.every((key) => i18n.exists(key));

  useEffect(() => {
    if (ready) return undefined;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const rerender = () => {
      if (!cancelled) setRevision((n) => n + 1);
    };
    const attempt = () => {
      loadFeatureNamespaces(localeOf(i18n.resolvedLanguage ?? i18n.language))
        .then(rerender)
        .catch((error: unknown) => {
          // Not swallowed: the controls stay hidden and the load is tried again.
          console.warn('[consent] consent texts failed to load, retrying', error);
          if (!cancelled) timer = setTimeout(attempt, CONSENT_TEXT_RETRY_MS);
        });
    };
    i18n.store.on('added', rerender);
    attempt();
    return () => {
      cancelled = true;
      if (timer !== undefined) clearTimeout(timer);
      i18n.store.off('added', rerender);
    };
  }, [ready, i18n]);

  return ready;
}
