import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TankStateChart from '@/components/tanks/TankStateChart';
import { renderWithProviders } from '@/test/helpers';
import type { TankState } from '@/api/types';

// Mock recharts ResponsiveContainer since jsdom has no layout engine
vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactElement }) => (
      <div style={{ width: 800, height: 280 }}>{children}</div>
    ),
  };
});

function createState(overrides: Partial<TankState> & { recorded_at: string }): TankState {
  return {
    key: `ts-${Math.random().toString(36).slice(2)}`,
    tank_key: 'tank-1',
    fill_level_liters: null,
    fill_level_percent: null,
    ph: null,
    ec_ms: null,
    water_temp_celsius: null,
    tds_ppm: null,
    dissolved_oxygen_mgl: null,
    orp_mv: null,
    source: 'manual',
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

const twoStates: TankState[] = [
  createState({ recorded_at: '2026-03-01T10:00:00Z', ph: 6.2, ec_ms: 1.4, water_temp_celsius: 20, fill_level_percent: 80 }),
  createState({ recorded_at: '2026-03-02T10:00:00Z', ph: 6.5, ec_ms: 1.6, water_temp_celsius: 21, fill_level_percent: 70 }),
];

describe('TankStateChart', () => {
  it('renders nothing when fewer than 2 data points', () => {
    const { container } = renderWithProviders(
      <TankStateChart states={[twoStates[0]]} />,
    );
    expect(container.textContent).toBe('');
  });

  it('renders chart with content when 2+ data points exist', () => {
    const { container } = renderWithProviders(<TankStateChart states={twoStates} />);
    // Chart renders recharts wrapper (not empty/null)
    expect(container.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('renders toggle button group for metrics', () => {
    renderWithProviders(<TankStateChart states={twoStates} />);
    expect(screen.getByRole('group')).toBeInTheDocument();
  });

  it('renders nothing for empty states array', () => {
    const { container } = renderWithProviders(
      <TankStateChart states={[]} />,
    );
    expect(container.textContent).toBe('');
  });

  it('toggle buttons can hide metrics', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TankStateChart states={twoStates} />);
    const phButton = screen.getByRole('button', { name: /pH/i });
    // Click pH toggle to deselect it (it starts selected)
    await user.click(phButton);
    // The button should still exist but be de-selected (aria-pressed=false)
    expect(phButton).toHaveAttribute('aria-pressed', 'false');
  });
});
