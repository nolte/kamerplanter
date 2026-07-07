import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { Cultivar } from '@/api/types';

// Force the mobile breakpoint so DataTable uses the mobileCardRenderer branch.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

// Import after the mock so the mocked useMediaQuery is picked up.
import CultivarListSection from '@/pages/stammdaten/CultivarListSection';

const CULTIVARS_URL = '/api/v1/species/sp-1/cultivars';

function makeCultivar(overrides: Partial<Cultivar> = {}): Cultivar {
  return {
    key: 'cv-1',
    name: 'Sungold',
    species_key: 'sp-1',
    breeder: 'Tozer',
    breeding_year: 1992,
    traits: [],
    patent_status: '',
    days_to_maturity: 65,
    dtm_reference: null,
    bearing_start_year_min: null,
    bearing_start_year_max: null,
    disease_resistances: [],
    phase_watering_overrides: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('CultivarListSection — mobile card renderer', () => {
  it('renders mobile cards with trait chips and the maturity field', async () => {
    server.use(
      http.get(CULTIVARS_URL, () =>
        HttpResponse.json([
          makeCultivar({ key: 'cv-1', name: 'Sungold', traits: ['compact'], days_to_maturity: 65 }),
          // No traits and no maturity → the undefined branches of the renderer.
          makeCultivar({ key: 'cv-2', name: 'Roma', breeder: null, traits: [], days_to_maturity: null }),
        ]),
      ),
    );
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    expect(await screen.findByTestId('data-table-cards')).toBeInTheDocument();
    expect(screen.getByText('Sungold')).toBeInTheDocument();
    expect(screen.getByText('Roma')).toBeInTheDocument();
    // Trait chip in the mobile card.
    expect(screen.getByText(i18n.t('enums.plantTrait.compact'))).toBeInTheDocument();
    // Maturity field label rendered for the cultivar that has a value.
    expect(screen.getByText(i18n.t('pages.cultivars.daysToMaturity'))).toBeInTheDocument();
  });
});
