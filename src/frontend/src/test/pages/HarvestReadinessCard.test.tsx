import { screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import i18n from 'i18next';
import type { ReadinessAssessment } from '@/api/types';
import HarvestReadinessCard from '@/pages/ernte/HarvestReadinessCard';
import { renderWithProviders } from '../helpers';

/**
 * REQ-007 §3 "Reife-Visualisierung" — the presentation half of the harvest
 * readiness feature. Spec test cases TC-007-032 … TC-007-035.
 */

function makeReadiness(overrides: Partial<ReadinessAssessment> = {}): ReadinessAssessment {
  return {
    overall_score: 92,
    recommendation: 'optimal',
    estimated_days: 1,
    indicators: [
      { indicator_key: 'trichome', stage: 'peak', score: 100, reliability: 0.9, weighted_contribution: 90 },
      { indicator_key: 'aroma', stage: 'approaching', score: 75, reliability: 0.7, weighted_contribution: 52.5 },
    ],
    ...overrides,
  };
}

describe('HarvestReadinessCard (REQ-007 §3)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
  });

  it('renders the score, a determinate progress bar and the recommendation chip (TC-007-032)', () => {
    renderWithProviders(<HarvestReadinessCard readiness={makeReadiness()} />);

    const card = screen.getByTestId('harvest-readiness-card');
    expect(within(card).getByText(i18n.t('pages.harvest.readiness'))).toBeInTheDocument();
    expect(within(card).getByText('92')).toBeInTheDocument();

    const progress = within(card).getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '92');
    expect(progress.className).toContain('colorSuccess');

    expect(within(card).getByText(i18n.t('enums.readinessRecommendation.optimal'))).toBeInTheDocument();
    expect(
      within(card).getByText(`${i18n.t('pages.harvest.estimatedDays')}:`, { exact: false }),
    ).toBeInTheDocument();
  });

  it('caps the progress bar at 100 for an out-of-range score', () => {
    renderWithProviders(<HarvestReadinessCard readiness={makeReadiness({ overall_score: 140 })} />);

    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('colours the gauge by score band (warning at 50-79, error below 50) (TC-007-033)', () => {
    const { unmount } = renderWithProviders(
      <HarvestReadinessCard readiness={makeReadiness({ overall_score: 60 })} />,
    );
    expect(screen.getByRole('progressbar').className).toContain('colorWarning');
    unmount();

    renderWithProviders(<HarvestReadinessCard readiness={makeReadiness({ overall_score: 20, recommendation: 'immature' })} />);
    expect(screen.getByRole('progressbar').className).toContain('colorError');
  });

  it('renders one row per indicator with stage, score, reliability and contribution (TC-007-035)', () => {
    renderWithProviders(
      <HarvestReadinessCard
        readiness={makeReadiness({
          indicators: [
            { indicator_key: 'trichome', stage: 'peak', score: 100, reliability: 0.9, weighted_contribution: 90 },
            { indicator_key: 'aroma', stage: 'approaching', score: 75, reliability: 0.7, weighted_contribution: 52.5 },
            { indicator_key: 'brix', stage: 'overripe', score: 40, reliability: 0.5, weighted_contribution: 20 },
            { indicator_key: 'color', stage: 'immature', score: 10, reliability: 0.4, weighted_contribution: 4 },
          ],
        })}
      />,
    );

    const rows = within(screen.getByRole('table')).getAllByRole('row');
    // 1 header row + 4 indicator rows
    expect(rows).toHaveLength(5);
    expect(screen.getByText('trichome')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.ripenessStage.overripe'))).toBeInTheDocument();
    // Reliability is rendered as a whole-percent value, contribution to 1 decimal.
    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('52.5')).toBeInTheDocument();
  });

  it('hides the estimated-days block when no estimate is available (TC-007-034)', () => {
    renderWithProviders(<HarvestReadinessCard readiness={makeReadiness({ estimated_days: null })} />);

    expect(screen.queryByText(`${i18n.t('pages.harvest.estimatedDays')}:`, { exact: false })).toBeNull();
    // Everything else still renders.
    expect(screen.getByTestId('harvest-readiness-card')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('omits the breakdown table when the assessment carries no indicators', () => {
    renderWithProviders(<HarvestReadinessCard readiness={makeReadiness({ indicators: [] })} />);

    expect(screen.queryByRole('table')).toBeNull();
  });

  describe('mobile viewport (393px)', () => {
    afterEach(() => {
      // @ts-expect-error - cleanup of the matchMedia stub between tests
      delete window.matchMedia;
    });

    const enableMobile = () => {
      window.matchMedia = (query: string) =>
        ({
          matches: true,
          media: query,
          onchange: null,
          addListener: () => {},
          removeListener: () => {},
          addEventListener: () => {},
          removeEventListener: () => {},
          dispatchEvent: () => false,
        }) as unknown as MediaQueryList;
    };

    it('renders a stacked MobileCard per indicator instead of the five-column table (no horizontal overflow)', () => {
      enableMobile();
      renderWithProviders(
        <HarvestReadinessCard
          readiness={makeReadiness({
            indicators: [
              { indicator_key: 'trichome', stage: 'peak', score: 100, reliability: 0.9, weighted_contribution: 90 },
              { indicator_key: 'aroma', stage: 'approaching', score: 75, reliability: 0.7, weighted_contribution: 52.5 },
            ],
          })}
        />,
      );

      // The five-column desktop table must not render at 393px — that is the
      // layout that squashes onto a phone viewport.
      expect(screen.queryByRole('table')).toBeNull();

      const cards = screen.getAllByTestId('data-table-row');
      expect(cards).toHaveLength(2);
      expect(within(cards[0]).getByTestId('card-title')).toHaveTextContent('trichome');
      expect(within(cards[0]).getByText(i18n.t('enums.ripenessStage.peak'))).toBeInTheDocument();
      expect(within(cards[0]).getByTestId(`card-field-score`)).toHaveTextContent('100');
      expect(within(cards[0]).getByTestId('card-field-reliability')).toHaveTextContent('90%');
      expect(within(cards[0]).getByTestId('card-field-contribution')).toHaveTextContent('90');
    });
  });

  it('falls back to the raw backend value for an untranslated stage or recommendation', () => {
    renderWithProviders(
      <HarvestReadinessCard
        readiness={makeReadiness({
          recommendation: 'not_yet_translated',
          indicators: [
            { indicator_key: 'mystery', stage: 'unmapped_stage', score: 5, reliability: 0.1, weighted_contribution: 0.5 },
          ],
        })}
      />,
    );

    // The literal i18n key must never reach the screen.
    expect(screen.queryByText(/^enums\./)).toBeNull();
    expect(screen.getByText('not_yet_translated')).toBeInTheDocument();
    expect(screen.getByText('unmapped_stage')).toBeInTheDocument();
  });
});
