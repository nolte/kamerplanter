import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import CultivarListSection from '@/pages/stammdaten/CultivarListSection';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { Cultivar } from '@/api/types';

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

describe('CultivarListSection', () => {
  it('renders cultivar rows with name, breeder, maturity and trait chips', async () => {
    server.use(
      http.get(CULTIVARS_URL, () =>
        HttpResponse.json([
          makeCultivar({ key: 'cv-1', name: 'Sungold', breeder: 'Tozer', traits: ['compact'] }),
          makeCultivar({ key: 'cv-2', name: 'Black Cherry', breeder: null, days_to_maturity: null }),
        ]),
      ),
    );
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    expect(await screen.findByText('Sungold')).toBeInTheDocument();
    expect(screen.getByText('Black Cherry')).toBeInTheDocument();
    expect(screen.getByText('Tozer')).toBeInTheDocument();
    // Missing breeder renders the em-dash fallback.
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
    // Trait chip is translated.
    expect(screen.getByText(i18n.t('enums.plantTrait.compact'))).toBeInTheDocument();
  });

  it('shows the empty state when there are no cultivars', async () => {
    server.use(http.get(CULTIVARS_URL, () => HttpResponse.json([])));
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    expect(await screen.findByText(i18n.t('pages.cultivars.title'))).toBeInTheDocument();
    // No data rows.
    await waitFor(() => expect(screen.queryByTestId('data-table-row')).toBeNull());
  });

  it('resolves without rows when loading fails (error handler path)', async () => {
    server.use(
      http.get(CULTIVARS_URL, () => HttpResponse.json({ message: 'boom' }, { status: 500 })),
    );
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    expect(await screen.findByText(i18n.t('pages.cultivars.title'))).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText('Sungold')).toBeNull());
  });

  it('opens the create dialog from the create button', async () => {
    server.use(http.get(CULTIVARS_URL, () => HttpResponse.json([])));
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    await screen.findByText(i18n.t('pages.cultivars.title'));
    await userEvent.click(screen.getByTestId('create-button'));

    expect(await screen.findByTestId('cultivar-create-dialog')).toBeInTheDocument();
  });

  it('deletes a cultivar after confirmation and reloads', async () => {
    let deleted = false;
    server.use(
      http.get(CULTIVARS_URL, () =>
        HttpResponse.json(deleted ? [] : [makeCultivar({ key: 'cv-1', name: 'Sungold' })]),
      ),
      http.delete('/api/v1/species/sp-1/cultivars/cv-1', () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    const row = (await screen.findByText('Sungold')).closest('[data-testid="data-table-row"]') as HTMLElement;
    await userEvent.click(within(row).getByLabelText(i18n.t('common.delete')));

    await userEvent.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleted).toBe(true));
    await waitFor(() => expect(screen.queryByText('Sungold')).toBeNull());
  });

  it('cancels the delete confirmation without deleting', async () => {
    server.use(
      http.get(CULTIVARS_URL, () =>
        HttpResponse.json([makeCultivar({ key: 'cv-1', name: 'Sungold' })]),
      ),
    );
    renderWithProviders(<CultivarListSection speciesKey="sp-1" />);

    const row = (await screen.findByText('Sungold')).closest('[data-testid="data-table-row"]') as HTMLElement;
    await userEvent.click(within(row).getByLabelText(i18n.t('common.delete')));

    await userEvent.click(await screen.findByTestId('confirm-dialog-cancel'));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(screen.getByText('Sungold')).toBeInTheDocument();
  });
});
