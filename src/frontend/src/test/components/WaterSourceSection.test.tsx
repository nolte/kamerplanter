import { screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import WaterSourceSection from '@/components/water/WaterSourceSection';
import type { SiteWaterConfig, WaterSourceWarning } from '@/api/types';
import { renderWithProviders } from '../helpers';

const defaultConfig: SiteWaterConfig = {
  has_ro_system: false,
  tap_water_profile: null,
  ro_water_profile: null,
};

describe('WaterSourceSection', () => {
  it('renders water config heading', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/Wasserquelle|Water Source/i)).toBeTruthy();
  });

  it('renders tap water EC and pH fields', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.getByTestId('tap-ec')).toBeTruthy();
    expect(screen.getByTestId('tap-ph')).toBeTruthy();
  });

  it('does not show RO fields when has_ro_system is false', () => {
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={vi.fn()} />,
    );
    expect(screen.queryByTestId('ro-ec')).toBeNull();
    expect(screen.queryByTestId('ro-ph')).toBeNull();
  });

  it('shows RO fields when has_ro_system is true', () => {
    const config: SiteWaterConfig = {
      ...defaultConfig,
      has_ro_system: true,
    };
    renderWithProviders(
      <WaterSourceSection value={config} onChange={vi.fn()} />,
    );
    expect(screen.getByTestId('ro-ec')).toBeTruthy();
    expect(screen.getByTestId('ro-ph')).toBeTruthy();
  });

  it('calls onChange when RO toggle is clicked', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <WaterSourceSection value={defaultConfig} onChange={onChange} />,
    );
    const toggle = screen.getByTestId('ro-system-toggle');
    fireEvent.click(toggle);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ has_ro_system: true }),
    );
  });

  it('displays warnings', () => {
    const warnings: WaterSourceWarning[] = [
      { code: 'gh_plausibility', message: 'GH mismatch', severity: 'warning' },
      { code: 'ro_membrane', message: 'RO EC high', severity: 'warning' },
    ];
    renderWithProviders(
      <WaterSourceSection
        value={defaultConfig}
        onChange={vi.fn()}
        warnings={warnings}
      />,
    );
    expect(screen.getByTestId('water-warning-gh_plausibility')).toBeTruthy();
    expect(screen.getByTestId('water-warning-ro_membrane')).toBeTruthy();
  });
});
