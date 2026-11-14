import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from 'i18next';
import DiseaseListPage from '@/pages/pflanzenschutz/DiseaseListPage';
import type { Disease } from '@/api/types';
import { createTestStore, renderWithProviders } from '../helpers';

vi.mock('@/store/slices/ipmSlice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/store/slices/ipmSlice')>();
  return { ...actual, fetchDiseases: () => ({ type: 'ipm/fetchDiseases/mock' }) };
});

function disease(key: string, en: string, de: string): Disease {
  return {
    key,
    scientific_name: `Pathogen ${key}`,
    common_name: en,
    common_names_i18n: { en: [en], de: [de] },
    pathogen_type: 'fungal',
    incubation_period_days: null,
    environmental_triggers: [],
    affected_plant_parts: [],
    description: null,
    created_at: null,
    updated_at: null,
  };
}

// English order: Apple Scab, Fire Blight, Powdery Mildew. German order: Apfelschorf,
// Echter Mehltau, Feuerbrand — a sort by the stored (English) name would put
// Feuerbrand before Echter Mehltau in the German UI.
const DISEASES = [
  disease('d1', 'Powdery Mildew', 'Echter Mehltau'),
  disease('d2', 'Fire Blight', 'Feuerbrand'),
  disease('d3', 'Apple Scab', 'Apfelschorf'),
];

function renderList(query: string) {
  const store = createTestStore({
    ipm: {
      pests: [],
      diseases: DISEASES,
      treatments: [],
      inspections: [],
      applications: [],
      loading: false,
      error: null,
    },
  });
  return renderWithProviders(<DiseaseListPage />, { store, route: `/pflanzenschutz/diseases?${query}` });
}

/** The given names in the order they appear on the page. */
function orderOnPage(names: string[]): string[] {
  const text = screen.getByTestId('disease-list-page').textContent ?? '';
  return names.filter((name) => text.includes(name)).sort((a, b) => text.indexOf(a) - text.indexOf(b));
}

describe('DiseaseListPage — names in the UI language (#2936)', () => {
  afterEach(async () => {
    await i18n.changeLanguage('de');
  });

  it.each([
    ['de', ['Apfelschorf', 'Echter Mehltau', 'Feuerbrand']],
    ['en', ['Apple Scab', 'Fire Blight', 'Powdery Mildew']],
  ])('sorts the name column by the shown name (%s)', async (language, expected) => {
    await i18n.changeLanguage(language);
    renderList('sort=commonName&dir=asc');

    expect(orderOnPage(expected)).toEqual(expected);
  });

  it('finds a disease by its name in another language', async () => {
    await i18n.changeLanguage('en');
    renderList('q=mehltau');

    expect(screen.getByTestId('disease-list-page')).toHaveTextContent('Powdery Mildew');
    expect(screen.getByTestId('disease-list-page')).not.toHaveTextContent('Fire Blight');
  });

  it('does not match a query across two names', async () => {
    await i18n.changeLanguage('en');
    renderList('q=mildew%20echter');

    expect(screen.getByTestId('disease-list-page')).not.toHaveTextContent('Powdery Mildew');
  });
});
