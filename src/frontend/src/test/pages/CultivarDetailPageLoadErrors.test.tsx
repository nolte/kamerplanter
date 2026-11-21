/**
 * #3037 SCR-003/SCR-004 — CultivarDetailPage load errors.
 *
 * - A retry after a failed first load shows the page (`load()` clears the error).
 * - The growth-phase section retry re-reads only the lifecycle, so unsaved form
 *   input survives it (no skeleton, no `reset`).
 */
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Cultivar, Species } from '@/api/types';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ speciesKey: 'sp-1', cultivarKey: 'cv-1' }),
    useNavigate: () => vi.fn(),
  };
});

const getCultivar = vi.fn();
const getSpecies = vi.fn();
vi.mock('@/api/endpoints/species', () => ({
  getCultivar: (...args: unknown[]) => getCultivar(...args),
  getSpecies: (...args: unknown[]) => getSpecies(...args),
  updateCultivar: vi.fn(),
  deleteCultivar: vi.fn(),
}));
const getLifecycleConfig = vi.fn();
const listGrowthPhases = vi.fn();
vi.mock('@/api/endpoints/phases', () => ({
  getLifecycleConfig: (...args: unknown[]) => getLifecycleConfig(...args),
  listGrowthPhases: (...args: unknown[]) => listGrowthPhases(...args),
}));

import CultivarDetailPage from '@/pages/stammdaten/CultivarDetailPage';
import { renderWithProviders } from '../helpers';

function makeCultivar(overrides: Partial<Cultivar> = {}): Cultivar {
  return {
    key: 'cv-1',
    name: 'Gala',
    species_key: 'sp-1',
    breeder: null,
    breeding_year: null,
    traits: [],
    patent_status: '',
    seed_type: null,
    days_to_maturity: 150,
    dtm_reference: 'transplant',
    bearing_start_year_min: 3,
    bearing_start_year_max: 5,
    disease_resistances: [],
    phase_watering_overrides: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeSpecies(): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Malus domestica',
    common_names: [],
    family_key: null,
    family_name: null,
    genus: 'Malus',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'tree',
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
  };
}

describe('CultivarDetailPage — load errors (#3037)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    getCultivar.mockReset();
    getSpecies.mockReset();
    getLifecycleConfig.mockReset();
    listGrowthPhases.mockReset();
    getSpecies.mockResolvedValue(makeSpecies());
    listGrowthPhases.mockResolvedValue([]);
  });

  it('shows the page after a successful retry of a failed first load', async () => {
    getCultivar.mockRejectedValueOnce(new Error('boom')).mockResolvedValue(makeCultivar());
    getLifecycleConfig.mockResolvedValue({ key: 'lc-1' });
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />);

    await user.click(await screen.findByTestId('error-retry-button'));

    expect(await screen.findByTestId('cultivar-detail-page')).toBeInTheDocument();
    expect(screen.queryByTestId('error-display')).toBeNull();
    expect(getCultivar).toHaveBeenCalledTimes(2);
  });

  it('keeps unsaved input when the growth-phase section is retried', async () => {
    getCultivar.mockResolvedValue(makeCultivar());
    getLifecycleConfig.mockRejectedValueOnce(new Error('boom')).mockResolvedValue({ key: 'lc-1' });
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />);

    const retry = await screen.findByTestId('cultivar-growth-phases-load-error-retry');
    const name = within(screen.getByTestId('form-field-name')).getByRole('textbox');
    await user.clear(name);
    await user.type(name, 'Elstar');

    await user.click(retry);

    await waitFor(() => expect(getLifecycleConfig).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.queryByTestId('cultivar-growth-phases-load-error')).toBeNull(),
    );
    expect(within(screen.getByTestId('form-field-name')).getByRole('textbox')).toHaveValue('Elstar');
    // Only the section was re-read, not the cultivar.
    expect(getCultivar).toHaveBeenCalledTimes(1);
  });
});
