import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import SurvivalStatsPanel from '@/pages/pflanzen/SurvivalStatsPanel';
import type { SurvivalStats } from '@/api/types';
import '@/i18n';

function makeStats(overrides: Partial<SurvivalStats> = {}): SurvivalStats {
  return {
    total: 10,
    terminated: 6,
    active: 4,
    died: 3,
    survived: 7,
    survival_rate: 0.7,
    by_termination_type: [
      { termination_type: 'harvested', count: 2 },
      { termination_type: 'died', count: 3 },
    ],
    by_termination_cause: [
      { termination_cause: 'pest', count: 2 },
      { termination_cause: 'frost', count: 1 },
    ],
    loss_by_phase: [
      { phase_name: 'vegetative', count: 2 },
      { phase_name: 'flowering', count: 1 },
    ],
    ...overrides,
  };
}

function renderPanel(stats: SurvivalStats) {
  return render(
    <ThemeContextProvider>
      <SurvivalStatsPanel stats={stats} />
    </ThemeContextProvider>,
  );
}

describe('SurvivalStatsPanel', () => {
  it('renders the survival rate and numeric breakdown', () => {
    renderPanel(makeStats());
    // Rate chip shows 70% (0.7 * 100).
    expect(screen.getByTestId('survival-rate-chip').textContent).toContain('70');
    expect(screen.getByTestId('survival-total').textContent).toBe('10');
    expect(screen.getByTestId('survival-survived').textContent).toBe('7');
    expect(screen.getByTestId('survival-died').textContent).toBe('3');
  });

  it('renders the loss chart when there are losses', () => {
    renderPanel(makeStats());
    expect(screen.getByTestId('survival-chart')).toBeTruthy();
    expect(screen.queryByTestId('survival-chart-empty')).toBeNull();
  });

  it('toggles the chart dimension between phase and cause', async () => {
    const user = userEvent.setup();
    renderPanel(makeStats());
    // Default dimension is phase; switching to cause keeps the chart mounted.
    await user.click(screen.getByTestId('dimension-cause'));
    expect(screen.getByTestId('survival-chart')).toBeTruthy();
    await user.click(screen.getByTestId('dimension-phase'));
    expect(screen.getByTestId('survival-chart')).toBeTruthy();
  });

  it('shows a no-losses message when nothing died', () => {
    renderPanel(makeStats({ died: 0, survived: 10, survival_rate: 1, by_termination_cause: [], loss_by_phase: [], by_termination_type: [{ termination_type: 'harvested', count: 5 }] }));
    expect(screen.getByTestId('survival-chart-empty')).toBeTruthy();
    expect(screen.queryByTestId('survival-chart')).toBeNull();
  });

  it('shows an empty state when there are no plants at all', () => {
    renderPanel(makeStats({ total: 0, terminated: 0, active: 0, died: 0, survived: 0, survival_rate: 0, by_termination_type: [], by_termination_cause: [], loss_by_phase: [] }));
    expect(screen.getByTestId('survival-empty')).toBeTruthy();
  });
});
