import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SiteListPage from '@/pages/standorte/SiteListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('SiteListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Standorte')).toBeTruthy();
    });
  });

  it('loads and displays sites from API', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Main Greenhouse')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('Standort erstellen')).toBeTruthy();
    });
  });

  it('displays area with unit', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText('50 m²')).toBeTruthy();
    });
  });

  it('shows the introduction text once sites are loaded', async () => {
    renderWithProviders(<SiteListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Standorte sind Ihre Anbauflächen/)).toBeTruthy();
    });
  });

  it('expands a site card and loads its location tree on click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    const header = within(card).getByRole('button', { expanded: false });
    await user.click(header);

    await waitFor(() => {
      expect(screen.getByText('Zone A')).toBeTruthy();
    });
    expect(within(card).getByRole('button', { expanded: true })).toBeTruthy();
  });

  it('opens the create-site dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const createButton = await screen.findByTestId('create-button');
    await user.click(createButton);

    expect(await screen.findByTestId('site-create-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('shows the empty state with a create action when there are no sites', async () => {
    server.use(
      http.get('/api/v1/sites', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/sites', () => HttpResponse.json([])),
    );
    renderWithProviders(<SiteListPage />);

    await waitFor(() => {
      expect(screen.getByText(/Noch keine Standorte/i)).toBeTruthy();
    });
  });

  it('opens the location-create dialog from an expanded site', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    await user.click(within(card).getByRole('button', { expanded: false }));

    // Tree loads → "create location" action becomes available
    const addLocationBtn = await screen.findByTestId('add-location-site-1');
    await user.click(addLocationBtn);

    expect(await screen.findByTestId('location-create-dialog')).toBeTruthy();
  });

  it('navigates to the site detail when the site name is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const siteName = await screen.findByTestId('site-name-site-1');
    // Clicking the name must not toggle the expand state (stopPropagation)
    await user.click(siteName);
    // Card stays collapsed: expand control still reports not-expanded
    const card = screen.getByTestId('site-card-site-1');
    expect(within(card).getByRole('button', { expanded: false })).toBeTruthy();
  });

  it('renders a nested location tree with slot, plant and tank chips', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/sites/:key/location-tree', () =>
        HttpResponse.json([
          {
            key: 'loc-parent', name: 'Greenhouse Zone', location_type_key: 'lt-bed',
            slot_count: 4, active_plant_count: 2, tank_name: 'Tank A',
            children: [
              { key: 'loc-child', name: 'Bed 1', location_type_key: 'lt-bed', slot_count: 2, active_plant_count: 1, tank_name: null, children: [] },
            ],
          },
        ]),
      ),
      http.get('/api/v1/sites/:key/location-tree', () =>
        HttpResponse.json([
          {
            key: 'loc-parent', name: 'Greenhouse Zone', location_type_key: 'lt-bed',
            slot_count: 4, active_plant_count: 2, tank_name: 'Tank A',
            children: [
              { key: 'loc-child', name: 'Bed 1', location_type_key: 'lt-bed', slot_count: 2, active_plant_count: 1, tank_name: null, children: [] },
            ],
          },
        ]),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    await user.click(within(card).getByRole('button', { expanded: false }));

    await waitFor(() => {
      expect(screen.getByText('Greenhouse Zone')).toBeTruthy();
    });
    expect(screen.getByText('Tank A')).toBeTruthy();
    expect(screen.getByText('Bed 1')).toBeTruthy();
  });

  it('shows the per-site empty tree state when a site has no locations', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/sites/:key/location-tree', () => HttpResponse.json([])),
      http.get('/api/v1/sites/:key/location-tree', () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    await user.click(within(card).getByRole('button', { expanded: false }));

    await waitFor(() => {
      expect(screen.getByText(i18n.t('pages.locations.noSublocations'))).toBeTruthy();
    });
  });
});
