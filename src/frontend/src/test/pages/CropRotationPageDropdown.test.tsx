import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import CropRotationPage from '@/pages/stammdaten/CropRotationPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Three families spanning the filter dimensions:
//  - Solanaceae: heavy feeder, not N-fixing, frost-sensitive, 2 successors
//  - Fabaceae:   medium feeder, N-fixing, frost-hardy, 0 successors (no rotation)
//  - Brassicaceae: light feeder, not N-fixing, frost-hardy, 1 successor
const FAMILIES = [
  {
    key: 'fam-solanaceae',
    name: 'Solanaceae',
    nitrogen_fixing: false,
    frost_tolerance: 'sensitive',
    typical_nutrient_demand: 'heavy',
  },
  {
    key: 'fam-fabaceae',
    name: 'Fabaceae',
    nitrogen_fixing: true,
    frost_tolerance: 'hardy',
    typical_nutrient_demand: 'medium',
  },
  {
    key: 'fam-brassicaceae',
    name: 'Brassicaceae',
    nitrogen_fixing: false,
    frost_tolerance: 'hardy',
    typical_nutrient_demand: 'light',
  },
];

// Fabaceae is intentionally absent → its count defaults to 0.
const COUNTS = { 'fam-solanaceae': 2, 'fam-brassicaceae': 1 };

function mockFamiliesAndCounts(): void {
  server.use(
    http.get('/api/v1/botanical-families', () => HttpResponse.json(FAMILIES)),
    http.get('/api/v1/crop-rotation/counts', () => HttpResponse.json(COUNTS)),
    // Rotation successors after a family is selected (kept empty here).
    http.get('/api/v1/crop-rotation/families/:key/successors', () => HttpResponse.json([])),
    // Favorites are user-global; accept both the tenant-scoped and bare paths so
    // the optimistic toggle never reverts regardless of the active slug.
    http.get('/api/v1/favorites', () => HttpResponse.json([])),
    http.get('/api/v1/t/:tenant/favorites', () => HttpResponse.json([])),
    http.post('/api/v1/favorites', () => HttpResponse.json({ status: 'created' }, { status: 201 })),
    http.post('/api/v1/t/:tenant/favorites', () =>
      HttpResponse.json({ status: 'created' }, { status: 201 }),
    ),
  );
}

function familyCombobox(): HTMLElement {
  // Two comboboxes exist (the family Autocomplete and the nutrient-demand Select);
  // scope to the Autocomplete's TextField root by test id.
  return within(screen.getByTestId('from-family-select')).getByRole('combobox');
}

async function openDropdown(): Promise<void> {
  await screen.findByTestId('from-family-select');
  await userEvent.click(familyCombobox());
}

async function optionNames(): Promise<string[]> {
  const options = await screen.findAllByRole('option');
  return options.map((o) => o.getAttribute('data-testid') ?? '');
}

