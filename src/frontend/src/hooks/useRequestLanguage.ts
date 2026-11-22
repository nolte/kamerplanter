import { useTranslation } from 'react-i18next';
import { normalizeNameLanguage } from '@/utils/plantDisplay';

/**
 * The UI language the API client sends as `Accept-Language` (`api/client.ts`), normalized
 * to its primary subtag (`de`, `en`).
 *
 * The server words some answers in this language — the species names of the care dashboard,
 * the dashboard plant grid, the sowing calendar, the bed plan's plant states, the succession
 * recommendation, the winter-hardiness overview, the workflow lists and the diary overview
 * (#2902). A component that keeps such an answer lists this value as a dependency of the
 * effect that loads it, so a language switch loads the answer again instead of showing the
 * names of the previous language; a cache that stores such an answer keys it by this value.
 *
 * `useTranslation` re-renders on `languageChanged`, so the value follows a switch.
 */
export function useRequestLanguage(): string {
  const { i18n } = useTranslation();
  return normalizeNameLanguage(i18n.resolvedLanguage || i18n.language);
}
