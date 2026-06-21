import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import TreatmentDetailPage from '@/pages/pflanzenschutz/TreatmentDetailPage';
import { renderWithProviders } from '../helpers';
import type { TreatmentDetail, Treatment } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 't1' }), useNavigate: () => mockNavigate };
});

vi.mock('@/api/endpoints/ipm', () => ({ getTreatmentDetail: vi.fn() }));
import { getTreatmentDetail } from '@/api/endpoints/ipm';

function makeTreatment(overrides: Partial<Treatment> = {}): Treatment {
  return {
    key: 't1',
    name: 'Neem Oil',
    name_de: 'Niemöl',
    treatment_type: 'biological',
    active_ingredient: 'Azadirachtin',
    application_method: 'spray',
    safety_interval_days: 3,
    dosage_per_liter: 5,
    protective_equipment: ['gloves'],
    description: 'Botanical insecticide.',
    description_de: 'Pflanzliches Insektizid aus dem Niembaum.',
    how_to_apply: 'Spray on leaf undersides every 7 days.',
    how_to_apply_de: 'Alle 7 Tage auf die Blattunterseiten sprühen.',
    mode_of_action: 'Disrupts insect moulting.',
    mode_of_action_de: 'Stört die Häutung der Insekten.',
    precautions: 'Apply in the evening to protect bees.',
    precautions_de: 'Abends ausbringen, um Bienen zu schonen.',
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeDetail(overrides: Partial<TreatmentDetail> = {}): TreatmentDetail {
  return {
    treatment: makeTreatment(),
    targeted_pests: [
      { key: 'p1', common_name: 'Spider Mites', scientific_name: 'Tetranychus urticae' },
    ],
    targeted_diseases: [],
    ...overrides,
  };
}

describe('TreatmentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('renders the localized name (German) and type/Karenz chips', async () => {
    vi.mocked(getTreatmentDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    // useLocalizedField picks name_de under the German locale.
    expect(await screen.findByText('Niemöl')).toBeInTheDocument();
    expect(screen.getByTestId('treatment-detail-type')).toBeInTheDocument();
    expect(screen.getByTestId('treatment-detail-karenz')).toBeInTheDocument();
    expect(getTreatmentDetail).toHaveBeenCalledWith('t1');
  });

  it('renders the multilingual detail sections (German variants)', async () => {
    vi.mocked(getTreatmentDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    expect(await screen.findByTestId('treatment-how-to-apply')).toHaveTextContent(
      'Alle 7 Tage auf die Blattunterseiten sprühen.',
    );
    expect(screen.getByTestId('treatment-mode-of-action')).toHaveTextContent('Stört die Häutung der Insekten.');
    expect(screen.getByTestId('treatment-precautions')).toHaveTextContent('Abends ausbringen, um Bienen zu schonen.');
  });

  it('shows the key facts (active ingredient, application method)', async () => {
    vi.mocked(getTreatmentDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    await screen.findByText('Niemöl');
    expect(screen.getByText('Azadirachtin')).toBeInTheDocument();
  });

  it('links a targeted pest to its detail page', async () => {
    vi.mocked(getTreatmentDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    // Chip renders as a native <a> element via RouterLink — verify the href.
    const pestChip = await screen.findByTestId('treatment-target-pest');
    expect(pestChip.closest('a')).toHaveAttribute('href', '/pflanzenschutz/pests/p1');
  });

  it('falls back to the English name when no German variant exists', async () => {
    vi.mocked(getTreatmentDetail).mockResolvedValue(
      makeDetail({ treatment: makeTreatment({ name_de: null }) }),
    );
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    expect(await screen.findByText('Neem Oil')).toBeInTheDocument();
  });

  it('renders an error state when loading fails', async () => {
    vi.mocked(getTreatmentDetail).mockRejectedValue(new Error('boom'));
    renderWithProviders(<TreatmentDetailPage />, { route: '/pflanzenschutz/treatments/t1' });

    expect(await screen.findByTestId('treatment-detail-error')).toBeInTheDocument();
  });
});
