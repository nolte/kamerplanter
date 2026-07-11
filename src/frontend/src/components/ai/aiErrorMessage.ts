import type { TFunction } from 'i18next';
import { isApiError } from '@/api/errors';

/**
 * REQ-031 §1.3/§7.1 — maps the two stable backend error codes for the
 * three-stage KI feature toggle to a user-facing explanation.
 *
 * Stage 2 (`AI_DISABLED_FOR_TENANT`, `FeatureGuard`) and stage 3
 * (`CONSENT_REQUIRED`, `ConsentGuard`) both respond with HTTP 403 and a
 * stable `error_code`. Without this mapping every KI call surface (chat,
 * "why?", tips) would show a generic, unhelpful "answer could not be
 * loaded" message even when the real cause is a disabled feature or a
 * missing consent — a dead end for the user. Falls back to `fallback` for
 * every other error (network failure, 5xx, stage-1 operator-off 404).
 */
export function resolveAiErrorMessage(error: unknown, t: TFunction, fallback: string): string {
  if (isApiError(error)) {
    if (error.errorCode === 'AI_DISABLED_FOR_TENANT') {
      return t('ai.errors.disabled');
    }
    if (error.errorCode === 'CONSENT_REQUIRED') {
      return t('ai.errors.consentRequired');
    }
  }
  return fallback;
}
