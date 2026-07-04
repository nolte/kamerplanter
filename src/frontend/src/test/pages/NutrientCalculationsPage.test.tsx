import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import NutrientCalculationsPage from '@/pages/duengung/NutrientCalculationsPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/** Returns the MUI Card element that contains the given section heading. */
function cardForHeading(name: RegExp): HTMLElement {
  const heading = screen.getByRole('heading', { name });
  const card = heading.closest('.MuiCard-root');
  if (!(card instanceof HTMLElement)) throw new Error('card not found');
  return card;
}

describe('NutrientCalculationsPage — AP-10/11 additions', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the new mixing-protocol alkalinity and phase inputs', () => {
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);
    expect(within(card).getByLabelText(/Alkalinität/)).toBeTruthy();
    expect(within(card).getByLabelText(/Wachstumsphase/)).toBeTruthy();
  });

  it('surfaces ec_net, pH reserve and validity in the mixing-protocol result', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-protocol', () =>
        HttpResponse.json({
          dosages: [],
          calculated_ec: 1.5,
          ph_adjustment: { needed: false, direction: 'none', delta: 0 },
          warnings: [],
          instructions: [],
          ec_net: 1.2,
          ec_ph_reserve: 0.3,
          valid: true,
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Netto-EC-Budget: 1\.200/)).toBeTruthy();
    });
    expect(within(card).getByText(/pH-Reserve: 0\.300/)).toBeTruthy();
    expect(within(card).getByText(/Rezept gültig/)).toBeTruthy();
  });

  it('renders the area-dosing section with area, location and demand inputs', () => {
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Flächendosierung/);
    expect(within(card).getByLabelText(/Beetfläche/)).toBeTruthy();
    expect(within(card).getByLabelText(/Standort/)).toBeTruthy();
    expect(within(card).getByLabelText(/Nährstoffbedarf/)).toBeTruthy();
  });

  it('calculates area dosing and renders the resulting amounts', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/area-dosing', () =>
        HttpResponse.json({
          area_m2: 12,
          items: [
            {
              fertilizer_key: 'compost',
              product_name: 'Compost',
              rate_g_per_m2: 150,
              rate_l_per_m2: null,
              total_grams: 1800,
              total_liters: null,
              dilution_ratio: null,
              nutrient_release_speed: 'months',
              note: null,
            },
          ],
          warnings: [],
          instructions: ['Prepare bed of 12 m².'],
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Flächendosierung/);

    const keysField = within(card).getByLabelText(/Düngemittel-Keys/);
    await user.type(keysField, 'compost');
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText('Compost')).toBeTruthy();
    });
    expect(within(card).getByText('1800.0')).toBeTruthy();
  });
});
