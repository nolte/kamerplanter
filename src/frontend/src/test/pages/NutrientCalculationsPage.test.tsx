import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import NutrientCalculationsPage from '@/pages/duengung/NutrientCalculationsPage';
import { createStoreWithExpertise, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/** Returns the MUI Card element that contains the given section heading. */
function cardForHeading(name: RegExp): HTMLElement {
  const heading = screen.getByRole('heading', { name });
  const card = heading.closest('.MuiCard-root');
  if (!(card instanceof HTMLElement)) throw new Error('card not found');
  return card;
}

/**
 * Clears a controlled numeric/text field and enters a fresh value.
 *
 * Uses paste rather than `user.type` on purpose. This page keeps every panel's
 * form state at page level, so a single keystroke re-renders all panels; typing
 * an n-character value costs n full page renders, and the 27 field entries in
 * this file made it the slowest test file in the suite (#778, H4). Pasting
 * enters the value in one input event — the same `onChange` contract the
 * component sees from a real paste. Measured interleaved under v8 coverage:
 * ~7% off the whole file and ~11% off the heaviest test. Intermediate
 * keystroke states ("1", "1.") are not asserted anywhere, and the page has no
 * key handlers, so nothing is lost.
 *
 * `user.clear` focuses the field, so the subsequent paste lands in it.
 */
async function retype(
  user: ReturnType<typeof userEvent.setup>,
  field: HTMLElement,
  value: string,
): Promise<void> {
  await user.clear(field);
  await user.paste(value);
}

/** Opens a MUI Autocomplete input and clicks the option matching `optionName`. */
async function pickOption(
  user: ReturnType<typeof userEvent.setup>,
  input: HTMLElement,
  optionName: RegExp | string,
): Promise<void> {
  await user.click(input);
  const option = await screen.findByRole('option', { name: optionName });
  await user.click(option);
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
    const user = userEvent.setup({ delay: null });
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
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Flächendosierung/);

    await pickOption(user, within(card).getByLabelText('Düngemittel'), /Compost/);
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText('1800.0')).toBeTruthy();
    });
  });
});

describe('NutrientCalculationsPage — mixing protocol details', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('drives every mixing-protocol input and renders an invalid result with dosages, pH adjustment, warnings and instructions', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-protocol', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          dosages: [
            {
              fertilizer_key: 'grow',
              product_name: 'Grow A',
              ml_per_liter: 2.5,
              total_ml: 25,
              ec_contribution: 0.8,
            },
          ],
          calculated_ec: 1.9,
          ph_adjustment: { needed: true, direction: 'down', delta: 0.42 },
          warnings: ['Hohe Alkalinität begrenzt das Dünger-Budget.'],
          instructions: ['Silizium zuerst zugeben.', 'Dann Basis A.'],
          ec_net: 1.5,
          ec_ph_reserve: 0.25,
          valid: false,
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);

    await retype(user, within(card).getByLabelText(/Zielvolumen/), '20');
    await retype(user, within(card).getByLabelText(/Ziel-EC/), '2');
    await retype(user, within(card).getByLabelText(/Ziel-pH/), '5.8');
    await retype(user, within(card).getByLabelText(/Basiswasser-EC/), '0.4');
    await retype(user, within(card).getByLabelText(/Basiswasser-pH/), '7');
    await retype(user, within(card).getByLabelText(/Alkalinität/), '120');
    const mpFertInput = within(card).getByLabelText('Düngemittel');
    await pickOption(user, mpFertInput, /Grow A/);
    await pickOption(user, mpFertInput, /Bloom B/);

    const phaseSelect = within(card).getByLabelText(/Wachstumsphase/);
    await user.click(phaseSelect);
    await user.click(await screen.findByRole('option', { name: 'Blüte' }));

    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Rezept überschreitet EC-Obergrenze/)).toBeTruthy();
    });
    // pH adjustment branch (needed === true)
    expect(within(card).getByText(/pH down/)).toBeTruthy();
    // warnings + instructions
    expect(within(card).getByText(/Hohe Alkalinität begrenzt/)).toBeTruthy();
    expect(within(card).getByText(/1\. Silizium zuerst zugeben\./)).toBeTruthy();
    expect(within(card).getByText(/2\. Dann Basis A\./)).toBeTruthy();
    // dosage table (desktop column renderers)
    expect(within(card).getByText('Grow A')).toBeTruthy();
    expect(within(card).getByText('2.50')).toBeTruthy();
    expect(within(card).getByText('0.800')).toBeTruthy();

    // request payload reflects the driven inputs
    expect(captured).toMatchObject({
      target_volume_liters: 20,
      target_ph: 5.8,
      alkalinity_ppm: 120,
      phase: 'flowering',
      fertilizer_keys: ['grow', 'bloom'],
    });
  });

  it('reports an API failure via the error handler without rendering a result', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-protocol', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    // A snackbar alert surfaces; no valid/invalid recipe chip appears in the card
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeTruthy();
    });
    expect(within(card).queryByText(/Rezept gültig/)).toBeNull();
    expect(within(card).queryByText(/Rezept überschreitet/)).toBeNull();
  });
});

