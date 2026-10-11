import { describe, it, expect, beforeAll } from 'vitest';
import i18n from 'i18next';
import '@/i18n';
import { ApiError } from '@/api/errors';
import type { EntitlementUsage } from '@/api/types';
import {
  formatPlanLimit,
  formatUsage,
  minimumLimit,
  quotaErrorKey,
  quotaErrorKeyForCode,
  usageColor,
  usagePercent,
} from '@/utils/entitlements';

/**
 * REQ-056 §7.2 / §7.7 (AK-45) — the two `null`s and the one `0` the quota views must not confuse:
 * `null` in a plan = the instance setting, `null` in an effective limit = unlimited, and `0` lifts
 * the limit (unlimited / budget off) — it is never rendered as "0" or "nothing allowed".
 */

const t = i18n.t.bind(i18n);

function apiError(code: string, status = 422): ApiError {
  return new ApiError(
    { error_id: 'e', error_code: code, message: 'English message', details: [], timestamp: '', path: '/', method: 'POST' },
    status,
  );
}

describe('formatPlanLimit', () => {
  beforeAll(async () => {
    await i18n.changeLanguage('de');
  });

  it('reads null and an absent value as the instance setting', () => {
    expect(formatPlanLimit('members', null, t)).toBe('wie Instanz-Einstellung');
    expect(formatPlanLimit('storage_mb', undefined, t)).toBe('wie Instanz-Einstellung');
  });

  it('reads 0 as unlimited for storage and photos, never as the number 0', () => {
    expect(formatPlanLimit('storage_mb', 0, t)).toBe('unbegrenzt');
    expect(formatPlanLimit('photos_per_instance', 0, t)).toBe('unbegrenzt');
  });

  it('reads 0 as budget off for every AI budget', () => {
    for (const d of ['ai_calls_per_user_day', 'ai_calls_per_tenant_day', 'ai_tokens_per_tenant_day'] as const) {
      expect(formatPlanLimit(d, 0, t)).toBe('Budget aus (unbegrenzt)');
    }
  });

  it('renders a number with its unit', () => {
    expect(formatPlanLimit('storage_mb', 5120, t)).toBe('5.120 MB');
    expect(formatPlanLimit('members', 30, t)).toBe('30 Mitglieder');
  });
});

describe('minimumLimit', () => {
  it('requires at least 1 for members and service accounts, 0 elsewhere', () => {
    expect(minimumLimit('members')).toBe(1);
    expect(minimumLimit('service_accounts')).toBe(1);
    expect(minimumLimit('storage_mb')).toBe(0);
    expect(minimumLimit('ai_tokens_per_tenant_day')).toBe(0);
  });
});

describe('usage of an effective limit', () => {
  beforeAll(async () => {
    await i18n.changeLanguage('de');
  });

  const row = (over: Partial<EntitlementUsage>): EntitlementUsage => ({
    dimension: 'members',
    limit: 50,
    used: 12,
    ...over,
  });

  it('measures a percentage only when both sides are known', () => {
    expect(usagePercent(row({}))).toBe(24);
    expect(usagePercent(row({ limit: null }))).toBeNull();
    expect(usagePercent(row({ used: null }))).toBeNull();
    expect(usagePercent(row({ used: 80, limit: 50 }))).toBe(100);
  });

  it('colours by how close the limit is', () => {
    expect(usageColor(24)).toBe('primary');
    expect(usageColor(80)).toBe('warning');
    expect(usageColor(100)).toBe('error');
  });

  it('spells out used of limit, unlimited and the per-plant count', () => {
    expect(formatUsage(row({}), t)).toBe('12 von 50 Mitglieder');
    expect(formatUsage(row({ dimension: 'storage_mb', limit: null, used: 731 }), t)).toBe('731 MB – unbegrenzt');
    expect(formatUsage(row({ dimension: 'photos_per_instance', limit: 50, used: null }), t)).toBe(
      'je Pflanze gezählt – höchstens 50 Fotos',
    );
    expect(formatUsage(row({ dimension: 'ai_calls_per_tenant_day', limit: 500, used: null }), t)).toBe(
      'Verbrauch gerade nicht lesbar – Grenze 500 Aufrufe',
    );
  });
});

describe('quotaErrorKey', () => {
  it('maps every quota refusal of REQ-056 §6.2/§7.2 to its own translation', () => {
    expect(quotaErrorKey(apiError('ORGANIZATION_LIMIT_REACHED'))).toBe('errors.quota.organizationLimitReached');
    expect(quotaErrorKey(apiError('MEMBER_LIMIT_REACHED'))).toBe('errors.quota.memberLimitReached');
    expect(quotaErrorKey(apiError('SERVICE_ACCOUNT_LIMIT_REACHED'))).toBe('errors.quota.serviceAccountLimitReached');
    expect(quotaErrorKey(apiError('STORAGE_QUOTA_EXCEEDED', 409))).toBe('errors.quota.storageQuotaExceeded');
    expect(quotaErrorKey(apiError('PHOTO_QUOTA_EXCEEDED', 409))).toBe('errors.quota.photoQuotaExceeded');
  });

  it('leaves every other error to the generic handling', () => {
    expect(quotaErrorKey(apiError('VALIDATION_ERROR'))).toBeNull();
    expect(quotaErrorKey(new Error('boom'))).toBeNull();
    expect(quotaErrorKeyForCode(null)).toBeNull();
  });

  it('has a German and an English text for every key', async () => {
    for (const lng of ['de', 'en']) {
      await i18n.changeLanguage(lng);
      for (const code of [
        'ORGANIZATION_LIMIT_REACHED',
        'MEMBER_LIMIT_REACHED',
        'SERVICE_ACCOUNT_LIMIT_REACHED',
        'STORAGE_QUOTA_EXCEEDED',
        'PHOTO_QUOTA_EXCEEDED',
      ]) {
        const key = quotaErrorKeyForCode(code)!;
        expect(i18n.exists(key), `${lng}:${key}`).toBe(true);
      }
    }
    await i18n.changeLanguage('de');
  });
});