describe('CropRotationPage family dropdown counts + filters', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
    mockFamiliesAndCounts();
  });

  it('renders a successor-count chip per family option, including an explicit 0', async () => {
    renderWithProviders(<CropRotationPage />);
    await openDropdown();

    await screen.findByTestId('family-option-fam-solanaceae');
    await waitFor(() =>
      expect(screen.getByTestId('family-option-count-fam-solanaceae')).toHaveTextContent('2'),
    );
    expect(screen.getByTestId('family-option-count-fam-brassicaceae')).toHaveTextContent('1');
    // Family with no rotation data still shows an explicit "0", not just muting.
    expect(screen.getByTestId('family-option-count-fam-fabaceae')).toHaveTextContent('0');
  });

  it('de-emphasizes families with no rotation data (still selectable)', async () => {
    renderWithProviders(<CropRotationPage />);
    await openDropdown();

    const solanaceae = await screen.findByTestId('family-option-fam-solanaceae');
    const fabaceae = screen.getByTestId('family-option-fam-fabaceae');
    expect(solanaceae).toHaveAttribute('data-has-rotation', 'true');
    expect(fabaceae).toHaveAttribute('data-has-rotation', 'false');
  });

  it('carries the successor count in the option accessible name, not colour alone', async () => {
    renderWithProviders(<CropRotationPage />);
    await openDropdown();

    const option = await screen.findByRole('option', { name: /Solanaceae/ });
    await waitFor(() =>
      expect(option).toHaveAccessibleName(/2 recommended successor families/),
    );
  });

  it('filters to families that have rotation data', async () => {
    renderWithProviders(<CropRotationPage />);
    await screen.findByTestId('filter-has-rotation');
    await userEvent.click(screen.getByTestId('filter-has-rotation'));
    await openDropdown();

    await waitFor(() => expect(screen.queryByTestId('family-option-fam-fabaceae')).toBeNull());
    const names = await optionNames();
    expect(names).toContain('family-option-fam-solanaceae');
    expect(names).toContain('family-option-fam-brassicaceae');
    expect(names).not.toContain('family-option-fam-fabaceae');
  });

  it('filters to nitrogen-fixing families', async () => {
    renderWithProviders(<CropRotationPage />);
    await screen.findByTestId('filter-nitrogen-fixing');
    await userEvent.click(screen.getByTestId('filter-nitrogen-fixing'));
    await openDropdown();

    const names = await optionNames();
    expect(names).toEqual(['family-option-fam-fabaceae']);
  });

  it('filters by nutrient demand (Zehrer / rotation category)', async () => {
    renderWithProviders(<CropRotationPage />);
    const select = await screen.findByTestId('filter-nutrient-demand');
    // MUI select renders a combobox button inside the TextField.
    await userEvent.click(within(select).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Heavy Feeder' }));
    await openDropdown();

    const names = await optionNames();
    expect(names).toEqual(['family-option-fam-solanaceae']);
  });

  it('favoriting a family scopes the favorites filter without selecting it', async () => {
    renderWithProviders(<CropRotationPage />);
    await openDropdown();

    const favBtn = await screen.findByTestId('family-favorite-fam-fabaceae');
    await userEvent.click(favBtn);

    // The star must NOT select the option — input stays empty (stopPropagation).
    expect(familyCombobox()).toHaveValue('');

    await userEvent.click(screen.getByTestId('filter-favorites'));
    await openDropdown();

    const names = await optionNames();
    expect(names).toEqual(['family-option-fam-fabaceae']);
  });

  it('loads successors after selecting a family', async () => {
    server.use(
      http.get('/api/v1/crop-rotation/families/fam-solanaceae/successors', () =>
        HttpResponse.json([
          { family_key: 'fam-fabaceae', name: 'Fabaceae', wait_years: 3, benefit_score: 0.8, benefit_reason: '' },
        ]),
      ),
    );
    renderWithProviders(<CropRotationPage />);
    await openDropdown();
    await userEvent.click(await screen.findByRole('option', { name: /Solanaceae/ }));

    expect(await screen.findByText('Fabaceae')).toBeInTheDocument();
    expect(screen.getByTestId('add-successor-button')).toBeInTheDocument();
  });

  it('adds a successor through the dialog and refreshes counts', async () => {
    const posted: Record<string, unknown>[] = [];
    let successorRows: unknown[] = [];
    server.use(
      http.get('/api/v1/crop-rotation/families/fam-solanaceae/successors', () =>
        HttpResponse.json(successorRows),
      ),
      http.post('/api/v1/crop-rotation/successors', async ({ request }) => {
        posted.push((await request.json()) as Record<string, unknown>);
        successorRows = [
          { family_key: 'fam-fabaceae', name: 'Fabaceae', wait_years: 3, benefit_score: 0, benefit_reason: '' },
        ];
        return HttpResponse.json({ status: 'created' }, { status: 201 });
      }),
    );

    renderWithProviders(<CropRotationPage />);
    await openDropdown();
    await userEvent.click(await screen.findByRole('option', { name: /Solanaceae/ }));

    await userEvent.click(await screen.findByTestId('add-successor-button'));
    const dialog = await screen.findByRole('dialog');
    await userEvent.click(within(dialog).getByRole('combobox'));
    await userEvent.click(await screen.findByRole('option', { name: 'Fabaceae' }));
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create' }));

    await waitFor(() => expect(posted).toHaveLength(1));
    expect(posted[0]).toMatchObject({
      from_family_key: 'fam-solanaceae',
      to_family_key: 'fam-fabaceae',
    });
  });

  it('clears all active filters with the reset button', async () => {
    renderWithProviders(<CropRotationPage />);
    await userEvent.click(await screen.findByTestId('filter-nitrogen-fixing'));
    await userEvent.click(screen.getByTestId('clear-filters'));
    await openDropdown();

    const names = await optionNames();
    expect(names).toHaveLength(3);
  });
});
