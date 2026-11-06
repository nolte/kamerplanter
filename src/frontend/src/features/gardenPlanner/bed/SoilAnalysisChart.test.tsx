/**
 * The soil history chart (REQ-053 GP-FR-122, WP 8.8): one chart per parameter with one line per method, the method
 * change marked, and a table alternative that screen readers always get - plus the axe pass.
 */
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import SoilAnalysisChart from './SoilAnalysisChart';
import { soilAnalyses } from './soilAnalysisTestKit';

afterEach(() => cleanup());

describe('SoilAnalysisChart', () => {
  it('has a section per charted parameter and a table for screen readers with the method change marked', () => {
    renderWithProviders(<SoilAnalysisChart data={soilAnalyses()} />);
    expect(screen.getByRole('region', { name: 'pH over time' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'EC (conductivity) over time' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Humus over time' })).toBeInTheDocument();

    // The table sits in the DOM even while the chart is shown (visually hidden), so it is the accessible content.
    const table = screen.getByTestId('soil-history-table-ph');
    const rows = within(table).getAllByRole('row').slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining('Water'),
      expect.stringMatching(/CaCl.*Method change/),
    ]);
    expect(within(screen.getByTestId('soil-history-table-humus')).getByText('Method unknown')).toBeInTheDocument();
  });

  it('shows the table instead of the chart on request', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SoilAnalysisChart data={soilAnalyses()} />);
    await user.click(screen.getByRole('switch', { name: 'Show as table' }));
    expect(screen.getByTestId('soil-history-table-ec')).toBeVisible();
    expect(within(screen.getByTestId('soil-history-table-ec')).getByText(/1:5 extract/)).toBeInTheDocument();
  });

  it('says so when no analysis carries a pH, EC or humus value', () => {
    renderWithProviders(
      <SoilAnalysisChart
        data={soilAnalyses({ series: [{ parameter: 'p', method: 'cal', points: [] }], method_changes: [] })}
      />,
    );
    expect(screen.getByTestId('soil-history-no-chart-values')).toBeInTheDocument();
  });

  it('has no accessibility violations, as chart and as table', async () => {
    const user = userEvent.setup();
    const view = renderWithProviders(<SoilAnalysisChart data={soilAnalyses()} />);
    await expectNoA11yViolations(view.container, { minImpact: 'serious', minElements: 30 });
    await user.click(screen.getByRole('switch', { name: 'Show as table' }));
    await expectNoA11yViolations(view.container, { minImpact: 'serious', minElements: 30 });
  });
});
