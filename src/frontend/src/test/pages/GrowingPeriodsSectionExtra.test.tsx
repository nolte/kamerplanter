import { screen, within, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, beforeAll, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import GrowingPeriodsSection from '@/pages/stammdaten/GrowingPeriodsSection';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';
import type { GrowingPeriod, Species } from '@/api/types';

function makePeriod(overrides: Partial<GrowingPeriod> = {}): GrowingPeriod {
  return {
    label: 'Main',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    growth_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    ...overrides,
  };
}

function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomate'],
    family_key: null,
    family_name: null,
    genus: 'Solanum',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 0,
    base_temp: 10,
    synonyms: [],
    taxonomic_authority: '',
    taxonomic_status: '',
    description: '',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    frost_sensitivity: null,
    plant_category: null,
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
    propagation_configs: [],
    allows_harvest: true,
    growing_periods: [],
    container_suitable: null,
    recommended_container_volume_l: null,
    min_container_depth_cm: null,
    mature_height_cm: null,
    mature_width_cm: null,
    spacing_cm: null,
    indoor_suitable: null,
    balcony_suitable: null,
    greenhouse_recommended: false,
    support_required: false,
    watering_guide: null,
    default_nutrient_plan_key: null,
    representative_image_url: null,
    representative_image_attribution: null,
    representative_image_license: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

beforeAll(() => {
  // jsdom does not implement pointer-capture; stub it so the drag handlers run.
  if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = vi.fn();
  }
});

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('GrowingPeriodsSection — empty state & add period', () => {
  it('shows the vegetative empty-state hint when no periods and vegetative-only propagation', () => {
    const species = makeSpecies({
      allows_harvest: false,
      growing_periods: [],
      propagation_configs: [{ method: 'cutting', months: [5] }],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.getByText(i18n.t('pages.species.noPeriodsDefined'))).toBeInTheDocument();
    const methods = i18n.t('enums.propagationMethod.cutting');
    expect(
      screen.getByText(i18n.t('pages.species.noPeriodsVegetativeHint', { methods })),
    ).toBeInTheDocument();
  });

  it('adds a period from the empty-state action, revealing the chart and action bar', async () => {
    const species = makeSpecies({ growing_periods: [], propagation_configs: [] });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });

    // Empty state present initially.
    expect(screen.getByText(i18n.t('pages.species.noPeriodsDefined'))).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: i18n.t('pages.species.addPeriod') }));

    // Now the save action appears and the empty state is gone.
    expect(screen.getByRole('button', { name: i18n.t('common.save') })).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('pages.species.noPeriodsDefined'))).toBeNull();
  });
});

describe('GrowingPeriodsSection — save & delete', () => {
  it('saves the periods via updateSpecies and calls onSaved', async () => {
    let putBody: Record<string, unknown> | null = null;
    server.use(
      http.put('/api/v1/species/sp-1', async ({ request }) => {
        putBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makeSpecies());
      }),
    );
    const onSaved = vi.fn();
    const species = makeSpecies({
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ direct_sow_months: [3], harvest_months: [8] })],
    });
    renderWithProviders(
      <GrowingPeriodsSection speciesKey="sp-1" species={species} onSaved={onSaved} />,
      { store: createStoreWithExpertise('expert') },
    );

    await userEvent.click(screen.getByRole('button', { name: i18n.t('common.save') }));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(putBody).toMatchObject({ scientific_name: 'Solanum lycopersicum' });
    expect(Array.isArray((putBody as unknown as Record<string, unknown>).growing_periods)).toBe(true);
  });

  it('reports an error and does not call onSaved when saving fails', async () => {
    server.use(
      http.put('/api/v1/species/sp-1', () => HttpResponse.json({ message: 'x' }, { status: 500 })),
    );
    const onSaved = vi.fn();
    const species = makeSpecies({
      growing_periods: [makePeriod({ direct_sow_months: [3] })],
    });
    renderWithProviders(
      <GrowingPeriodsSection speciesKey="sp-1" species={species} onSaved={onSaved} />,
      { store: createStoreWithExpertise('expert') },
    );

    const save = screen.getByRole('button', { name: i18n.t('common.save') });
    await userEvent.click(save);
    await waitFor(() => expect(save).not.toBeDisabled());
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('deletes a period from the expanded detail form', async () => {
    const species = makeSpecies({
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ label: 'Frühbeet', direct_sow_months: [3], harvest_months: [8] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });

    // Expand the period detail row.
    fireEvent.click(screen.getByText('Frühbeet'));
    const deleteBtn = await screen.findByTestId('delete-period-0');
    await userEvent.click(deleteBtn);

    // The period is gone → empty state returns.
    await waitFor(() =>
      expect(screen.getByText(i18n.t('pages.species.noPeriodsDefined'))).toBeInTheDocument(),
    );
  });
});

describe('GrowingPeriodsSection — legacy fallback', () => {
  it('synthesizes a period from legacy flat fields when growing_periods is empty', () => {
    const species = makeSpecies({
      growing_periods: [],
      sowing_indoor_weeks_before_last_frost: 6,
      direct_sow_months: [4, 5],
      harvest_months: [8, 9],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });

    // A timing chart (thus a save button) exists rather than the empty state.
    expect(screen.getByRole('button', { name: i18n.t('common.save') })).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('pages.species.noPeriodsDefined'))).toBeNull();
  });
});

describe('GrowingPeriodsSection — sow/harvest overlap framing', () => {
  it('frames the overlap as normal for a perennial (R-016/R-002)', () => {
    const species = makeSpecies({
      harvest_pattern: 'perennial',
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ direct_sow_months: [6], harvest_months: [6, 7] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(screen.getByText(i18n.t('pages.species.sowHarvestOverlapHint'))).toBeInTheDocument();
  });

  it('flags the overlap for review for an annual-looking species', () => {
    const species = makeSpecies({
      harvest_pattern: 'single',
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ direct_sow_months: [6], harvest_months: [6] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(screen.getByText(i18n.t('pages.species.sowHarvestOverlapHintAnnual'))).toBeInTheDocument();
  });
});

describe('GrowingPeriodsSection — pointer drag (expert)', () => {
  it('resizes a bar via pointer down/move/up and announces the range', () => {
    const species = makeSpecies({
      allows_harvest: true,
      harvest_pattern: 'continuous',
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ harvest_months: [5, 6] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });

    const endHandle = screen.getByLabelText(
      i18n.t('pages.species.barResizeEndAriaLabel', {
        kind: i18n.t('pages.species.barKind.harvest'),
      }),
    );

    fireEvent.pointerDown(endHandle, { pointerId: 1, clientX: 100 });
    // The grid parent carries the pointer-move/up handlers.
    const grid = endHandle.closest('[style*="grid"]') ?? endHandle.parentElement!;
    fireEvent.pointerMove(grid, { pointerId: 1, clientX: 40 });
    fireEvent.pointerUp(grid, { pointerId: 1, clientX: 40 });

    // The live region has been populated with a range announcement.
    const live = screen.getByTestId('bar-live-0-harvest');
    expect(within(live).getByText(/–|Mai|Jun/)).toBeInTheDocument();
  });
});