describe('NutrientCalculationsPage — flushing', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('drives the flushing inputs and renders the schedule table', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/flushing', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          substrate_type: 'coco',
          recommended_flush_days: 7,
          flush_start_day: 57,
          current_ec_ms: 1.5,
          schedule: [
            { day: 1, absolute_day: 57, target_ec_ms: 1.2, action: 'Reduzieren', dosage_percent: 75 },
            { day: 2, absolute_day: 58, target_ec_ms: 0.8, action: 'Spülen', dosage_percent: 50 },
          ],
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/^Spülung$/);

    await retype(user, within(card).getByLabelText(/Aktueller EC/), '1.6');
    await retype(user, within(card).getByLabelText(/Tage bis Ernte/), '10');
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Empfohlene Spültage: 7/)).toBeTruthy();
    });
    // flushColumns render functions (action + target EC + dosage percent)
    expect(within(card).getByText('Reduzieren')).toBeTruthy();
    expect(within(card).getByText('Spülen')).toBeTruthy();
    expect(within(card).getByText('1.20')).toBeTruthy();
    expect(within(card).getByText('75%')).toBeTruthy();

    expect(captured).toMatchObject({ current_ec_ms: 1.6, days_until_harvest: 10 });
  });
});

describe('NutrientCalculationsPage — runoff analysis', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it.each([
    ['healthy', 'ok', 'ok', 'ok'],
    ['warning', 'high', 'low', 'high'],
    ['critical', 'high', 'low', 'low'],
  ])(
    'renders runoff status alerts for overall_health=%s',
    async (overall, ecStatus, phStatus, volumeStatus) => {
      server.use(
        http.post('/api/v1/t/:tenant/nutrient-calculations/runoff', () =>
          HttpResponse.json({
            ec_delta: 0.7,
            ec_status: ecStatus,
            ec_message: 'EC-Meldung',
            ph_delta: -0.5,
            ph_status: phStatus,
            ph_message: 'pH-Meldung',
            runoff_percent: 20,
            volume_status: volumeStatus,
            volume_message: 'Volumen-Meldung',
            overall_health: overall,
          }),
        ),
      );
      const user = userEvent.setup({ delay: null });
      renderWithProviders(<NutrientCalculationsPage />);
      const card = cardForHeading(/Ablauf-Analyse/);
      await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

      await waitFor(() => {
        expect(within(card).getByText(new RegExp(`Gesamtzustand: ${overall}`))).toBeTruthy();
      });
      expect(within(card).getByText(/EC-Meldung/)).toBeTruthy();
      expect(within(card).getByText(/pH-Meldung/)).toBeTruthy();
      expect(within(card).getByText(/Volumen-Meldung/)).toBeTruthy();
      expect(within(card).getByText(/20\.0%/)).toBeTruthy();
    },
  );

  it('drives every runoff input field before calculating', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/runoff', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          ec_delta: 0.1,
          ec_status: 'ok',
          ec_message: 'ok',
          ph_delta: 0,
          ph_status: 'ok',
          ph_message: 'ok',
          runoff_percent: 15,
          volume_status: 'ok',
          volume_message: 'ok',
          overall_health: 'healthy',
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Ablauf-Analyse/);

    await retype(user, within(card).getByLabelText(/Eingangs-EC/), '1.7');
    await retype(user, within(card).getByLabelText(/Ablauf-EC/), '2.1');
    await retype(user, within(card).getByLabelText(/Eingangs-pH/), '6.1');
    await retype(user, within(card).getByLabelText(/Ablauf-pH/), '5.9');
    await retype(user, within(card).getByLabelText(/Eingangsvolumen/), '2');
    await retype(user, within(card).getByLabelText(/Ablaufvolumen/), '0.3');
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Gesamtzustand: healthy/)).toBeTruthy();
    });
    expect(captured).toMatchObject({
      input_ec_ms: 1.7,
      runoff_ec_ms: 2.1,
      input_ph: 6.1,
      runoff_ph: 5.9,
      input_volume_liters: 2,
      runoff_volume_liters: 0.3,
    });
  });
});

