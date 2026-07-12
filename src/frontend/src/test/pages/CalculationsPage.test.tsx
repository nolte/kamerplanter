import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Site } from '@/api/types';

/**
 * The calculators call the REST API through `@/api/endpoints/calculations`.
 * We mock that module so we can assert the *exact* payloads the reworked
 * selection fields still send — the server contract (REQ #542) is unchanged.
 */
const calcMocks = vi.hoisted(() => ({
  calculateVPD: vi.fn(),
  calculateGDD: vi.fn(),
  calculatePhotoperiodTransition: vi.fn(),
  calculateSlotCapacity: vi.fn(),
  calculateSunTimes: vi.fn(),
}));

vi.mock('@/api/endpoints/calculations', () => calcMocks);

// The sun-times card lazy-loads sites; keep it deterministic and offline.
const sitesMocks = vi.hoisted(() => ({ listSites: vi.fn() }));
vi.mock('@/api/endpoints/sites', () => ({
  __esModule: true,
  listSites: sitesMocks.listSites,
  getSite: vi.fn(),
  listLocations: vi.fn(),
  getLocation: vi.fn(),
  listSlots: vi.fn(),
}));

import CalculationsPage from '@/pages/pflanzen/CalculationsPage';
import { createTestStore, renderWithProviders, type TestStore } from '../helpers';

function makeSite(partial: Partial<Site>): Site {
  return {
    key: 's1',
    name: 'Garten',
    type: 'outdoor',
    gps_coordinates: [48, 11],
    climate_zone: '',
    total_area_m2: 0,
    timezone: 'Europe/Vienna',
    last_frost_date_avg: null,
    first_frost_date_avg: null,
    eisheilige_date: null,
    created_at: null,
    updated_at: null,
    ...partial,
  };
}

function storeWithSites(sites: Site[]): TestStore {
  return createTestStore({
    sites: {
      sites,
      currentSite: null,
      locations: [],
      currentLocation: null,
      slots: [],
      loading: false,
      error: null,
    },
  });
}

/** Returns the MUI Card element that contains the given section heading. */
function cardForHeading(name: RegExp): HTMLElement {
  const heading = screen.getByRole('heading', { name });
  const card = heading.closest('.MuiCard-root');
  if (!(card instanceof HTMLElement)) throw new Error('card not found');
  return card;
}

beforeEach(() => {
  vi.clearAllMocks();
  sitesMocks.listSites.mockResolvedValue([]);
  calcMocks.calculateVPD.mockResolvedValue({ vpd_kpa: 1.05, status: 'optimal', recommendation: 'ok' });
  calcMocks.calculateGDD.mockResolvedValue({ accumulated_gdd: 30, days_counted: 3 });
  calcMocks.calculatePhotoperiodTransition.mockResolvedValue([
    { day: 1, photoperiod_hours: 18, lights_on: '06:00', lights_off: '00:00', dli: 25.9 },
  ]);
  calcMocks.calculateSlotCapacity.mockResolvedValue({
    max_capacity: 111,
    optimal_range: [80, 100],
    plants_per_m2: 11.11,
  });
  calcMocks.calculateSunTimes.mockResolvedValue({
    date: '2026-07-12',
    sunrise: '05:10',
    sunset: '21:20',
    dawn: '04:30',
    dusk: '22:00',
    day_length_hours: 16.17,
  });
  return i18n.changeLanguage('de');
});

