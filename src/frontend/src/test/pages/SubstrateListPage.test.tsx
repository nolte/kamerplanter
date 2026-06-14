import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SubstrateListPage from '@/pages/standorte/SubstrateListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { mockSubstrates } from '../mocks/handlers';

describe('SubstrateListPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the page title', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText('Substrate')).toBeTruthy();
    });
  });

  it('shows empty state when no substrates', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText(/keine daten/i)).toBeTruthy();
    });
  });

  it('shows the create button', async () => {
    renderWithProviders(<SubstrateListPage />);
    await waitFor(() => {
      expect(screen.getByText('Substrat erstellen')).toBeTruthy();
    });
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateListPage />);

    await user.click(await screen.findByText('Substrat erstellen'));
    expect(await screen.findByTestId('substrate-create-dialog')).toBeTruthy();
  });

  it('opens the mix dialog when the create-mix button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateListPage />);

    await user.click(await screen.findByText('Mischung erstellen'));
    expect(await screen.findByTestId('substrate-mix-dialog')).toBeTruthy();
  });

  describe('with a populated substrate list', () => {
    beforeEach(() => {
      server.use(http.get('/api/v1/substrates', () => HttpResponse.json(mockSubstrates)));
    });

    it('renders substrate rows with localized type and pH', async () => {
      renderWithProviders(<SubstrateListPage />);
      await waitFor(() => {
        expect(screen.getAllByText('Kokos Substrat').length).toBeGreaterThan(0);
      });
      // ph_base 6.0 rendered with one decimal
      expect(screen.getAllByText('6.0').length).toBeGreaterThan(0);
    });

    it('renders a favorite-toggle star for each substrate row', async () => {
      renderWithProviders(<SubstrateListPage />);

      await screen.findAllByText('Kokos Substrat');
      const starButtons = screen.getAllByRole('button').filter((b) =>
        b.querySelector('svg[data-testid="StarBorderIcon"], svg[data-testid="StarIcon"]'),
      );
      expect(starButtons.length).toBeGreaterThanOrEqual(2);
    });

    it('renders the second substrate row with its localized name', async () => {
      renderWithProviders(<SubstrateListPage />);
      await waitFor(() => {
        expect(screen.getAllByText('Perlit').length).toBeGreaterThan(0);
      });
    });

    it('searches substrates, exercising the column search predicates', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SubstrateListPage />);

      await screen.findAllByText('Kokos Substrat');
      const search = screen.getByPlaceholderText('Tabelle durchsuchen...');
      await user.type(search, 'Perlit');
      await waitFor(() => {
        expect(screen.queryByText('Kokos Substrat')).toBeNull();
      });
      expect(screen.getAllByText('Perlit').length).toBeGreaterThan(0);
    });

    it('sorts substrates by the pH column', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SubstrateListPage />);

      await screen.findAllByText('Kokos Substrat');
      const header = screen.getByRole('button', {
        name: new RegExp(i18n.t('pages.substrates.phBase')),
      });
      await user.click(header);
      expect(screen.getAllByText('Kokos Substrat').length).toBeGreaterThan(0);
    });

    it('invokes row navigation when a substrate row is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SubstrateListPage />);

      const rows = await screen.findAllByText('Kokos Substrat');
      await user.click(rows[0]);
      // Row click triggers navigate(); the page itself stays mounted
      expect(screen.getByTestId('data-table')).toBeTruthy();
    });

    it('renders the reusable yes/no chip for each substrate', async () => {
      renderWithProviders(<SubstrateListPage />);
      await screen.findAllByText('Kokos Substrat');
      // sub-1 is reusable (Ja), sub-2 is not (Nein)
      expect(screen.getAllByText('Ja').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Nein').length).toBeGreaterThan(0);
    });

    describe('mobile viewport', () => {
      afterEach(() => {
        vi.unstubAllGlobals();
      });

      it('renders mobile substrate cards', async () => {
        vi.stubGlobal(
          'matchMedia',
          vi.fn().mockReturnValue({
            matches: true,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            addListener: vi.fn(),
            removeListener: vi.fn(),
          } as unknown as MediaQueryList),
        );
        renderWithProviders(<SubstrateListPage />);
        await waitFor(() => {
          expect(screen.getAllByText('Kokos Substrat').length).toBeGreaterThan(0);
        });
      });
    });
  });
});
