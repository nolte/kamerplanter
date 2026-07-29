import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import { useSearchParams } from 'react-router-dom';
import PestListPage from '@/pages/pflanzenschutz/PestListPage';
import { renderWithProviders, createTestStore } from '../helpers';
import type { Pest, PestDetectionStatus } from '@/api/types';

/** Renders the page plus a probe that mirrors the current URL query string. */
function PageWithUrlProbe() {
  const [params] = useSearchParams();
  return (
    <>
      <div data-testid="url-search">{params.toString()}</div>
      <PestListPage />
    </>
  );
}

// The page dispatches fetchPests + fetchPestDetectionStatus on mount. We stub
// both thunks with no-op action creators so the test drives state purely via the
// preloaded store (no MSW/network), then asserts the conditional REQ-044 marker.
vi.mock('@/store/slices/ipmSlice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/store/slices/ipmSlice')>();
  return { ...actual, fetchPests: () => ({ type: 'ipm/fetchPests/mock' }) };
});
vi.mock('@/store/slices/pestDetectionSlice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/store/slices/pestDetectionSlice')>();
  return {
    ...actual,
    fetchPestDetectionStatus: () => ({ type: 'pestDetection/fetchStatus/mock' }),
  };
});

function pest(key: string, overrides: Partial<Pest> = {}): Pest {
  return {
    key,
    scientific_name: 'Tetranychus urticae',
    common_name: 'Spider mite',
    common_name_de: 'Spinnmilbe',
    pest_type: 'mite',
    lifecycle_days: 14,
    optimal_temp_min: null,
    optimal_temp_max: null,
    detection_difficulty: 'hard',
    description: null,
    description_de: null,
    damage_symptoms: null,
    damage_symptoms_de: null,
    affected_plant_parts: [],
    host_plants: [],
    host_plants_de: [],
    prevention_tips: null,
    prevention_tips_de: null,
    monitoring_hints: null,
    monitoring_hints_de: null,
    severity: null,
    optimal_humidity_min: null,
    optimal_humidity_max: null,
    detection_slug: 'spider_mite',
    reference_image_refs: [],
    has_reference_images: false,
    reference_image_count: 0,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function status(available: boolean): PestDetectionStatus {
  return {
    available,
    feature_enabled: available,
    primary_adapter: 'local',
    active_adapter: available ? 'local' : null,
    adapters: {},
  };
}

function storeWith(pests: Pest[], detectionStatus: PestDetectionStatus | null) {
  return createTestStore({
    ipm: {
      pests,
      loading: false,
      error: null,
    },
    pestDetection: {
      status: detectionStatus,
      statusLoading: false,
      result: null,
      detecting: false,
      history: [],
      historyLoading: false,
      error: null,
      errorCode: null,
    },
  });
}

describe('PestListPage — REQ-044 reference-image marker', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the recognition marker when detection is enabled and images exist', async () => {
    const store = storeWith(
      [pest('p-mite', { has_reference_images: true, reference_image_count: 30 })],
      status(true),
    );
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => {
      expect(screen.getAllByText('Spinnmilbe').length).toBeGreaterThan(0);
    });
    expect(screen.getAllByTestId('recognition-chip').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Erkennung verfügbar').length).toBeGreaterThan(0);
  });

  it('hides the marker for a pest without reference images', async () => {
    const store = storeWith(
      [pest('p-mite', { has_reference_images: false, reference_image_count: 0 })],
      status(true),
    );
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => {
      expect(screen.getAllByText('Spinnmilbe').length).toBeGreaterThan(0);
    });
    // The column header exists (feature enabled) but no row chip is rendered.
    expect(screen.queryByTestId('recognition-chip')).toBeNull();
  });

  it('never shows the marker when pest detection is disabled', async () => {
    const store = storeWith(
      [pest('p-mite', { has_reference_images: true, reference_image_count: 30 })],
      status(false),
    );
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => {
      expect(screen.getAllByText('Spinnmilbe').length).toBeGreaterThan(0);
    });
    expect(screen.queryByTestId('recognition-chip')).toBeNull();
    // The column header must not appear either when the feature is off.
    expect(screen.queryByText('Bilderkennung')).toBeNull();
  });
});

describe('PestListPage — origin column removed', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('no longer renders the "Herkunft" origin column header', async () => {
    const store = storeWith([pest('p1')], status(false));
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => {
      expect(screen.getAllByText('Spinnmilbe').length).toBeGreaterThan(0);
    });
    // The origin column header used the common.origin.filterLabel ("Herkunft").
    // It must not appear as a column header anymore.
    const columnHeaders = screen.queryAllByRole('columnheader');
    expect(columnHeaders.some((h) => /Herkunft/.test(h.textContent ?? ''))).toBe(false);
  });
});

