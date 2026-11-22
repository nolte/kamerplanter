/**
 * The follow-up crop recommendation under the timeline (REQ-053 GP-FR-133, WP 8.14): the step of the feeder cycle, the
 * families and species of it, why a list is empty, and that no amount is ever named.
 */
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { noHistoryRecommendation } from './historyTestKit';
import type { SuccessionRecommendation } from './historyTypes';
import SuccessionRecommendationPanel from './SuccessionRecommendationPanel';
import type { SuccessionState } from './useSuccessionRecommendation';


function ready(overrides: Partial<SuccessionRecommendation>): SuccessionState {
  return { status: 'ready', recommendation: noHistoryRecommendation(overrides) };
}

const AFTER_HEAVY = ready({
  status: 'ok',
  previous: { year: 2025, step: 'main_crop', nutrient_demand: 'heavy_feeder', family_keys: ['fam_sol'] },
  target: 'medium_feeder',
  families: [
    {
      family_key: 'fam_api',
      family_name: 'Apiaceae',
      benefit_score: 0.7,
      benefit_reason: 'soil_structure',
      pause_years: 3,
      species: [
        {
          species_key: 'sp_carrot',
          scientific_name: 'Daucus carota',
          common_name: 'Carrot',
          nutrient_demand: 'medium_feeder',
          nitrogen_fixing: false,
        },
      ],
    },
    {
      family_key: 'fam_fab',
      family_name: 'Fabaceae',
      benefit_score: null,
      benefit_reason: 'something_new',
      pause_years: null,
      species: [
        { species_key: 'sp_bean', scientific_name: 'Phaseolus vulgaris', common_name: null, nutrient_demand: 'medium_feeder', nitrogen_fixing: true },
      ],
    },
  ],
});

afterEach(() => cleanup());

describe('SuccessionRecommendationPanel', () => {
  it('names the step after the last year, the families and their species with the feeder class as text', () => {
    renderWithProviders(<SuccessionRecommendationPanel state={AFTER_HEAVY} onRetry={() => undefined} />);

    expect(screen.getByTestId('succession-basis')).toHaveTextContent('After 2025 (Heavy Feeder) the next step is: medium feeder.');
    const apiaceae = screen.getByTestId('succession-family-fam_api');
    expect(within(apiaceae).getByRole('heading', { name: 'Apiaceae' })).toBeInTheDocument();
    expect(apiaceae).toHaveTextContent('Carrot (Daucus carota)');
    expect(apiaceae).toHaveTextContent('Medium Feeder');
    expect(apiaceae).toHaveTextContent('improves the soil structure');
  });

  it('shows nitrogen fixation as a fact, an unknown pause as unknown, and an unknown reason code not at all', () => {
    renderWithProviders(<SuccessionRecommendationPanel state={AFTER_HEAVY} onRetry={() => undefined} />);

    const fabaceae = screen.getByTestId('succession-family-fam_fab');
    expect(fabaceae).toHaveTextContent('fixes nitrogen');
    expect(fabaceae).toHaveTextContent('No rotation pause is stored for this family.');
    expect(fabaceae).not.toHaveTextContent('something_new');
  });

  it('names no amount: only the order of the cycle', () => {
    const { container } = renderWithProviders(<SuccessionRecommendationPanel state={AFTER_HEAVY} onRetry={() => undefined} />);
    expect(container.textContent).not.toMatch(/\b(kg|g\/m|l\/m|kg N|N\/ha)\b/i);
    expect(container.textContent).toMatch(/not a fertiliser recommendation/);
  });

  it('offers a fallow year beside green manure at the restoring step', () => {
    renderWithProviders(
      <SuccessionRecommendationPanel
        state={ready({
          status: 'ok',
          previous: { year: 2025, step: 'main_crop', nutrient_demand: 'light_feeder', family_keys: ['fam_fab'] },
          target: 'restoring',
          fallow_option: true,
        })}
        onRetry={() => undefined}
      />,
    );
    expect(screen.getByTestId('succession-basis')).toHaveTextContent('the next step is: green manure or fallow');
    expect(screen.getByTestId('succession-fallow')).toBeInTheDocument();
  });

  it('lists the families still keeping their pause as held back, not as suggestions', () => {
    renderWithProviders(
      <SuccessionRecommendationPanel
        state={ready({
          status: 'no_matching_species',
          previous: { year: 2025, step: 'main_crop', nutrient_demand: 'heavy_feeder', family_keys: ['fam_sol'] },
          target: 'medium_feeder',
          held_back: [{ family_key: 'fam_bra', family_name: 'Brassicaceae', last_year: 2024, pause_years: 4 }],
        })}
        onRetry={() => undefined}
      />,
    );
    expect(screen.getByTestId('succession-held-back')).toHaveTextContent('Brassicaceae (last 2024, pause 4 years)');
    expect(screen.queryByTestId('succession-family-fam_bra')).toBeNull();
    expect(screen.getByTestId('succession-status')).toHaveTextContent('no species with a stored feeder class');
  });

  it.each([
    ['no_history', 'No year is recorded yet'],
    ['demand_unknown', 'No feeder class is stored for the last crop'],
    ['no_successor_data', 'No follow-up families are stored'],
  ] as const)('says why the list is empty for %s', (status, text) => {
    renderWithProviders(<SuccessionRecommendationPanel state={ready({ status })} onRetry={() => undefined} />);
    expect(screen.getByTestId('succession-status')).toHaveTextContent(text);
    expect(screen.queryByTestId('succession-basis')).toBeNull();
  });

  it('renders nothing when the rotation check is off for the bed (the timeline tells it)', () => {
    renderWithProviders(
      <SuccessionRecommendationPanel state={ready({ status: 'not_applicable', rotation_applicable: false })} onRetry={() => undefined} />,
    );
    expect(screen.queryByTestId('succession-panel')).toBeNull();
  });

  it('shows a failed load beside the timeline with a retry', async () => {
    const retry = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<SuccessionRecommendationPanel state={{ status: 'error', message: 'boom' }} onRetry={retry} />);

    expect(screen.getByTestId('succession-error')).toHaveTextContent('The timeline is not affected');
    await user.click(screen.getByRole('button', { name: 'Retry' }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it('has no critical accessibility violation', async () => {
    const { container } = renderWithProviders(<SuccessionRecommendationPanel state={AFTER_HEAVY} onRetry={() => undefined} />);
    await expectNoA11yViolations(container);
  });
});
