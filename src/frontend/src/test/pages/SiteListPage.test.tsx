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
      expect(screen.getByText(/Standorte sind deine Anbauflächen/)).toBeTruthy();
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

  it('renders the site name as a link that does not toggle the card (#3047)', async () => {
    const user = userEvent.setup();
    const { router } = renderWithProviders(<SiteListPage />, { route: '/standorte/sites' });

    const siteName = await screen.findByTestId('site-name-site-1');
    expect(siteName.tagName).toBe('A');
    expect(siteName).toHaveAttribute('href', '/standorte/sites/site-1');
    // The link is not nested in the expand button any more.
    const card = screen.getByTestId('site-card-site-1');
    expect(within(card).getByRole('button', { expanded: false }).contains(siteName)).toBe(false);
    await user.click(siteName);
    expect(router.state.location.pathname).toBe('/standorte/sites/site-1');
    // The header around the link toggles the card; the link's click must not reach it.
    expect(within(screen.getByTestId('site-card-site-1')).getByRole('button', { expanded: false })).toBeInTheDocument();
  });

  it('toggles once per click on the expand button and on the header (#3047)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    await user.click(within(card).getByRole('button', { expanded: false }));
    expect(within(card).getByRole('button', { expanded: true })).toBeTruthy();
    // A click on the header text outside the link toggles back.
    await user.click(within(card).getByText('50 m²'));
    expect(within(card).getByRole('button', { expanded: false })).toBeTruthy();
  });

  it('links each location of the tree to its detail page (#3047)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteListPage />);

    const card = await screen.findByTestId('site-card-site-1');
    await user.click(within(card).getByRole('button', { expanded: false }));
    const location = await within(card).findByRole('link', { name: 'Zone A' });
    expect(location.getAttribute('href')).toMatch(/^\/standorte\/locations\//);
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
