import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { NutrientPlanUsage } from '@/api/types';

/**
 * REQ-004 — FertilizerUsageGantt is a pure, prop-driven presentation component
 * that renders a week-grid of the plans a fertilizer is used in. These tests
 * drive both terminal states (empty / zero-week) and the populated grid with
 * every cell branch (segment change vs. continuation, known/unknown phase
 * colour, empty week cells) plus the row-navigation callback and the mobile
 * layout branch.
 */

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

import FertilizerUsageGantt from '@/pages/duengung/FertilizerUsageGantt';
import { renderWithProviders } from '../helpers';

beforeEach(() => {
  navigate.mockReset();
  i18n.changeLanguage('de');
});

/**
 * One plan whose drench row spans weeks 1–5 across three phases (with a
 * continuation at the phase-2 boundary so the "unchanged dose" branch is hit,
 * and an unknown phase name so the colour fallback is hit), plus a fertigation
 * row that only spans weeks 1–2 so later weeks render as empty cells.
 */
const richUsage: NutrientPlanUsage[] = [
  {
    key: 'plan-1',
    name: 'Veg Plan',
    phase_entries: [
      {
        phase_name: 'vegetative',
        week_start: 1,
        week_end: 2,
        channels: [
          { channel_id: 'c1', label: 'Tank', application_method: 'drench', ml_per_liter: 4 },
          { channel_id: 'c2', label: 'Auto', application_method: 'fertigation', ml_per_liter: 2 },
        ],
      },
      {
        phase_name: 'flowering',
        week_start: 3,
        week_end: 4,
        // same method + same ml/L as the previous drench segment → continuation
        channels: [
          { channel_id: 'c1', label: 'Tank', application_method: 'drench', ml_per_liter: 4 },
        ],
      },
      {
        phase_name: 'mystery-phase',
        week_start: 5,
        week_end: 5,
        channels: [
          { channel_id: 'c1', label: 'Tank', application_method: 'drench', ml_per_liter: 9 },
        ],
      },
    ],
  },
];

describe('FertilizerUsageGantt — terminal states', () => {
  it('renders the not-used empty state for an empty plan list', () => {
    renderWithProviders(<FertilizerUsageGantt planUsage={[]} />);
    expect(
      screen.getByText(i18n.t('pages.fertilizers.notUsedInAnyPlan')),
    ).toBeInTheDocument();
  });

  it('renders the empty state when rows exist but total weeks resolve to zero', () => {
    const zeroWeek: NutrientPlanUsage[] = [
      {
        key: 'plan-z',
        name: 'Zero',
        phase_entries: [
          {
            phase_name: 'vegetative',
            week_start: 0,
            week_end: 0,
            channels: [
              { channel_id: 'c1', label: 'Tank', application_method: 'drench', ml_per_liter: 1 },
            ],
          },
        ],
      },
    ];
    renderWithProviders(<FertilizerUsageGantt planUsage={zeroWeek} />);
    expect(
      screen.getByText(i18n.t('pages.fertilizers.notUsedInAnyPlan')),
    ).toBeInTheDocument();
  });
});

describe('FertilizerUsageGantt — populated grid', () => {
  it('renders week headers, method rows and dose values across all cell branches', () => {
    renderWithProviders(<FertilizerUsageGantt planUsage={richUsage} />);

    // Section header.
    expect(screen.getByText(i18n.t('pages.fertilizers.usedInPlans'))).toBeInTheDocument();

    // Five week columns (totalWeeks = 5).
    const weekHeaders = screen.getAllByRole('columnheader');
    expect(weekHeaders).toHaveLength(5);

    // Two rows: one drench (grouped across three phases) + one fertigation.
    const drenchLabel = `Veg Plan · ${i18n.t('enums.applicationMethod.drench')}`;
    const fertigationLabel = `Veg Plan · ${i18n.t('enums.applicationMethod.fertigation')}`;
    expect(screen.getByText(drenchLabel)).toBeInTheDocument();
    expect(screen.getByText(fertigationLabel)).toBeInTheDocument();

    // Dose labels rendered inside the cells (4 appears for weeks 1–4, 9 for week 5, 2 for fertigation).
    expect(screen.getAllByText('4').length).toBeGreaterThan(0);
    expect(screen.getByText('9')).toBeInTheDocument();
    // "2" is the fertigation dose (week headers render the number in a separate node).
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
  });

  it('navigates to the plan detail page from a row open-in-new button', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerUsageGantt planUsage={richUsage} />);

    // Each row exposes an icon-button whose accessible name is the plan name.
    const openButtons = screen.getAllByRole('button', { name: 'Veg Plan' });
    expect(openButtons.length).toBeGreaterThan(0);
    await user.click(openButtons[0]);
    expect(navigate).toHaveBeenCalledWith('/duengung/plans/plan-1');
  });
});

describe('FertilizerUsageGantt — mobile layout', () => {
  const realMatchMedia = window.matchMedia;

  afterEach(() => {
    window.matchMedia = realMatchMedia;
  });

  it('renders the compact mobile grid when the viewport matches a small breakpoint', () => {
    // MUI useMediaQuery consults window.matchMedia; force every query to match
    // so the isMobile branch (narrow label column, tighter cells) is exercised.
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;

    renderWithProviders(<FertilizerUsageGantt planUsage={richUsage} />);
    expect(screen.getByText(i18n.t('pages.fertilizers.usedInPlans'))).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader')).toHaveLength(5);
  });
});
