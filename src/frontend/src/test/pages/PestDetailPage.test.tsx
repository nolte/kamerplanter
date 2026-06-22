import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import PestDetailPage from '@/pages/pflanzenschutz/PestDetailPage';
import { renderWithProviders } from '../helpers';
import type { PestDetail, Pest, Treatment } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'p1' }), useNavigate: () => mockNavigate };
});

vi.mock('@/api/endpoints/ipm', () => ({ getPestDetail: vi.fn() }));
import { getPestDetail } from '@/api/endpoints/ipm';

// The gallery is a self-contained component (own tenant-scoped API + own tests).
vi.mock('@/components/pests/PestImageGallery', () => ({
  default: () => <div data-testid="pest-image-gallery-stub" />,
}));

function makePest(overrides: Partial<Pest> = {}): Pest {
  return {
    key: 'p1',
    scientific_name: 'Tetranychus urticae',
    common_name: 'Spinnmilbe',
    common_name_de: null,
    pest_type: 'arachnid',
    lifecycle_days: 21,
    optimal_temp_min: 25,
    optimal_temp_max: 30,
    detection_difficulty: 'medium',
    description: 'Saugende Milbe.',
    description_de: null,
    damage_symptoms: 'Helle Sprenkelung der Blattoberseite.',
    damage_symptoms_de: null,
    affected_plant_parts: ['leaf', 'stem'],
    host_plants: ['Gurke', 'Bohne'],
    host_plants_de: [],
    prevention_tips: 'Luftfeuchte hoch halten.',
    prevention_tips_de: null,
    monitoring_hints: 'Blattunterseiten mit Lupe prüfen.',
    monitoring_hints_de: null,
    severity: 'high',
    optimal_humidity_min: 30,
    optimal_humidity_max: 50,
    detection_slug: 'spider_mite',
    reference_image_refs: [],
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeTreatment(overrides: Partial<Treatment> = {}): Treatment {
  return {
    key: 't1',
    name: 'Treatment',
    name_de: null,
    treatment_type: 'biological',
    active_ingredient: null,
    application_method: 'spray',
    safety_interval_days: 0,
    dosage_per_liter: null,
    protective_equipment: [],
    description: null,
    description_de: null,
    how_to_apply: null,
    how_to_apply_de: null,
    mode_of_action: null,
    mode_of_action_de: null,
    precautions: null,
    precautions_de: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeDetail(overrides: Partial<PestDetail> = {}): PestDetail {
  return {
    pest: makePest(),
    treatments: [
      makeTreatment({ key: 't1', name: 'Environmental Control', treatment_type: 'cultural' }),
      makeTreatment({ key: 't2', name: 'Pyrethrin', treatment_type: 'chemical', active_ingredient: 'Pyrethrin', safety_interval_days: 7 }),
    ],
    beneficials: [
      { key: 'b1', slug: 'ladybird', common_name: 'Marienkäfer', scientific_name: 'Coccinellidae', description: null, preys_on: ['spider_mite'] },
    ],
    detection_symptom_hint: 'Feine Gespinste an der Blattunterseite.',
    ...overrides,
  };
}

describe('PestDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('renders the pest profile with name, severity and symptoms', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    expect(await screen.findByText('Spinnmilbe')).toBeInTheDocument();
    expect(screen.getByText('Tetranychus urticae')).toBeInTheDocument();
    expect(screen.getByTestId('pest-detail-severity')).toBeInTheDocument();
    // damage_symptoms is shown in the profile section.
    expect(screen.getByText('Helle Sprenkelung der Blattoberseite.')).toBeInTheDocument();
    expect(getPestDetail).toHaveBeenCalledWith('p1');
  });

  it('groups countermeasures by IPM tier and shows the Karenz chip', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    await screen.findByTestId('pest-detail-treatments');
    expect(screen.getByTestId('treatment-group-cultural')).toBeInTheDocument();
    expect(screen.getByTestId('treatment-group-chemical')).toBeInTheDocument();
    expect(screen.getByText('Environmental Control')).toBeInTheDocument();
    expect(screen.getByText('Pyrethrin')).toBeInTheDocument();
    // Chemical treatment exposes its pre-harvest interval (Karenz).
    expect(screen.getByTestId('treatment-karenz')).toBeInTheDocument();
  });

  it('lists matching beneficial organisms', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    await screen.findByTestId('pest-detail-beneficials');
    expect(screen.getByText('Marienkäfer')).toBeInTheDocument();
  });

  it('renders an error state when loading fails', async () => {
    vi.mocked(getPestDetail).mockRejectedValue(new Error('boom'));
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    expect(await screen.findByTestId('pest-detail-error')).toBeInTheDocument();
  });

  it('navigates back to the pest list', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(makeDetail());
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    const back = await screen.findByTestId('pest-detail-back');
    await userEvent.click(back);
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/pflanzenschutz/pests'));
  });

  it('shows the German common name in the title under the German locale', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(
      makeDetail({ pest: makePest({ common_name: 'Fungus Gnats', common_name_de: 'Trauermücken' }) }),
    );
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    expect(await screen.findByText('Trauermücken')).toBeInTheDocument();
    expect(screen.queryByText('Fungus Gnats')).toBeNull();
  });

  it('shows the German variant of a profile field under the German locale', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(
      makeDetail({
        pest: makePest({
          damage_symptoms: 'Light speckling on the leaf surface.',
          damage_symptoms_de: 'Helle Sprenkelung der Blattoberseite (DE).',
        }),
      }),
    );
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    // i18n is set to 'de' in beforeEach → the _de variant wins.
    expect(await screen.findByText('Helle Sprenkelung der Blattoberseite (DE).')).toBeInTheDocument();
    expect(screen.queryByText('Light speckling on the leaf surface.')).toBeNull();
  });

  it('shows a localized summary explaining how each countermeasure works', async () => {
    vi.mocked(getPestDetail).mockResolvedValue(
      makeDetail({
        treatments: [
          makeTreatment({
            key: 't1',
            name: 'Neem Oil',
            name_de: 'Niemöl',
            treatment_type: 'biological',
            description_de: 'Pflanzliches Insektizid, das die Häutung stört.',
          }),
        ],
      }),
    );
    renderWithProviders(<PestDetailPage />, { route: '/pflanzenschutz/pests/p1' });

    const summary = await screen.findByTestId('treatment-summary');
    expect(summary).toHaveTextContent('Pflanzliches Insektizid, das die Häutung stört.');
  });
});
