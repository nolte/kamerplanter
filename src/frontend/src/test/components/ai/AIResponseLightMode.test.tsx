import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/helpers';

/**
 * #3025 L-14 — light mode has no `/privacy` page (no accounts; the route redirects to the dashboard). The
 * "uses your plant data" chip still informs there, but it must not pretend to lead to privacy settings.
 */
vi.mock('@/config/mode', () => ({ KAMERPLANTER_MODE: 'light', isLightMode: true, isFullMode: false }));

const { default: AIResponse } = await import('@/components/ai/AIResponse');

describe('AIResponse in light mode', () => {
  it('shows the tenant-data chip without a link to the privacy settings', () => {
    renderWithProviders(
      <AIResponse usesTenantData>
        <span>x</span>
      </AIResponse>,
    );
    const chip = screen.getByTestId('ai-tenant-data-indicator');
    expect(chip).not.toHaveAttribute('href');
    expect(chip.closest('a')).toBeNull();
  });
});
