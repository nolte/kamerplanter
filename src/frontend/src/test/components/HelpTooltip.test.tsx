import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import HelpTooltip from '@/components/common/HelpTooltip';
import { renderWithProviders } from '@/test/helpers';

describe('HelpTooltip', () => {
  it('renders the trigger icon for a known glossary term', () => {
    renderWithProviders(
      <HelpTooltip term="ec">
        <span>EC (mS/cm)</span>
      </HelpTooltip>,
    );
    expect(screen.getByTestId('help-tooltip-icon-ec')).toBeTruthy();
    expect(screen.getByText('EC (mS/cm)')).toBeTruthy();
  });

  it('renders icon-only mode without children', () => {
    renderWithProviders(<HelpTooltip term="ph" iconOnly />);
    expect(screen.getByTestId('help-tooltip-icon-ph')).toBeTruthy();
  });

  it('still renders an icon for an unknown term (graceful fallback)', () => {
    renderWithProviders(<HelpTooltip term="totally-unknown" iconOnly />);
    expect(screen.getByTestId('help-tooltip-icon-totally-unknown')).toBeTruthy();
  });

  it('exposes a focusable trigger for keyboard accessibility', () => {
    renderWithProviders(
      <HelpTooltip term="vpd">
        <span>VPD</span>
      </HelpTooltip>,
    );
    const trigger = screen.getByText('VPD').parentElement;
    expect(trigger?.getAttribute('tabindex')).toBe('0');
  });
});
