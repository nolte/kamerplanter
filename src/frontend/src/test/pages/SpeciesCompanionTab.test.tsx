import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesCompanionTab from '@/pages/stammdaten/species-detail/SpeciesCompanionTab';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { CompatibleSpecies, IncompatibleSpecies } from '@/api/types';

const COMPAT_URL = '/api/v1/companion-planting/species/sp-1/compatible';
const INCOMPAT_URL = '/api/v1/companion-planting/species/sp-1/incompatible';

/** A minimal species-list handler with two selectable targets. */
function speciesListHandler() {
  return http.get('/api/v1/species', () =>
    HttpResponse.json({
      items: [
        { key: 'sp-1', scientific_name: 'Solanum lycopersicum' },
        { key: 'sp-2', scientific_name: 'Ocimum basilicum' },
        { key: 'sp-3', scientific_name: 'Brassica oleracea' },
      ],
      total: 3,
      offset: 0,
      limit: 200,
    }),
  );
}

function setupRelations(compatible: CompatibleSpecies[], incompatible: IncompatibleSpecies[]) {
  server.use(
    speciesListHandler(),
    http.get(COMPAT_URL, () => HttpResponse.json(compatible)),
    http.get(INCOMPAT_URL, () => HttpResponse.json(incompatible)),
  );
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('SpeciesCompanionTab', () => {
  it('renders empty states for both relation columns', async () => {
    setupRelations([], []);
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );

    expect(await screen.findByText(i18n.t('pages.companionPlanting.noCompatible'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.companionPlanting.noIncompatible'))).toBeInTheDocument();
  });

  it('renders compatible and incompatible relations with count chips', async () => {
    setupRelations(
      [{ species_key: 'sp-2', scientific_name: 'Ocimum basilicum', score: 0.9 }],
      [{ species_key: 'sp-3', scientific_name: 'Brassica oleracea', reason: 'Nährstoffkonkurrenz' }],
    );
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );

    expect(await screen.findByText('Ocimum basilicum')).toBeInTheDocument();
    expect(screen.getByText('Brassica oleracea')).toBeInTheDocument();
    expect(screen.getByText('Nährstoffkonkurrenz')).toBeInTheDocument();
    expect(screen.getByText(`${i18n.t('pages.companionPlanting.score')}: 0.9`)).toBeInTheDocument();
  });

  it('falls back to the species key when the scientific name is missing', async () => {
    setupRelations([{ species_key: 'sp-9', scientific_name: null, score: 0.5 }], []);
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );
    expect(await screen.findByText('sp-9')).toBeInTheDocument();
  });

  it('adds a compatible relation via the dialog', async () => {
    let posted: Record<string, unknown> | null = null;
    setupRelations([], []);
    server.use(
      http.post('/api/v1/companion-planting/compatible', async ({ request }) => {
        posted = (await request.json()) as Record<string, unknown>;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );

    await screen.findByText(i18n.t('pages.companionPlanting.noCompatible'));
    await userEvent.click(screen.getByTestId('add-compatible-button'));

    const dialog = await screen.findByRole('dialog');
    // Open the species select and pick a target.
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Ocimum basilicum' }));

    await userEvent.click(within(dialog).getByRole('button', { name: i18n.t('common.create') }));

    await waitFor(() =>
      expect(posted).toMatchObject({ from_species_key: 'sp-1', to_species_key: 'sp-2' }),
    );
  });

  it('adds an incompatible relation with a reason via the dialog', async () => {
    let posted: Record<string, unknown> | null = null;
    setupRelations([], []);
    server.use(
      http.post('/api/v1/companion-planting/incompatible', async ({ request }) => {
        posted = (await request.json()) as Record<string, unknown>;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );

    await screen.findByText(i18n.t('pages.companionPlanting.noIncompatible'));
    await userEvent.click(screen.getByTestId('add-incompatible-button'));

    const dialog = await screen.findByRole('dialog');
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Brassica oleracea' }));

    await userEvent.type(within(dialog).getByTestId('reason-input').querySelector('textarea')!, 'Konkurrenz');
    await userEvent.click(within(dialog).getByRole('button', { name: i18n.t('common.create') }));

    await waitFor(() =>
      expect(posted).toMatchObject({ from_species_key: 'sp-1', to_species_key: 'sp-3' }),
    );
  });

  it('disables the create button until a target species is selected', async () => {
    setupRelations([], []);
    renderWithProviders(
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />,
    );
    await screen.findByText(i18n.t('pages.companionPlanting.noCompatible'));
    await userEvent.click(screen.getByTestId('add-compatible-button'));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('button', { name: i18n.t('common.create') })).toBeDisabled();

    // Cancel closes the dialog.
    await userEvent.click(within(dialog).getByRole('button', { name: i18n.t('common.cancel') }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });
});
