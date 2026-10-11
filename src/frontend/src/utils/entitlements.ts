import type { TFunction } from 'i18next';
import { isApiError } from '@/api/errors';
import type { EntitlementDimension, EntitlementUsage } from '@/api/types';
import { formatNumber } from '@/utils/formatting';

/**
 * Presentation rules of the plan catalogue and the quota views (REQ-056 §7, AK-45).
 *
 * Two different `null`s meet here, and the UI has to keep them apart:
 *
 * - In a **plan** (`Plan.limits`), `null` means *the instance setting* — the operator's
 *   environment variable decides, the plan does not.
 * - In an **effective limit** (`EntitlementUsage.limit`), `null` means *unlimited*: the
 *   backend has already resolved plan → instance setting.
 *
 * And one `0` that is not what it looks like: for `storage_mb` / `photos_per_instance`
 * a `0` means **unlimited**, for the three AI budgets **budget off** (also no limit). It
 * never means "nothing allowed" (REQ-056 §7.2, SEC-002) — so it is never rendered as "0".
 */

/** Every dimension in the order the backend lists them (REQ-056 §7.2). */
export const ENTITLEMENT_DIMENSIONS: readonly EntitlementDimension[] = [
  'members',
  'service_accounts',
  'storage_mb',
  'photos_per_instance',
  'ai_calls_per_user_day',
  'ai_calls_per_tenant_day',
  'ai_tokens_per_tenant_day',
];

/** Dimensions whose `0` lifts the limit — unlimited (storage, photos) or budget off (AI). */
export const ZERO_IS_UNLIMITED: ReadonlySet<EntitlementDimension> = new Set([
  'storage_mb',
  'photos_per_instance',
  'ai_calls_per_user_day',
  'ai_calls_per_tenant_day',
  'ai_tokens_per_tenant_day',
]);

/** The AI budgets: `0` is "budget off", not "unlimited storage". */
export const AI_BUDGET_DIMENSIONS: ReadonlySet<EntitlementDimension> = new Set([
  'ai_calls_per_user_day',
  'ai_calls_per_tenant_day',
  'ai_tokens_per_tenant_day',
]);

/** Smallest value a plan may set per dimension (REQ-056 §13.2): members and service accounts start at 1. */
export function minimumLimit(dimension: EntitlementDimension): number {
  return ZERO_IS_UNLIMITED.has(dimension) ? 0 : 1;
}

/** Upper bounds of the backend (`LIMIT_MAXIMA` in `app/domain/models/plan.py`). */
export const LIMIT_MAXIMA: Readonly<Record<EntitlementDimension, number>> = {
  members: 1_000_000,
  service_accounts: 100_000,
  storage_mb: 10_000_000,
  photos_per_instance: 100_000,
  ai_calls_per_user_day: 10_000_000,
  ai_calls_per_tenant_day: 100_000_000,
  ai_tokens_per_tenant_day: 1_000_000_000_000,
};

/**
 * How a plan's own value for one dimension reads: the instance setting, unlimited, budget off,
 * or the number with its unit.
 */
export function formatPlanLimit(
  dimension: EntitlementDimension,
  value: number | null | undefined,
  t: TFunction,
): string {
  if (value === null || value === undefined) return t('pages.plans.value.instanceSetting');
  if (value === 0 && ZERO_IS_UNLIMITED.has(dimension)) {
    return AI_BUDGET_DIMENSIONS.has(dimension) ? t('pages.plans.value.budgetOff') : t('pages.plans.value.unlimited');
  }
  return `${formatNumber(value)} ${t(`pages.plans.unit.${dimension}`)}`;
}

/** The used share of an effective limit in percent (0–100), or `null` when there is nothing to measure. */
export function usagePercent(row: EntitlementUsage): number | null {
  if (row.limit === null || row.used === null || row.limit <= 0) return null;
  return Math.min(100, Math.round((row.used / row.limit) * 100));
}

/** Theme colour for a usage bar: calm below 80 %, a warning from 80 %, an error at the limit. */
export function usageColor(percent: number): 'primary' | 'warning' | 'error' {
  if (percent >= 100) return 'error';
  if (percent >= 80) return 'warning';
  return 'primary';
}

/**
 * The readable usage line of one effective limit: "12 of 50 members", "731 MB used – unlimited",
 * "counted per plant: at most 50 photos", …
 */
export function formatUsage(row: EntitlementUsage, t: TFunction): string {
  const unit = t(`pages.plans.unit.${row.dimension}`);
  if (row.used === null) {
    if (row.dimension === 'photos_per_instance') {
      return row.limit === null
        ? t('pages.plans.usage.perPlantUnlimited')
        : t('pages.plans.usage.perPlant', { limit: formatNumber(row.limit), unit });
    }
    return row.limit === null
      ? t('pages.plans.usage.unreadableUnlimited')
      : t('pages.plans.usage.unreadable', { limit: formatNumber(row.limit), unit });
  }
  if (row.limit === null) {
    return t('pages.plans.usage.usedUnlimited', { used: formatNumber(row.used), unit });
  }
  return t('pages.plans.usage.usedOfLimit', {
    used: formatNumber(row.used),
    limit: formatNumber(row.limit),
    unit,
  });
}

/**
 * The quota refusals of REQ-056 §6.2/§7.2 → i18n key, keyed on the stable `error_code`
 * (the backend message is English, NFR-003). `null` for any other error.
 *
 * Every dimension keeps its own code and status (REQ-056 E-06); `AI_BUDGET_EXCEEDED` is not
 * here because the AI surfaces explain it in more detail themselves (`resolveAiErrorMessage`).
 */
const QUOTA_ERROR_KEYS: Readonly<Record<string, string>> = {
  ORGANIZATION_LIMIT_REACHED: 'errors.quota.organizationLimitReached',
  MEMBER_LIMIT_REACHED: 'errors.quota.memberLimitReached',
  SERVICE_ACCOUNT_LIMIT_REACHED: 'errors.quota.serviceAccountLimitReached',
  STORAGE_QUOTA_EXCEEDED: 'errors.quota.storageQuotaExceeded',
  PHOTO_QUOTA_EXCEEDED: 'errors.quota.photoQuotaExceeded',
};

export function quotaErrorKeyForCode(errorCode: string | null | undefined): string | null {
  if (!errorCode) return null;
  return QUOTA_ERROR_KEYS[errorCode] ?? null;
}

export function quotaErrorKey(error: unknown): string | null {
  if (!isApiError(error)) return null;
  return quotaErrorKeyForCode(error.errorCode);
}
