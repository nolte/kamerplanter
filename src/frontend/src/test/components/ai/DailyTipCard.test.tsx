import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import type { AiTipCard } from '@/api/types';

const getDailyTip = vi.fn();
const dismissDailyTip = vi.fn();

vi.mock('@/api', () => ({
  aiApi: {
    getDailyTip: (...args: unknown[]) => getDailyTip(...args),
    dismissDailyTip: (...args: unknown[]) => dismissDailyTip(...args),
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

  it('renders nothing when there is no daily tip', async () => {
    getDailyTip.mockResolvedValue(null);
    renderWithProviders(<DailyTipCard />);

    await waitFor(() => expect(getDailyTip).toHaveBeenCalled());
    expect(screen.queryByTestId('daily-tip-card')).toBeNull();
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
