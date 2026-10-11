import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { TenantEntitlements } from '@/api/types';

vi.mock('@/api/endpoints/tenants', () => ({
  getTenantEntitlements: vi.fn(),
}));

const api = await import('@/api/endpoints/tenants');
const { useTenantEntitlements } = await import('@/hooks/useTenantEntitlements');
const getEntitlements = api.getTenantEntitlements as ReturnType<typeof vi.fn>;

const ANSWER: TenantEntitlements = {
  plan: { key: 'standard', name: 'Standard' },
  limits: [{ dimension: 'members', limit: 50, used: 12 }],
};

describe('useTenantEntitlements (REQ-056 §7.7)', () => {
  beforeEach(() => {
    getEntitlements.mockReset();
  });

  it('is idle without a garden and asks nothing', () => {
    const { result } = renderHook(() => useTenantEntitlements(null));
    expect(result.current.status).toBe('idle');
    expect(getEntitlements).not.toHaveBeenCalled();
  });

  it('loads the garden by its slug and keeps a stable object between renders', async () => {
    getEntitlements.mockResolvedValue(ANSWER);
    const { result, rerender } = renderHook(() => useTenantEntitlements('mein-garten'));
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(getEntitlements).toHaveBeenCalledWith('mein-garten');
    expect(result.current.entitlements).toEqual(ANSWER);
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });

  it('never shows the answer of one garden for another', async () => {
    getEntitlements.mockResolvedValueOnce(ANSWER);
    const { result, rerender } = renderHook(({ slug }) => useTenantEntitlements(slug), {
      initialProps: { slug: 'garten-a' },
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    getEntitlements.mockReturnValueOnce(new Promise(() => {}));
    rerender({ slug: 'garten-b' });
    expect(result.current.status).toBe('loading');
    expect(result.current.entitlements).toBeNull();
  });

  it('turns a failed read into an error with a retry', async () => {
    getEntitlements.mockRejectedValueOnce(new Error('offline'));
    const { result } = renderHook(() => useTenantEntitlements('mein-garten'));
    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.errorStatus).toBe(0);

    getEntitlements.mockResolvedValueOnce(ANSWER);
    act(() => result.current.reload());
    await waitFor(() => expect(result.current.status).toBe('ready'));
  });
});