describe('NutrientCalculationsPage — mixing safety', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders a safe result', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-safety', () =>
        HttpResponse.json({ safe: true, warnings: [] }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischsicherheit/);
    const msInput = within(card).getByLabelText('Düngemittel');
    await pickOption(user, msInput, /Grow A/);
    await pickOption(user, msInput, /Bloom B/);
    await user.click(within(card).getByRole('button', { name: /Validieren/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Alle Düngemittel sind kompatibel/)).toBeTruthy();
    });
    expect(within(card).getByText('Sicher')).toBeTruthy();
  });

  it('renders an unsafe result with warnings', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-safety', () =>
        HttpResponse.json({
          safe: false,
          warnings: ['CalMag darf nicht mit Sulfaten gemischt werden.'],
        }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischsicherheit/);
    const msInput = within(card).getByLabelText('Düngemittel');
    await pickOption(user, msInput, /CalMag Plus/);
    await pickOption(user, msInput, /Base Nute/);
    await user.click(within(card).getByRole('button', { name: /Validieren/ }));

    await waitFor(() => {
      expect(within(card).getByText(/Inkompatibilitäten/)).toBeTruthy();
    });
    expect(within(card).getByText('Unsicher')).toBeTruthy();
    expect(within(card).getByText(/CalMag darf nicht mit Sulfaten/)).toBeTruthy();
  });
});

describe('NutrientCalculationsPage — area dosing edge cases', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('shows the override hint when both area and location are set, and renders warnings, instructions and liters-based items', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/area-dosing', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          area_m2: 8,
          items: [
            {
              fertilizer_key: 'liquid-manure',
              product_name: 'Jauche',
              rate_g_per_m2: null,
              rate_l_per_m2: 2,
              total_grams: null,
              total_liters: 16,
              dilution_ratio: '1:10',
              nutrient_release_speed: 'immediate',
              note: 'Vor dem Gießen verdünnen.',
            },
            {
              fertilizer_key: null,
              product_name: 'Unbenannt',
              rate_g_per_m2: null,
              rate_l_per_m2: null,
              total_grams: null,
              total_liters: null,
              dilution_ratio: null,
              nutrient_release_speed: null,
              note: null,
            },
          ],
          warnings: ['Stickstoffsammler brauchen keinen N-Dünger.'],
          instructions: ['Beet gleichmäßig gießen.'],
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Flächendosierung/);

    await pickOption(user, within(card).getByLabelText('Düngemittel'), /Jauche Liquid/);
    await retype(user, within(card).getByLabelText(/Beetfläche/), '8');
    await pickOption(user, within(card).getByLabelText('Standort'), /Zone A/);

    // area + location both set -> override hint alert (branch)
    await waitFor(() => {
      expect(within(card).getByText(/Standort wird ignoriert/)).toBeTruthy();
    });

    const demandSelect = within(card).getByLabelText(/Nährstoffbedarf/);
    await user.click(demandSelect);
    await user.click(await screen.findByRole('option', { name: 'Stickstoffsammler' }));

    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText('Jauche')).toBeTruthy();
    });
    // release speed enum render + liters column + note
    expect(within(card).getByText('Sofort verfügbar')).toBeTruthy();
    expect(within(card).getByText('16.0')).toBeTruthy();
    // null total_grams renders the em-dash fallback and null-key row uses product name
    expect(within(card).getAllByText('—').length).toBeGreaterThan(0);
    expect(within(card).getByText('Unbenannt')).toBeTruthy();
    // warnings + instructions
    expect(within(card).getByText(/Stickstoffsammler brauchen keinen/)).toBeTruthy();
    expect(within(card).getByText(/Beet gleichmäßig gießen\./)).toBeTruthy();

    expect(captured).toMatchObject({
      area_m2: 8,
      location_key: 'loc-1',
      demand_level: 'nitrogen_fixer',
      fertilizer_keys: ['liquid-manure'],
    });
  });
});

