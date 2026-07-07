import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesCropRotationTab from '@/pages/stammdaten/species-detail/SpeciesCropRotationTab';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { BotanicalFamily, RotationSuccessor } from '@/api/types';

const FAMILY_URL = '/api/v1/botanical-families/fam-1';
const SUCCESSORS_URL = '/api/v1/crop-rotation/families/fam-1/successors';

function makeFamily(overrides: Partial<BotanicalFamily> = {}): BotanicalFamily {
  return {
    key: 'fam-1',
    name: 'Solanaceae',
    common_name_de: 'Nachtschattengewächse',
    common_name_en: 'Nightshades',
    order: 'Solanales',
    description: '',
    typical_nutrient_demand: 'high',
    nitrogen_fixing: false,
    typical_root_depth: 'medium',
    soil_ph_preference: null,
    frost_tolerance: 'tender',
    typical_growth_forms: [],
    common_pests: [],
    common_diseases: [],
    pollination_type: [],
    rotation_category: 'fruit',
    species_count: 3,
    created_at: null,
    updated_at: null,
    ...overrides,
  } as BotanicalFamily;
}

function makeSuccessor(overrides: Partial<RotationSuccessor> = {}): RotationSuccessor {
  return {
    family_key: 'fam-2',
    name: 'Fabaceae',
    wait_years: 3,
    benefit_score: 0.8,
    benefit_reason: 'Stickstoffanreicherung',
    ...overrides,
  };
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('SpeciesCropRotationTab', () => {
  it('shows the no-family alert when the species has no family', () => {
    renderWithProviders(<SpeciesCropRotationTab familyKey={null} fullScreen={false} />);
    expect(screen.getByTestId('no-family-alert')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.species.noFamilyForCropRotation'))).toBeInTheDocument();
  });

  it('renders the family card and successor cards with wait-year chips', async () => {
    server.use(
      http.get(FAMILY_URL, () => HttpResponse.json(makeFamily())),
      http.get(SUCCESSORS_URL, () =>
        HttpResponse.json([
          makeSuccessor({ family_key: 'fam-2', name: 'Fabaceae', wait_years: 1, benefit_reason: 'Stickstoffanreicherung' }),
          makeSuccessor({ family_key: 'fam-3', name: 'Brassicaceae', wait_years: 3, benefit_reason: 'Bodenlockerung' }),
          makeSuccessor({ family_key: 'fam-4', name: 'Apiaceae', wait_years: 5, benefit_reason: 'Schädlingsunterbrechung' }),
        ]),
      ),
    );
    renderWithProviders(<SpeciesCropRotationTab familyKey="fam-1" fullScreen={false} />);

    // Family name from the loaded family.
    expect(await screen.findByText('Solanaceae')).toBeInTheDocument();
    expect(screen.getByText('Nachtschattengewächse')).toBeInTheDocument();
    // Successors.
    expect(await screen.findByText('Fabaceae')).toBeInTheDocument();
    expect(screen.getByText('Brassicaceae')).toBeInTheDocument();
    expect(screen.getByText('Apiaceae')).toBeInTheDocument();
    expect(screen.getByText('Stickstoffanreicherung')).toBeInTheDocument();
    // Wait-year chips reflect the three colour branches (1 / 3 / 5 years).
    expect(screen.getByText(`1 ${i18n.t('pages.cropRotation.waitYears')}`)).toBeInTheDocument();
    expect(screen.getByText(`5 ${i18n.t('pages.cropRotation.waitYears')}`)).toBeInTheDocument();
  });

  it('shows the successors empty state when there are none', async () => {
    server.use(
      http.get(FAMILY_URL, () => HttpResponse.json(makeFamily())),
      http.get(SUCCESSORS_URL, () => HttpResponse.json([])),
    );
    renderWithProviders(<SpeciesCropRotationTab familyKey="fam-1" fullScreen={false} />);

    expect(await screen.findByText(i18n.t('pages.cropRotation.noSuccessors'))).toBeInTheDocument();
  });

  it('opens the dialog, loads families and adds a successor', async () => {
    let posted: Record<string, unknown> | null = null;
    server.use(
      http.get(FAMILY_URL, () => HttpResponse.json(makeFamily())),
      http.get(SUCCESSORS_URL, () => HttpResponse.json([])),
      http.get('/api/v1/botanical-families', () =>
        HttpResponse.json([
          makeFamily({ key: 'fam-1', name: 'Solanaceae' }),
          makeFamily({ key: 'fam-2', name: 'Fabaceae' }),
        ]),
      ),
      http.post('/api/v1/crop-rotation/successors', async ({ request }) => {
        posted = (await request.json()) as Record<string, unknown>;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderWithProviders(<SpeciesCropRotationTab familyKey="fam-1" fullScreen={false} />);

    await screen.findByText(i18n.t('pages.cropRotation.noSuccessors'));
    await userEvent.click(screen.getByTestId('add-successor-button'));

    const dialog = await screen.findByRole('dialog');
    // The current family (fam-1) is filtered out; only Fabaceae is selectable.
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Fabaceae' }));

    await userEvent.click(within(dialog).getByRole('button', { name: i18n.t('common.create') }));

    await waitFor(() =>
      expect(posted).toMatchObject({ from_family_key: 'fam-1', to_family_key: 'fam-2' }),
    );
  });

  it('disables the create button until a target family is chosen', async () => {
    server.use(
      http.get(FAMILY_URL, () => HttpResponse.json(makeFamily())),
      http.get(SUCCESSORS_URL, () => HttpResponse.json([])),
      http.get('/api/v1/botanical-families', () =>
        HttpResponse.json([makeFamily({ key: 'fam-2', name: 'Fabaceae' })]),
      ),
    );
    renderWithProviders(<SpeciesCropRotationTab familyKey="fam-1" fullScreen={false} />);

    await screen.findByText(i18n.t('pages.cropRotation.noSuccessors'));
    await userEvent.click(screen.getByTestId('add-successor-button'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: i18n.t('common.create') })).toBeDisabled();

    await userEvent.click(within(dialog).getByRole('button', { name: i18n.t('common.cancel') }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });
});
