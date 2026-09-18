import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createStoreWithTenantRole } from '@/test/helpers';
import type { AiTipCard } from '@/api/types';

const getDailyTip = vi.fn();
const dismissDailyTip = vi.fn();
const refreshDailyTip = vi.fn();

vi.mock('@/api', () => ({
  aiApi: {
    getDailyTip: (...args: unknown[]) => getDailyTip(...args),
    dismissDailyTip: (...args: unknown[]) => dismissDailyTip(...args),
    refreshDailyTip: (...args: unknown[]) => refreshDailyTip(...args),
  },
}));

import DailyTipCard from '@/components/ai/DailyTipCard';

function makeTip(overrides: Partial<AiTipCard> = {}): AiTipCard {
  return {
    key: 'tip-1',
    context_type: 'daily',
    context_key: '2026-07-11',
    tip_type: 'optimization',
    priority: 'low',
    title: 'Water in the morning',
    body: 'Give your tomato a morning drink.',
    sources: [],
    language: 'de',
    language_mismatch_warning: false,
    uses_tenant_data: true,
    confidence: 'high',
    model_name: 'gemma3:12b',
    ...overrides,
  };
}

describe('DailyTipCard', () => {
  beforeEach(() => {
    getDailyTip.mockReset();
    dismissDailyTip.mockReset();
    refreshDailyTip.mockReset();
    try {
      localStorage.clear();
    } catch {
      /* storage unavailable */
    }
  });

  it('renders the daily tip wrapped in an AIResponse', async () => {
    getDailyTip.mockResolvedValue(makeTip());
    renderWithProviders(<DailyTipCard />);

    expect(await screen.findByTestId('daily-tip-card')).toBeTruthy();
    expect(screen.getByText('Water in the morning')).toBeTruthy();
    // Rendered through the mandatory AIResponse wrapper (KI badge visible).
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
    expect(screen.getByTestId('ai-tenant-data-indicator')).toBeTruthy();
  });

  it('renders nothing when there is no daily tip and the viewer cannot generate one', async () => {
    getDailyTip.mockResolvedValue(null);
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('viewer') });

    await waitFor(() => expect(getDailyTip).toHaveBeenCalled());
    expect(screen.queryByTestId('daily-tip-card')).toBeNull();
    expect(screen.queryByTestId('daily-tip-empty')).toBeNull();
  });

  it('invites a grower to generate today\u2019s tip when there is none', async () => {
    // #1461 — the read stopped generating on a miss, so `null` is now also the
    // "nothing generated for today" answer. Without an explicit invitation the
    // dashboard card would be permanently invisible.
    getDailyTip.mockResolvedValue(null);
    refreshDailyTip.mockResolvedValue(makeTip({ title: 'Generated today' }));
    const user = userEvent.setup();
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('grower') });

    expect(await screen.findByTestId('daily-tip-empty')).toBeTruthy();
    await user.click(screen.getByTestId('daily-tip-generate'));

    await waitFor(() => expect(refreshDailyTip).toHaveBeenCalled());
    expect(await screen.findByText('Generated today')).toBeTruthy();
  });

  it('says so when generating is refused', async () => {
    // Review SCR-002 — `.catch(() => undefined)` left a refusal and "never
    // pressed" rendering identically, so a 403 (viewer, KI off, missing consent)
    // looked like a dead button.
    getDailyTip.mockResolvedValue(null);
    refreshDailyTip.mockRejectedValue(new Error('refused'));
    const user = userEvent.setup();
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('grower') });

    await user.click(await screen.findByTestId('daily-tip-generate'));

    expect(await screen.findByTestId('daily-tip-generate-error')).toBeTruthy();
    // The control stays, inviting a retry rather than repeating its first label.
    expect(screen.getByTestId('daily-tip-generate')).toBeTruthy();
  });

  it('distinguishes a successful generate that produced nothing from a refusal', async () => {
    // The third state the old code collapsed: the call succeeded and the
    // Knowledge Service simply had nothing to say. Telling the user to try again
    // later is a different sentence from telling them it failed.
    getDailyTip.mockResolvedValue(null);
    refreshDailyTip.mockResolvedValue(null);
    const user = userEvent.setup();
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('grower') });

    await user.click(await screen.findByTestId('daily-tip-generate'));

    expect(await screen.findByTestId('daily-tip-generate-empty')).toBeTruthy();
    expect(screen.queryByTestId('daily-tip-generate-error')).toBeNull();
  });

  it('explains a disabled-AI refusal instead of showing a generic failure', async () => {
    const { ApiError } = await import('@/api/errors');
    getDailyTip.mockResolvedValue(null);
    refreshDailyTip.mockRejectedValue(
      new ApiError(
        {
          error_id: 'err-1',
          timestamp: '2026-09-18T00:00:00Z',
          error_code: 'AI_DISABLED_FOR_TENANT',
          message: 'forbidden',
          details: [],
          path: '/ai/daily-tip/refresh',
          method: 'POST',
        },
        403,
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('grower') });

    await user.click(await screen.findByTestId('daily-tip-generate'));

    const error = await screen.findByTestId('daily-tip-generate-error');
    expect(error.textContent).toContain('disabled');
  });

  it('offers no generate invitation after a failed read', async () => {
    // A fetch failure is not an empty day. Offering "generate" over an outage
    // would turn a transient error into a needless LLM call the user pays for.
    getDailyTip.mockRejectedValue(new Error('offline'));
    renderWithProviders(<DailyTipCard />, { store: createStoreWithTenantRole('grower') });

    await waitFor(() => expect(getDailyTip).toHaveBeenCalled());
    expect(screen.queryByTestId('daily-tip-empty')).toBeNull();
    expect(screen.queryByTestId('daily-tip-generate')).toBeNull();
  });

  it('hides the card and calls the API on dismiss', async () => {
    getDailyTip.mockResolvedValue(makeTip());
    dismissDailyTip.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithProviders(<DailyTipCard />);

    await screen.findByTestId('daily-tip-card');
    await user.click(screen.getByTestId('daily-tip-dismiss'));

    expect(dismissDailyTip).toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByTestId('daily-tip-card')).toBeNull());
  });

  it('renders nothing on a fetch error (online-only degradation)', async () => {
    getDailyTip.mockRejectedValue(new Error('offline'));
    renderWithProviders(<DailyTipCard />);

    await waitFor(() => expect(getDailyTip).toHaveBeenCalled());
    expect(screen.queryByTestId('daily-tip-card')).toBeNull();
  });
});