describe('NutrientCalculationsPage — water mixer + EC budget (expert)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('calculates the reverse water mix and surfaces the RO percentage', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/water-mix/reverse', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          ro_percent: 40,
          effective_profile: {
            ec_ms: 0.18,
            ph: 7.1,
            alkalinity_ppm: 50,
            calcium_ppm: 20,
            magnesium_ppm: 5,
            chlorine_ppm: 0,
            chloramine_ppm: 0,
          },
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);

    await retype(user, within(card).getByLabelText('Basiswasser-EC'), '0.6');
    await retype(user, within(card).getByLabelText(/Alkalinität/), '90');
    await retype(user, within(card).getByLabelText(/Ziel-Basiswasser-EC/), '0.2');

    const buttons = within(card).getAllByRole('button', { name: /Berechnen/ });
    await user.click(buttons[0]);

    await waitFor(() => {
      expect(within(card).getByText(/Empfohlener RO-Anteil: 40%/)).toBeTruthy();
    });
    expect(within(card).getByText(/0\.180 mS\/cm/)).toBeTruthy();
    expect(captured).toMatchObject({ target_base_ec_ms: 0.2 });
  });

  it('calculates the EC budget with segments, temperature correction, dosage table and instructions', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/ec-budget', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          ec_mix: 0.2,
          ec_net: 1.6,
          ec_silicate: 0.1,
          ec_calmag: 0.2,
          ec_fertilizers: 1.1,
          ec_ph_reserve: 0.2,
          ec_final: 1.75,
          ec_max: 2.0,
          ec_target: 1.8,
          ec_at_25_corrected: 1.72,
          tolerance: 0.1,
          valid: true,
          living_soil_bypass: false,
          segments: [
            { label: 'Basis', ec_contribution: 0.2, color_hint: 'bluegrey', ml_per_liter: 0, total_ml: 0, warning: null },
            { label: 'CalMag', ec_contribution: 0.2, color_hint: 'teal', ml_per_liter: 1, total_ml: 10, warning: null },
            { label: 'Dünger', ec_contribution: 1.1, color_hint: 'unknown-color', ml_per_liter: 3, total_ml: 30, warning: null },
            { label: 'x', ec_contribution: 0.02, color_hint: 'grey', ml_per_liter: 0, total_ml: 0, warning: null },
          ],
          warnings: ['EC nahe der Obergrenze.'],
          dosage_table: [
            { key: 'grow', product_name: 'Grow A', ml_per_liter: 3, total_ml: 30, ec_contribution: 1.1 },
          ],
          dosage_instructions: ['Silikat zuerst.', 'Dann CalMag.'],
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);

    await retype(user, within(card).getByLabelText(/Ziel-EC/), '1.8');
    await retype(user, within(card).getByLabelText('Zielvolumen (L)'), '15');

    // fertilizer rows editor: row 1 = grow @ 3.0 ml/L, row 2 = bloom (no dose)
    await user.click(within(card).getByRole('button', { name: /Dünger hinzufügen/ }));
    await pickOption(user, within(card).getByLabelText('Düngemittel'), /Grow A/);
    await retype(user, within(card).getByLabelText('Dosis (ml/L)'), '3.0');
    await user.click(within(card).getByRole('button', { name: /Dünger hinzufügen/ }));
    await pickOption(user, within(card).getAllByLabelText('Düngemittel')[1], /Bloom B/);

    await pickOption(user, within(card).getByLabelText(/CalMag-Dünger/), /CalMag Plus/);
    await retype(user, within(card).getByLabelText(/CalMag-Dosis/), '1.2');
    await pickOption(user, within(card).getByLabelText(/Silikat-Dünger/), /Silica Boost/);
    await retype(user, within(card).getByLabelText(/Silikat-Dosis/), '0.6');
    await retype(user, within(card).getByLabelText(/Substrat-Zyklen/), '3');
    await retype(user, within(card).getByLabelText(/Gemessener EC/), '1.9');
    await retype(user, within(card).getByLabelText(/Wassertemperatur/), '22');

    const buttons = within(card).getAllByRole('button', { name: /Berechnen/ });
    await user.click(buttons[buttons.length - 1]);

    await waitFor(() => {
      expect(within(card).getByText(/EC-Budget gültig/)).toBeTruthy();
    });
    // validation summary
    expect(within(card).getByText(/End-EC: 1\.75 mS/)).toBeTruthy();
    // temperature correction alert
    expect(within(card).getByText(/EC @25°C \(korrigiert\): 1\.720/)).toBeTruthy();
    // warnings + instructions + dosage table
    expect(within(card).getByText(/EC nahe der Obergrenze\./)).toBeTruthy();
    expect(within(card).getByText('Grow A')).toBeTruthy();
    expect(within(card).getByText(/Silikat zuerst\./)).toBeTruthy();

    // fertilizer keys parsed into key:dose entries; calmag/silicate doses attached
    expect(captured).toMatchObject({
      target_ec: 1.8,
      volume_liters: 15,
      calmag_key: 'calmag',
      calmag_dose_ml_per_liter: 1.2,
      silicate_key: 'si',
      silicate_dose_ml_per_liter: 0.6,
      substrate_cycles_used: 3,
      measured_ec: 1.9,
      measured_temp_celsius: 22,
      fertilizer_keys: [
        { key: 'grow', recipe_ml_per_liter: 3 },
        { key: 'bloom' },
      ],
    });
    // Comprehensive expert EC-budget flow: ~35 interactions across every field
    // of the panel, which makes it the longest test in the suite. Measured on
    // an idle 8-core box: 6.2s plain, 10-11s with v8 coverage instrumentation
    // (~1.8x), and 47s with coverage while the box ran another test suite
    // (~4x on top). That last case is what blew the previous 60s budget in CI
    // (#778, H4) — load, not a defect. This raised budget is a mitigation, not
    // a fix: the cost is inherent to the page keeping every panel's form state
    // at page level, so each interaction re-renders all panels. Fixing that
    // means memoising the panels in NutrientCalculationsPage itself.
  }, 120000);

  it('renders the living-soil bypass notice instead of the EC bar', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/ec-budget', () =>
        HttpResponse.json({
          ec_mix: 0,
          ec_net: 0,
          ec_silicate: 0,
          ec_calmag: 0,
          ec_fertilizers: 0,
          ec_ph_reserve: 0,
          ec_final: 0,
          ec_max: 0,
          ec_target: 0,
          ec_at_25_corrected: null,
          tolerance: 0,
          valid: true,
          living_soil_bypass: true,
          segments: [],
          warnings: [],
          dosage_table: [],
          dosage_instructions: [],
        }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);
    const buttons = within(card).getAllByRole('button', { name: /Berechnen/ });
    await user.click(buttons[buttons.length - 1]);

    await waitFor(() => {
      expect(within(card).getByText(/Living Soil: EC-Dosierung nicht anwendbar/)).toBeTruthy();
    });
    // bypass path hides the validity summary
    expect(within(card).queryByText(/EC-Budget gültig/)).toBeNull();
  });

  it('renders an invalid EC-budget result', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/ec-budget', () =>
        HttpResponse.json({
          ec_mix: 0.3,
          ec_net: 1.7,
          ec_silicate: 0,
          ec_calmag: 0,
          ec_fertilizers: 2.0,
          ec_ph_reserve: 0.2,
          ec_final: 2.5,
          ec_max: 2.0,
          ec_target: 1.8,
          ec_at_25_corrected: null,
          tolerance: 0.1,
          valid: false,
          living_soil_bypass: false,
          segments: [],
          warnings: [],
          dosage_table: [],
          dosage_instructions: [],
        }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);
    const buttons = within(card).getAllByRole('button', { name: /Berechnen/ });
    await user.click(buttons[buttons.length - 1]);

    await waitFor(() => {
      expect(within(card).getByText(/EC-Budget überschreitet Obergrenze/)).toBeTruthy();
    });
  });

  it('uses the reverse water-mix result as the EC-budget base water when available', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/water-mix/reverse', () =>
        HttpResponse.json({
          ro_percent: 30,
          effective_profile: {
            ec_ms: 0.22,
            ph: 7,
            alkalinity_ppm: 40,
            calcium_ppm: 10,
            magnesium_ppm: 3,
            chlorine_ppm: 0,
            chloramine_ppm: 0,
          },
        }),
      ),
    );
    let ecBudgetPayload: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/ec-budget', async ({ request }) => {
        ecBudgetPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          ec_mix: 0.22,
          ec_net: 1.6,
          ec_silicate: 0,
          ec_calmag: 0,
          ec_fertilizers: 1.0,
          ec_ph_reserve: 0.1,
          ec_final: 1.5,
          ec_max: 2.0,
          ec_target: 1.8,
          ec_at_25_corrected: null,
          tolerance: 0.1,
          valid: true,
          living_soil_bypass: false,
          segments: [],
          warnings: [],
          dosage_table: [],
          dosage_instructions: [],
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);
    const buttons = within(card).getAllByRole('button', { name: /Berechnen/ });

    // reverse water-mix first populates wmResult
    await user.click(buttons[0]);
    await waitFor(() => {
      expect(within(card).getByText(/Empfohlener RO-Anteil: 30%/)).toBeTruthy();
    });

    // EC budget now derives base_water_ec from the effective profile
    await user.click(buttons[buttons.length - 1]);
    await waitFor(() => {
      expect(within(card).getByText(/EC-Budget gültig/)).toBeTruthy();
    });
    expect(ecBudgetPayload).toMatchObject({ base_water_ec: 0.22 });
  });
});