describe('PestListPage — column filters with URL state', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  const rows = [
    pest('p-mite', {
      scientific_name: 'Tetranychus urticae',
      common_name_de: 'Spinnmilbe',
      pest_type: 'arachnid',
      detection_difficulty: 'hard',
    }),
    pest('p-aphid', {
      scientific_name: 'Aphis fabae',
      common_name_de: 'Blattlaus',
      pest_type: 'insect',
      detection_difficulty: 'easy',
    }),
    pest('p-snail', {
      scientific_name: 'Helix pomatia',
      common_name_de: 'Weinbergschnecke',
      pest_type: 'gastropod',
      detection_difficulty: 'easy',
    }),
  ];

  /** Opens a multi-select filter and toggles a single option by its label. */
  async function pickOption(user: ReturnType<typeof userEvent.setup>, filterId: string, optionLabel: string) {
    const control = screen.getByTestId(`column-filter-${filterId}`);
    const trigger = within(control).getByRole('combobox');
    await user.click(trigger);
    const listbox = await screen.findByRole('listbox');
    await user.click(within(listbox).getByRole('option', { name: new RegExp(optionLabel) }));
    // Close the menu so subsequent queries are unambiguous.
    await user.keyboard('{Escape}');
  }

  it('filters rows client-side by pest type (multi-select)', async () => {
    const user = userEvent.setup();
    const store = storeWith(rows, status(false));
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => expect(screen.getByText('Spinnmilbe')).toBeInTheDocument());

    await pickOption(user, 'pest_type', 'Insekt');
    await pickOption(user, 'pest_type', 'Schnecke');

    // Only insect + gastropod rows remain; the arachnid (mite) is filtered out.
    await waitFor(() => expect(screen.queryByText('Spinnmilbe')).toBeNull());
    expect(screen.getByText('Blattlaus')).toBeInTheDocument();
    expect(screen.getByText('Weinbergschnecke')).toBeInTheDocument();
  });

  it('serialises active filters into URL query params', async () => {
    const user = userEvent.setup();
    const store = storeWith(rows, status(false));
    renderWithProviders(<PageWithUrlProbe />, { store });

    await waitFor(() => expect(screen.getByText('Spinnmilbe')).toBeInTheDocument());

    await pickOption(user, 'pest_type', 'Insekt');
    await pickOption(user, 'difficulty', 'Einfach');

    await waitFor(() => {
      const search = screen.getByTestId('url-search').textContent ?? '';
      const params = new URLSearchParams(search);
      expect(params.get('pest_type')).toBe('insect');
      expect(params.get('difficulty')).toBe('easy');
    });
  });

  it('rehydrates filters from the URL on initial load (multi-value)', async () => {
    const store = storeWith(rows, status(false));
    renderWithProviders(<PageWithUrlProbe />, {
      store,
      route: '/?pest_type=insect,gastropod',
    });

    await waitFor(() => expect(screen.getByText('Blattlaus')).toBeInTheDocument());
    // Mite (arachnid) is excluded by the rehydrated filter; the two selected
    // types are visible — proving the comma-separated multi-value round-trip.
    expect(screen.queryByText('Spinnmilbe')).toBeNull();
    expect(screen.getByText('Weinbergschnecke')).toBeInTheDocument();
  });

  it('clears column filters (and their URL params) via the clear button', async () => {
    const user = userEvent.setup();
    const store = storeWith(rows, status(false));
    renderWithProviders(<PageWithUrlProbe />, {
      store,
      route: '/?pest_type=insect',
    });

    await waitFor(() => expect(screen.getByText('Blattlaus')).toBeInTheDocument());
    expect(screen.queryByText('Spinnmilbe')).toBeNull();

    await user.click(screen.getByTestId('clear-column-filters-button'));

    await waitFor(() => expect(screen.getByText('Spinnmilbe')).toBeInTheDocument());
    const params = new URLSearchParams(screen.getByTestId('url-search').textContent ?? '');
    expect(params.get('pest_type')).toBeNull();
  });

  it('offers the recognition filter only when detection is enabled', async () => {
    const store = storeWith(rows, status(true));
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => expect(screen.getByText('Spinnmilbe')).toBeInTheDocument());
    expect(screen.getByTestId('column-filter-recognition')).toBeInTheDocument();
  });

  it('hides the recognition filter when detection is disabled', async () => {
    const store = storeWith(rows, status(false));
    renderWithProviders(<PestListPage />, { store });

    await waitFor(() => expect(screen.getByText('Spinnmilbe')).toBeInTheDocument());
    expect(screen.queryByTestId('column-filter-recognition')).toBeNull();
  });
});
