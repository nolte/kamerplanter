import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import CompanionPlantingPage from '@/pages/stammdaten/CompanionPlantingPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Two species: one with curated companion relationships, one with none (0/0).
const SPECIES = [
  { key: 'sp-tomato', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'], genus: 'Solanum' },
  { key: 'sp-lonely', scientific_name: 'Rara planta', common_names: [], genus: 'Rara' },
];

function mockSpeciesAndCounts(counts: Record<string, { compatible: number; incompatible: number }>) {
  server.use(
    http.get('/api/v1/species', () =>
      HttpResponse.json({ items: SPECIES, total: SPECIES.length, offset: 0, limit: 200 }),
    ),
    http.get('/api/v1/companion-planting/counts', () => HttpResponse.json(counts)),
  );
}

/** Records the POST bodies the write endpoints receive, for assertion. */
function mockRelationEndpoints(): {
  compatible: unknown[];
  incompatible: unknown[];
  posted: Record<string, unknown>[];
} {
  const state = {
    compatible: [] as unknown[],
    incompatible: [] as unknown[],
    posted: [] as Record<string, unknown>[],
  };
  server.use(
    http.get('/api/v1/companion-planting/species/:key/compatible', () =>
      HttpResponse.json(state.compatible),
    ),
    http.get('/api/v1/companion-planting/species/:key/incompatible', () =>
      HttpResponse.json(state.incompatible),
    ),
    http.post('/api/v1/companion-planting/compatible', async ({ request }) => {
      state.posted.push((await request.json()) as Record<string, unknown>);
      return HttpResponse.json({ status: 'created' }, { status: 201 });
    }),
    http.post('/api/v1/companion-planting/incompatible', async ({ request }) => {
      state.posted.push((await request.json()) as Record<string, unknown>);
      return HttpResponse.json({ status: 'created' }, { status: 201 });
    }),
  );
  return state;
}

async function openDropdown(): Promise<void> {
  const combobox = await screen.findByRole('combobox');
  await userEvent.click(combobox);
}

async function selectSpecies(name: string | RegExp): Promise<void> {
  await openDropdown();
  await userEvent.click(await screen.findByRole('option', { name }));
}

describe('CompanionPlantingPage species dropdown counts', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
    mockSpeciesAndCounts({ 'sp-tomato': { compatible: 5, incompatible: 2 } });
  });

  it('renders a compatible + incompatible count chip per option', async () => {
    renderWithProviders(<CompanionPlantingPage />);
    await openDropdown();

    await screen.findByTestId('species-option-sp-tomato');
    await waitFor(() =>
      expect(screen.getByTestId('species-option-compatible-sp-tomato')).toHaveTextContent('5'),
    );
    expect(screen.getByTestId('species-option-incompatible-sp-tomato')).toHaveTextContent('2');
  });

  it('de-emphasizes species with no curated relationships and shows explicit zeros', async () => {
    renderWithProviders(<CompanionPlantingPage />);
    await openDropdown();

    const tomato = await screen.findByTestId('species-option-sp-tomato');
    const lonely = screen.getByTestId('species-option-sp-lonely');
    expect(tomato).toHaveAttribute('data-has-relations', 'true');
    expect(lonely).toHaveAttribute('data-has-relations', 'false');
    // The 0/0 species still surfaces explicit zero counts (not just muted colour).
    expect(screen.getByTestId('species-option-compatible-sp-lonely')).toHaveTextContent('0');
    expect(screen.getByTestId('species-option-incompatible-sp-lonely')).toHaveTextContent('0');
  });

  it('carries the counts in the option accessible name, not colour alone', async () => {
    renderWithProviders(<CompanionPlantingPage />);
    await openDropdown();

    const option = await screen.findByRole('option', { name: /Solanum lycopersicum/ });
    await waitFor(() => expect(option).toHaveAccessibleName(/5 compatible, 2 incompatible/));
  });

  it('loads and renders the compatible + incompatible cards after selection', async () => {
    const state = mockRelationEndpoints();
    state.compatible = [{ species_key: 'sp-lonely', scientific_name: 'Rara planta', score: 0.8 }];
    state.incompatible = [{ species_key: 'sp-x', scientific_name: 'Bad plant', reason: 'allelopathy' }];

    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    expect(await screen.findByText('Rara planta')).toBeInTheDocument();
    expect(await screen.findByText('Bad plant')).toBeInTheDocument();
    expect(screen.getByText('allelopathy')).toBeInTheDocument();
  });

  it('adds a compatible relationship through the dialog', async () => {
    const state = mockRelationEndpoints();
    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    await userEvent.click(await screen.findByTestId('add-compatible-button'));
    const dialog = await screen.findByRole('dialog');
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Rara planta' }));
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create' }));

    await waitFor(() => expect(state.posted).toHaveLength(1));
    expect(state.posted[0]).toMatchObject({
      from_species_key: 'sp-tomato',
      to_species_key: 'sp-lonely',
    });
  });

  it('adds an incompatible relationship with a reason through the dialog', async () => {
    const state = mockRelationEndpoints();
    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    await userEvent.click(await screen.findByTestId('add-incompatible-button'));
    const dialog = await screen.findByRole('dialog');
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Rara planta' }));
    const reasonInput = within(dialog).getByTestId('reason-input').querySelector('textarea');
    await userEvent.type(reasonInput as HTMLTextAreaElement, 'shades out');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create' }));

    await waitFor(() => expect(state.posted).toHaveLength(1));
    expect(state.posted[0]).toMatchObject({
      from_species_key: 'sp-tomato',
      to_species_key: 'sp-lonely',
      reason: 'shades out',
    });
  });

  it('leads each dropdown option with the common name and keeps the scientific name secondary (#567)', async () => {
    renderWithProviders(<CompanionPlantingPage />);
    await openDropdown();

    const option = await screen.findByTestId('species-option-sp-tomato');
    // Common name (from common_names[0]) leads, scientific name stays as context.
    expect(option).toHaveTextContent('Tomato');
    expect(option).toHaveTextContent('Solanum lycopersicum');
  });

  it('renders each compatible species as a detail-page link, common name first (#567)', async () => {
    const state = mockRelationEndpoints();
    state.compatible = [
      {
        species_key: 'sp-leek',
        scientific_name: 'Allium porrum',
        common_names: ['Lauch', 'Leek'],
        score: 0.9,
      },
    ];
    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    const link = await screen.findByTestId('compatible-species-link-sp-leek');
    expect(link).toHaveTextContent('Lauch');
    expect(link).toHaveAttribute('href', '/stammdaten/species/sp-leek');
    // Scientific name still visible as secondary information.
    expect(screen.getByText('Allium porrum')).toBeInTheDocument();
  });

  it('renders each incompatible species as a detail-page link, common name first (#567)', async () => {
    const state = mockRelationEndpoints();
    state.incompatible = [
      {
        species_key: 'sp-fennel',
        scientific_name: 'Foeniculum vulgare',
        common_names: ['Fenchel'],
        reason: 'allelopathy',
      },
    ];
    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    const link = await screen.findByTestId('incompatible-species-link-sp-fennel');
    expect(link).toHaveTextContent('Fenchel');
    expect(link).toHaveAttribute('href', '/stammdaten/species/sp-fennel');
    expect(screen.getByText('Foeniculum vulgare')).toBeInTheDocument();
    expect(screen.getByText('allelopathy')).toBeInTheDocument();
  });

  it('closes the dialog on cancel without posting', async () => {
    const state = mockRelationEndpoints();
    renderWithProviders(<CompanionPlantingPage />);
    await selectSpecies(/Solanum lycopersicum/);

    await userEvent.click(await screen.findByTestId('add-compatible-button'));
    const dialog = await screen.findByRole('dialog');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(state.posted).toHaveLength(0);
  });
});