describe('CalculationsPage — selection-field rework (#542)', () => {
  it('renders all five calculators', () => {
    renderWithProviders(<CalculationsPage />);
    expect(screen.getByRole('heading', { name: /VPD-Rechner/ })).toBeTruthy();
    expect(screen.getByRole('heading', { name: /GDD-Rechner/ })).toBeTruthy();
    expect(screen.getByRole('heading', { name: /Photoperioden-Übergang/ })).toBeTruthy();
    expect(screen.getByRole('heading', { name: /Stellplatz-Kapazität/ })).toBeTruthy();
    expect(screen.getByRole('heading', { name: /Sonnenstand-Rechner/ })).toBeTruthy();
  });

  it('VPD sends the selected phase through to the unchanged payload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/VPD-Rechner/);

    // The phase select is a real dropdown (was not exposed before).
    const phase = within(card).getByRole('combobox', { name: /Wachstumsphase/ });
    await user.click(phase);
    await user.click(await screen.findByRole('option', { name: 'Blüte' }));

    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateVPD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateVPD).toHaveBeenCalledWith({
      temp_c: 25,
      humidity_percent: 60,
      phase: 'flowering',
    });
    expect(within(card).getByText(/1\.05 kPa/)).toBeTruthy();
  });

  it('VPD shows the phase target band', () => {
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/VPD-Rechner/);
    // default phase = vegetative → 0.8–1.2 kPa
    expect(within(card).getByText(/0\.8–1\.2 kPa/)).toBeTruthy();
  });

  it('GDD sends structured min/max rows as daily_temps tuples', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateGDD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateGDD).toHaveBeenCalledWith({
      daily_temps: [
        [15, 25],
        [14, 24],
        [16, 28],
      ],
      base_temp_c: 10,
    });
  });

  it('GDD base-temp preset button updates the sent base_temp_c', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    await user.click(within(card).getByRole('button', { name: /Warmjahreszeit/ }));
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateGDD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateGDD.mock.calls[0][0].base_temp_c).toBe(15);
  });

  it('GDD add/remove day changes the number of tuples', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    await user.click(within(card).getByRole('button', { name: 'Tag hinzufügen' }));
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateGDD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateGDD.mock.calls[0][0].daily_temps).toHaveLength(4);
  });

  it('GDD remove-day drops a tuple from the payload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    await user.click(within(card).getByRole('button', { name: 'Tag 3 entfernen' }));
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateGDD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateGDD.mock.calls[0][0].daily_temps).toEqual([
      [15, 25],
      [14, 24],
    ]);
  });

  it('GDD edits a min temperature and sends the updated tuple', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    const min1 = within(card).getByLabelText('Min 1');
    fireEvent.change(min1, { target: { value: '12' } });
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateGDD).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateGDD.mock.calls[0][0].daily_temps[0]).toEqual([12, 25]);
  });

  it('GDD blocks calculation when a row max is below its min', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/GDD-Rechner/);

    const max1 = within(card).getByLabelText('Max 1');
    await user.clear(max1);
    await user.type(max1, '5');

    expect(within(card).getByRole('button', { name: 'Berechnen' })).toBeDisabled();
    expect(within(card).getByText(/Höchstwert darf nicht unter/)).toBeTruthy();
  });

  it('Photoperiod captures PPFD (preset) and sends it in the payload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/Photoperioden-Übergang/);

    await user.click(within(card).getByRole('button', { name: '600' }));
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() =>
      expect(calcMocks.calculatePhotoperiodTransition).toHaveBeenCalledTimes(1),
    );
    expect(calcMocks.calculatePhotoperiodTransition).toHaveBeenCalledWith({
      current_hours: 18,
      target_hours: 12,
      transition_days: 7,
      ppfd: 600,
      lights_on_time: '06:00',
    });
  });

  it('Slot capacity sends unchanged payload and renders result tiles', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/Stellplatz-Kapazität/);

    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateSlotCapacity).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateSlotCapacity).toHaveBeenCalledWith({
      area_m2: 10,
      plant_spacing_cm: 30,
    });
    expect(within(card).getByText('111')).toBeTruthy();
    expect(within(card).getByText('80–100')).toBeTruthy();
  });

  it('Slot capacity accepts a custom spacing via the autocomplete', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/Stellplatz-Kapazität/);

    const spacing = within(card).getByRole('combobox', { name: /Pflanzabstand/ });
    await user.clear(spacing);
    await user.type(spacing, '45');
    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateSlotCapacity).toHaveBeenCalledTimes(1));
    expect(calcMocks.calculateSlotCapacity.mock.calls[0][0].plant_spacing_cm).toBe(45);
  });

  it('Sun times sends unchanged payload with the default timezone', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalculationsPage />);
    const card = cardForHeading(/Sonnenstand-Rechner/);

    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateSunTimes).toHaveBeenCalledTimes(1));
    const payload = calcMocks.calculateSunTimes.mock.calls[0][0];
    expect(payload.latitude).toBe(52.52);
    expect(payload.longitude).toBe(13.405);
    expect(payload.timezone).toBe('Europe/Berlin');
    expect(typeof payload.date).toBe('string');
  });

  it('Sun times prefills coordinates and timezone from a selected site', async () => {
    const user = userEvent.setup();
    const site = makeSite({ key: 's9', name: 'Balkon', gps_coordinates: [48, 11], timezone: 'Europe/Vienna' });
    renderWithProviders(<CalculationsPage />, { store: storeWithSites([site]) });
    const card = cardForHeading(/Sonnenstand-Rechner/);

    const sitePicker = within(card).getByRole('combobox', { name: /Standort übernehmen/ });
    await user.click(sitePicker);
    await user.click(await screen.findByRole('option', { name: 'Balkon' }));

    await user.click(within(card).getByRole('button', { name: 'Berechnen' }));

    await waitFor(() => expect(calcMocks.calculateSunTimes).toHaveBeenCalledTimes(1));
    const payload = calcMocks.calculateSunTimes.mock.calls[0][0];
    expect(payload.latitude).toBe(48);
    expect(payload.longitude).toBe(11);
    expect(payload.timezone).toBe('Europe/Vienna');
  });
});
