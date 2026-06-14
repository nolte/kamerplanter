import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SiteListPage from '@/pages/standorte/SiteListPage';
import { renderWithProviders } from '../helpers';

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
});
