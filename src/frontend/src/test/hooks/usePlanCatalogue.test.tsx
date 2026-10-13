import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { ApiError } from '@/api/errors';
import type { Plan } from '@/api/types';

vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn(),
}));

const api = await import('@/api/endpoints/adminPlans');
const { usePlanCatalogue } = await import('@/hooks/usePlanCatalogue');
const listPlans = api.listPlans as ReturnType<typeof vi.fn>;

const STANDARD: Plan = {
  key: 'standard',
  name: 'Standard',
  description: null,
  limits: {},
  unlimited: [],
  is_default: true,
  tenant_count: 3,
  created_at: null,
  updated_at: null,
};

describe('usePlanCatalogue (REQ-056 §7.6)', () => {
  beforeEach(() => {
    listPlans.mockReset();
  });

  it('reads nothing while disabled', () => {
    const { result } = renderHook(() => usePlanCatalogue(false));
    expect(result.current.status).toBe('idle');
    expect(listPlans).not.toHaveBeenCalled();
  });

  it('loads the catalogue and keeps a stable object between renders (useMemo, FRONTEND.md §6.1)', async () => {
    listPlans.mockResolvedValue([STANDARD]);
    const { result, rerender } = renderHook(() => usePlanCatalogue());
    expect(result.current.status).toBe('loading');
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.plans).toEqual([STANDARD]);
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });

  it('reports the status of a failed read instead of an empty catalogue', async () => {
    const refusal = new ApiError(
      { error_id: 'e', error_code: 'FORBIDDEN', message: 'no', details: [], timestamp: '', path: '/', method: 'GET' },
      403,
    );
    listPlans.mockImplementation(() => Promise.reject(refusal));
    const { result } = renderHook(() => usePlanCatalogue());
    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.errorStatus).toBe(403);
    expect(result.current.plans).toEqual([]);
  });

  it('reloads on demand and keeps the last list on screen meanwhile', async () => {
    listPlans.mockResolvedValueOnce([STANDARD]);
    const { result } = renderHook(() => usePlanCatalogue());
    await waitFor(() => expect(result.current.status).toBe('ready'));

    let resolve: (plans: Plan[]) => void = () => {};
    listPlans.mockReturnValueOnce(new Promise<Plan[]>((r) => (resolve = r)));
    act(() => result.current.reload());
    expect(result.current.status).toBe('ready');
    expect(result.current.plans).toEqual([STANDARD]);

    const community = { ...STANDARD, key: 'community', name: 'Community', is_default: false };
    await act(async () => resolve([STANDARD, community]));
    expect(result.current.plans).toHaveLength(2);
    expect(listPlans).toHaveBeenCalledTimes(2);
  });
});
