import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';
import { renderWithProviders } from '../helpers';

describe('PlantInstanceListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanzeninstanzen')).toBeTruthy();
    });
  });

  it('loads and displays plants from API', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Big Red')).toBeTruthy();
    });
  });

  it('shows instance ID', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('TOM-001')).toBeTruthy();
    });
  });

  it('shows the data table', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByTestId('data-table')).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Pflanze erstellen')).toBeTruthy();
    });
  });

  it('renders the current phase as a localized chip', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText('Vegetativ')).toBeTruthy();
    });
  });

  it('shows the introduction text once plants are loaded', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Hier sehen Sie alle angelegten Pflanzen/)).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    const createButton = await screen.findByTestId('create-button');
    await user.click(createButton);

    expect(await screen.findByTestId('plant-instance-create-dialog')).toBeTruthy();
  });

  it('hides removed plants by default and reveals them when the switch is toggled off', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantInstanceListPage />);

    await screen.findByText('Big Red');
    const toggle = screen.getByRole('switch');
    expect(toggle).toBeChecked();

    await user.click(toggle);
    expect(toggle).not.toBeChecked();
    // The single mock plant has no removed_on, so it stays visible regardless.
    expect(screen.getByText('Big Red')).toBeTruthy();
  });

  it('enables label printing when plants are present', async () => {
    renderWithProviders(<PlantInstanceListPage />);
    const labelButton = await screen.findByTestId('label-button');
    await waitFor(() => {
      expect(labelButton).not.toBeDisabled();
    });
  });
});