describe('NutrientCalculationsPage — panel intros and selectors (#610)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders a descriptive intro under every panel heading', async () => {
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });

    expect(screen.getByText(/genaue Dosierung je Dünger/)).toBeTruthy();
    expect(screen.getByText(/Spülplan/)).toBeTruthy();
    expect(screen.getByText(/Ablaufwasser \(Drainage\)/)).toBeTruthy();
    expect(screen.getByText(/bedenkenlos zusammen anmischen/)).toBeTruthy();
    expect(screen.getByText(/Organische Freiland-Dünger/)).toBeTruthy();
    expect(screen.getByText(/mischt zunächst das Basiswasser/)).toBeTruthy();
  });

  it('submits the selected fertilizer key (not free text) from the mixing-protocol autocomplete', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-protocol', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          dosages: [],
          calculated_ec: 1.5,
          ph_adjustment: { needed: false, direction: 'none', delta: 0 },
          warnings: [],
          instructions: [],
          ec_net: 1.2,
          ec_ph_reserve: 0.3,
          valid: true,
        });
      }),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);

    await pickOption(user, within(card).getByLabelText('Düngemittel'), /Grow A/);
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(captured).not.toBeNull();
    });
    expect(captured).toMatchObject({ fertilizer_keys: ['grow'] });
  });

  it('adds and removes rows in the EC-budget fertilizer editor', async () => {
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />, {
      store: createStoreWithExpertise('expert'),
    });
    const card = cardForHeading(/EC-Budget-Kalkulation/);

    // Empty state hint before any row is added.
    expect(within(card).getByText(/Noch keine Dünger hinzugefügt/)).toBeTruthy();

    const addButton = within(card).getByRole('button', { name: /Dünger hinzufügen/ });
    await user.click(addButton);
    await user.click(addButton);

    expect(within(card).getAllByLabelText('Düngemittel')).toHaveLength(2);

    // Remove the first row -> one row left.
    const removeButtons = within(card).getAllByRole('button', { name: /Dünger entfernen/ });
    await user.click(removeButtons[0]);

    expect(within(card).getAllByLabelText('Düngemittel')).toHaveLength(1);
  });
});

