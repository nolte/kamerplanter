import { describe, it, expect, vi, afterEach } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import type { TFunction } from 'i18next';
import { ApiError } from '@/api/errors';
import { ChatStreamError, streamChatMessage } from '@/api/endpoints/ai';
import {
  consentPurposeOf,
  isConsentRequired,
  resolveAiErrorMessage,
} from '@/components/ai/aiErrorMessage';

// The key is the observable: each branch must pick its own message.
const t = ((key: string) => key) as unknown as TFunction;

function apiError(errorCode: string, statusCode: number, detailCode = ''): ApiError {
  return new ApiError(
    {
      error_id: 'err_1',
      error_code: errorCode,
      message: 'refused',
      details: detailCode ? [{ field: 'ai_budget', reason: 'Daily budget used up.', code: detailCode }] : [],
      timestamp: '',
      path: '',
      method: 'POST',
    },
    statusCode,
  );
}

describe('resolveAiErrorMessage — AI budget (#2110)', () => {
  it('names the account when the personal daily budget is used up', () => {
    expect(resolveAiErrorMessage(apiError('AI_BUDGET_EXCEEDED', 429, 'user_calls'), t, 'fallback')).toBe(
      'ai.errors.budgetUserExceeded',
    );
  });

  it.each(['tenant_calls', 'tenant_tokens'])('names the garden when its %s budget is used up', (scope) => {
    expect(resolveAiErrorMessage(apiError('AI_BUDGET_EXCEEDED', 429, scope), t, 'fallback')).toBe(
      'ai.errors.budgetTenantExceeded',
    );
  });

  it('explains a budget that cannot be checked', () => {
    expect(resolveAiErrorMessage(apiError('AI_BUDGET_UNAVAILABLE', 503), t, 'fallback')).toBe(
      'ai.errors.budgetUnavailable',
    );
  });

  it('explains the per-minute limit, which answers without the error envelope', () => {
    const axios429 = new AxiosError('Too Many Requests', '429', undefined, undefined, {
      status: 429,
      statusText: 'Too Many Requests',
      data: { error: 'Rate limit exceeded: 20 per 1 minute' },
      headers: {},
      config: { headers: new AxiosHeaders() },
    });
    expect(resolveAiErrorMessage(axios429, t, 'fallback')).toBe('ai.errors.tooManyRequests');
    expect(resolveAiErrorMessage(new ChatStreamError(429), t, 'fallback')).toBe('ai.errors.tooManyRequests');
  });

  it('keeps the fallback for everything else', () => {
    expect(resolveAiErrorMessage(new ChatStreamError(502), t, 'fallback')).toBe('fallback');
    expect(resolveAiErrorMessage(new Error('network'), t, 'fallback')).toBe('fallback');
  });
});

describe('streamChatMessage — a refused message (#2110)', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('turns the JSON error envelope into an ApiError the drawer can explain', async () => {
    const envelope = {
      error_id: 'err_9',
      error_code: 'AI_BUDGET_EXCEEDED',
      message: 'used up',
      details: [{ field: 'ai_budget', reason: 'Daily budget used up.', code: 'tenant_calls' }],
      timestamp: '',
      path: '',
      method: 'POST',
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify(envelope), { status: 429 })),
    );

    const failure = await streamChatMessage('conv-1', 'Why?', () => {}).catch((err: unknown) => err);

    expect(failure).toBeInstanceOf(ApiError);
    expect(resolveAiErrorMessage(failure, t, 'fallback')).toBe('ai.errors.budgetTenantExceeded');
  });

  it('keeps the status of a refusal without an envelope', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Rate limit exceeded', { status: 429 })));

    const failure = await streamChatMessage('conv-1', 'Why?', () => {}).catch((err: unknown) => err);

    expect(failure).toBeInstanceOf(ChatStreamError);
    expect((failure as ChatStreamError).statusCode).toBe(429);
  });
});

describe('consentPurposeOf — the purpose a CONSENT_REQUIRED refusal names (#2175)', () => {
  function consentError(message: string, purpose?: string | null): ApiError {
    return new ApiError(
      {
        error_id: 'e',
        error_code: 'CONSENT_REQUIRED',
        message,
        details:
          purpose === undefined
            ? []
            : [{ field: 'consent', reason: 'Grant consent.', code: 'consent_required', purpose }],
        timestamp: '',
        path: '',
        method: 'POST',
      },
      403,
    );
  }

  it('reads the machine-readable purpose from details[0].purpose first', () => {
    // The message names a different purpose on purpose: only reading `details`
    // first yields the detail's value.
    const error = consentError(
      "Consent for 'ai_tenant_data_access' is required for this action.",
      'ai_knowledge_question',
    );
    expect(consentPurposeOf(error)).toBe('ai_knowledge_question');
  });

  it('reads details[0].purpose even when the message names none', () => {
    expect(consentPurposeOf(consentError('Consent required.', 'ai_cloud_processing'))).toBe(
      'ai_cloud_processing',
    );
  });

  it.each([null, ''])('falls back to the message when details[0].purpose is %j', (purpose) => {
    const error = consentError("Consent for 'ai_knowledge_question' is required.", purpose);
    expect(consentPurposeOf(error)).toBe('ai_knowledge_question');
  });

  it("falls back to the message for an older server's envelope without the field", () => {
    const error = consentError("Consent for 'ai_knowledge_question' is required for this action.");
    expect(isConsentRequired(error)).toBe(true);
    expect(consentPurposeOf(error)).toBe('ai_knowledge_question');
  });

  it('answers null when the message names no purpose', () => {
    expect(consentPurposeOf(consentError('Consent required.'))).toBeNull();
  });

  it('answers null for any other refusal', () => {
    const error = apiError('AI_DISABLED_FOR_TENANT', 403);
    expect(isConsentRequired(error)).toBe(false);
    expect(consentPurposeOf(error)).toBeNull();
    expect(consentPurposeOf(new Error("Consent for 'x' is required"))).toBeNull();
  });
});
