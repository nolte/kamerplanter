import { describe, it, expect, vi, afterEach } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import type { TFunction } from 'i18next';
import { ApiError } from '@/api/errors';
import { ChatStreamError, streamChatMessage } from '@/api/endpoints/ai';
import { resolveAiErrorMessage } from '@/components/ai/aiErrorMessage';

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