describe('NutrientCalculationsPage — mobile rendering', () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    i18n.changeLanguage('de');
    // Force MUI useMediaQuery (breakpoints.down) to report a mobile viewport so
    // DataTable renders the MobileCard branch and its per-row renderers run.
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('renders mixing-protocol dosages as mobile cards', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/nutrient-calculations/mixing-protocol', () =>
        HttpResponse.json({
          dosages: [
            {
              fertilizer_key: 'grow',
              product_name: 'Grow A',
              ml_per_liter: 2.5,
              total_ml: 25,
              ec_contribution: 0.8,
            },
          ],
          calculated_ec: 1.8,
          ph_adjustment: { needed: false, direction: 'none', delta: 0 },
          warnings: [],
          instructions: [],
          ec_net: 1.5,
          ec_ph_reserve: 0.2,
          valid: true,
        }),
      ),
    );
    const user = userEvent.setup({ delay: null });
    renderWithProviders(<NutrientCalculationsPage />);
    const card = cardForHeading(/Mischprotokoll/);
    await user.click(within(card).getByRole('button', { name: /Berechnen/ }));

    await waitFor(() => {
      expect(within(card).getByText('Grow A')).toBeTruthy();
    });
    // MobileCard renders the ml/L field label from the mobileCardRenderer
    expect(within(card).getAllByText(/ml\/L/).length).toBeGreaterThan(0);
  });
});
