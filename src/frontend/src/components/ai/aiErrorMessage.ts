import axios from 'axios';
import type { TFunction } from 'i18next';
import { isApiError } from '@/api/errors';
import { ChatStreamError } from '@/api/endpoints/ai';

/**
 * REQ-031 §1.3/§7.1 — maps the stable backend error codes of a KI call to a
 * user-facing explanation.
 *
 * Stage 2 (`AI_DISABLED_FOR_TENANT`, `FeatureGuard`) and stage 3
 * (`CONSENT_REQUIRED`, `ConsentGuard`) both respond with HTTP 403 and a
 * stable `error_code`. Without this mapping every KI call surface (chat,
 * "why?", tips) would show a generic, unhelpful "answer could not be
 * loaded" message even when the real cause is a disabled feature or a
 * missing consent — a dead end for the user.
 *
 * REQ-031 §3 (#2110) — the daily AI budget answers `429 AI_BUDGET_EXCEEDED`
 * (`details[0].code` says whether the account's or the garden's budget is
 * used up) and `503 AI_BUDGET_UNAVAILABLE` when it cannot be checked; the
 * per-minute limit answers a plain `429` without the envelope.
 *
 * Falls back to `fallback` for every other error (network failure, 5xx,
 * stage-1 operator-off 404).
 */
export function resolveAiErrorMessage(error: unknown, t: TFunction, fallback: string): string {
  if (isApiError(error)) {
    if (error.errorCode === 'AI_DISABLED_FOR_TENANT') {
      return t('ai.errors.disabled');
    }
    if (error.errorCode === 'CONSENT_REQUIRED') {
      return t('ai.errors.consentRequired');
    }
    if (error.errorCode === 'AI_BUDGET_EXCEEDED') {
      return error.details[0]?.code === 'user_calls'
        ? t('ai.errors.budgetUserExceeded')
        : t('ai.errors.budgetTenantExceeded');
    }
    if (error.errorCode === 'AI_BUDGET_UNAVAILABLE') {
      return t('ai.errors.budgetUnavailable');
    }
  }
  if (statusOf(error) === 429) {
    return t('ai.errors.tooManyRequests');
  }
  return fallback;
}

/**
 * Whether the error is the stage-3 refusal `403 CONSENT_REQUIRED`.
 */
export function isConsentRequired(error: unknown): boolean {
  return isApiError(error) && error.errorCode === 'CONSENT_REQUIRED';
}

const CONSENT_PURPOSE_IN_MESSAGE = /'([a-z][a-z0-9_]*)'/;

/**
 * The consent purpose a `CONSENT_REQUIRED` refusal names, or `null`.
 *
 * The backend names it machine-readably in `details[0].purpose`
 * (`ConsentRequiredError`); that is read first. Older servers carried it only in
 * the English message (`Consent for '<purpose>' is required for this action.`),
 * so the message is parsed as a fallback. `null` means "the refusal does not
 * say" — the caller decides what that defaults to.
 */
export function consentPurposeOf(error: unknown): string | null {
  if (!isApiError(error) || error.errorCode !== 'CONSENT_REQUIRED') return null;
  const named = error.details[0]?.purpose;
  if (typeof named === 'string' && named.trim() !== '') return named;
  const match = CONSENT_PURPOSE_IN_MESSAGE.exec(error.message);
  return match ? match[1] : null;
}

/**
 * Why an AI call cannot work here at all, or `null` when it might on a retry.
 *
 * `'tenant'` — stage 2: the garden has AI switched off (`403 AI_DISABLED_FOR_TENANT`).
 * `'instance'` — stage 1: the operator flag is off, so the AI route answers a
 * bare `404` (§1.3, "as if it did not exist").
 *
 * Neither is fixed by trying again, so a caller hides its trigger instead of
 * offering a retry that is refused the same way.
 */
export type AiUnavailableReason = 'tenant' | 'instance';

export function aiUnavailableReason(error: unknown): AiUnavailableReason | null {
  if (isApiError(error) && error.errorCode === 'AI_DISABLED_FOR_TENANT') return 'tenant';
  if (statusOf(error) === 404) return 'instance';
  return null;
}

/** The user-facing sentence for an {@link AiUnavailableReason}. */
export function aiUnavailableMessage(reason: AiUnavailableReason, t: TFunction): string {
  return reason === 'tenant' ? t('ai.errors.disabled') : t('ai.errors.notEnabled');
}

function statusOf(error: unknown): number | undefined {
  if (isApiError(error)) return error.statusCode;
  if (error instanceof ChatStreamError) return error.statusCode;
  if (axios.isAxiosError(error)) return error.response?.status;
  return undefined;
}
