/**
 * The tent rules of a location (REQ-053 WP 10.11, W-016): the light-schedule hints in words, the location's own
 * neighbourhood factor and its lighting, written through `PATCH /locations/{key}`.
 */
import { act, cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/i18n/i18n';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import TentRulesSection from './TentRulesSection';
import type { TentHint } from './types';

const BASE = '/api/v1/t/:tenant';

function usePatch() {
  const bodies: unknown[] = [];
  server.use(
    http.patch(`${BASE}/locations/:key`, async ({ request }) => {
      bodies.push(await request.json());
      return HttpResponse.json({ key: 'loc_tent', bed_status: 'active', plan_revision: 3 });
    }),
  );
  return bodies;
}

function renderSection(props: Partial<Parameters<typeof TentRulesSection>[0]> = {}) {
  const onSaved = vi.fn();
  const view = renderWithProviders(
    <TentRulesSection
      locationKey="loc_tent"
      supportsLayout
      adjacencyFactor={null}
      lighting={null}
      hints={[]}
      canEdit
      onSaved={onSaved}
      {...props}
    />,
  );
  return { onSaved, ...view };
}

const CONFLICT: TentHint = {
  code: 'tent.photoperiod_conflict',
  severity: 'warning',
  groups: [
    { photoperiod_hours: 18, plant_count: 2, phase_names: ['Vegetative'] },
    { photoperiod_hours: 12, plant_count: 1, phase_names: [] },
  ],
  unknown_plant_count: 1,
};

afterEach(() => cleanup());

/** #2889: the phase in the hint is worded in the UI language, never the English name the server falls back to. */
describe('TentRulesSection phase names', () => {
  const initialLanguage = i18n.language;

  afterEach(async () => {
    cleanup();
    await act(() => i18n.changeLanguage(initialLanguage));
  });

  const LOCALISED: TentHint = {
    code: 'tent.photoperiod_conflict',
    severity: 'warning',
    groups: [
      {
        photoperiod_hours: 18,
        plant_count: 2,
        phase_names: ['Vegetative'],
        phases: [{ code: 'vegetative', display_name: 'Vegetative', display_name_de: 'Vegetative Phase' }],
      },
      {
        photoperiod_hours: 12,
        plant_count: 1,
        phase_names: ['Flowering'],
        phases: [{ code: 'flowering', display_name: 'Flowering', display_name_de: 'Blüte' }],
      },
    ],
    unknown_plant_count: 0,
  };

  it('names the phases in German in the German UI', async () => {
    await act(() => i18n.changeLanguage('de'));
    renderSection({ hints: [LOCALISED] });

    const alert = screen.getByTestId('tent-hint-photoperiod-conflict');
    expect(alert).toHaveTextContent(
      '18 Stunden Licht für 2 Pflanzen (Vegetative Phase); 12 Stunden Licht für 1 Pflanze (Blüte)',
    );
    expect(alert).not.toHaveTextContent('Flowering');
  });

  it('names the phases in English in the English UI', async () => {
    await act(() => i18n.changeLanguage('en'));
    renderSection({ hints: [LOCALISED] });

    expect(screen.getByTestId('tent-hint-photoperiod-conflict')).toHaveTextContent(
      '18 hours of light for 2 plants (Vegetative); 12 hours of light for 1 plant (Flowering)',
    );
  });

  it('falls back to the app translation of the code, then the English name, then the code', async () => {
    await act(() => i18n.changeLanguage('de'));
    renderSection({
      hints: [
        {
          code: 'tent.photoperiod_conflict',
          severity: 'warning',
          groups: [
            {
              photoperiod_hours: 18,
              plant_count: 3,
              phase_names: ['Bud swell', 'Vegetative', 'zz_custom'],
              phases: [
                // a legacy growth phase: no German catalogue name
                { code: 'bud_swell', display_name: 'Bud swell', display_name_de: '' },
                { code: 'vegetative', display_name: 'Vegetative', display_name_de: '' },
                { code: 'zz_custom', display_name: '', display_name_de: '' },
              ],
            },
            // an older backend sends no `phases`
            { photoperiod_hours: 12, plant_count: 1, phase_names: ['Flowering'] },
          ],
          unknown_plant_count: 0,
        },
      ],
    });

    expect(screen.getByTestId('tent-hint-photoperiod-conflict')).toHaveTextContent(
      '18 Stunden Licht für 3 Pflanzen (Bud swell, Vegetativ, zz_custom); 12 Stunden Licht für 1 Pflanze (Blüte)',
    );
  });
});

describe('TentRulesSection', () => {
  it('describes a photoperiod conflict in words, without its code', () => {
    renderSection({ hints: [CONFLICT] });

    const alert = screen.getByTestId('tent-hint-photoperiod-conflict');
    expect(alert).toHaveTextContent('Different light needs under one lamp');
    expect(alert).toHaveTextContent('According to the species profile or the entered phase profile');
    expect(alert).toHaveTextContent('18 hours of light for 2 plants (Vegetative); 12 hours of light for 1 plant');
    expect(alert).toHaveTextContent(
      'For 1 more plant no light duration from the species profile or entered by you exists; it is not counted.',
    );
    expect(alert).not.toHaveTextContent('tent.photoperiod_conflict');
  });

  it('says when the light needs of some plants are unknown', () => {
    renderSection({
      hints: [{ code: 'tent.photoperiod_unknown', severity: 'info', groups: [], unknown_plant_count: 2 }],
    });

    const alert = screen.getByTestId('tent-hint-photoperiod-unknown');
    expect(alert).toHaveTextContent(
      'For 2 plants no light duration from the species profile or entered by you exists for their current phase, ' +
        'at most a default or template value.',
    );
    // #2857: the grower is told what to do - a default or template value never counts.
    expect(alert).toHaveTextContent('Enter the light duration in the phase profile of the species, then the plants count.');
  });

  /** #2857: the German text says why a stored value does not count and what to do, in the informal "du". */
  describe('in the German UI', () => {
    const initialLanguage = i18n.language;

    afterEach(async () => {
      cleanup();
      await act(() => i18n.changeLanguage(initialLanguage));
    });

    it('says that only a sourced light duration counts and how to give one', async () => {
      await act(() => i18n.changeLanguage('de'));
      renderSection({
        hints: [{ code: 'tent.photoperiod_unknown', severity: 'info', groups: [], unknown_plant_count: 1 }],
      });

      const alert = screen.getByTestId('tent-hint-photoperiod-unknown');
      expect(alert).toHaveTextContent('Lichtbedarf nicht für alle Pflanzen bekannt');
      expect(alert).toHaveTextContent(
        'Für 1 Pflanze ist zur aktuellen Phase keine Lichtdauer aus dem Steckbrief oder von dir eingetragen, ' +
          'höchstens ein Standard- oder Vorlagenwert.',
      );
      expect(alert).toHaveTextContent('Trag die Lichtdauer im Phasenprofil der Art ein, dann zählt die Pflanze mit.');
      // No sentence starts with the formal "Sie".
      expect(alert.textContent ?? '').not.toMatch(/(^|[.!?;:]\s*)Sie\b/);
    });

    it('names the source of the conflicting values', async () => {
      await act(() => i18n.changeLanguage('de'));
      renderSection({ hints: [CONFLICT] });

      const alert = screen.getByTestId('tent-hint-photoperiod-conflict');
      expect(alert).toHaveTextContent('Laut Steckbrief oder eingetragenem Phasenprofil brauchen die Pflanzen hier');
      expect(alert).not.toHaveTextContent('hinterlegten Phasenprofilen');
      expect(alert.textContent ?? '').not.toMatch(/(^|[.!?;:]\s*)Sie\b/);
    });
  });

  it('names the plants whose light needs are unknown, the first five and how many more', () => {
    renderSection({
      hints: [
        {
          code: 'tent.photoperiod_unknown',
          severity: 'info',
          groups: [],
          unknown_plant_count: 7,
          unknown_plant_names: ['Basil', 'Chili', 'Gelato', 'Mint', 'Thyme'],
        },
      ],
    });

    expect(screen.getByTestId('tent-hint-unknown-plants')).toHaveTextContent(
      'Affected: Basil, Chili, Gelato, Mint, Thyme and 2 more.',
    );
  });

  it('names all unknown plants when they fit', () => {
    renderSection({
      hints: [
        {
          code: 'tent.photoperiod_unknown',
          severity: 'info',
          groups: [],
          unknown_plant_count: 2,
          unknown_plant_names: ['Basil', 'Chili'],
        },
      ],
    });

    expect(screen.getByTestId('tent-hint-unknown-plants')).toHaveTextContent('Affected: Basil, Chili.');
  });

  it('writes the factor and the lighting in one PATCH and keeps a stored fixture footprint', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    const fixture = { kind: 'rect', origin: [0.1, 0.1], width_m: 0.6, length_m: 0.6 };
    const { onSaved } = renderSection({ lighting: { fixture_geometry: fixture } });

    await user.type(screen.getByRole('spinbutton', { name: 'Neighbourhood factor' }), '2.5');
    await user.type(screen.getByRole('spinbutton', { name: 'Lamp height' }), '180');
    await user.type(screen.getByRole('spinbutton', { name: 'Distance to the plants' }), '40');
    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(bodies).toEqual([
      {
        adjacency_factor: 2.5,
        lighting: { lamp_height_cm: 180, canopy_distance_cm: 40, fixture_geometry: fixture },
      },
    ]);
  });

  it('refuses a canopy farther from the lamp than the lamp is high, before any request', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    renderSection();

    await user.type(screen.getByRole('spinbutton', { name: 'Lamp height' }), '50');
    await user.type(screen.getByRole('spinbutton', { name: 'Distance to the plants' }), '80');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(await screen.findByText('The distance to the plants cannot be larger than the lamp height.')).toBeVisible();
    expect(bodies).toEqual([]);
  });

  it('is read-only for a viewer', () => {
    renderSection({ canEdit: false, adjacencyFactor: 2 });

    expect(screen.getByRole('spinbutton', { name: 'Neighbourhood factor' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
  });

  it('shows nothing for a location without a layout and without hints', () => {
    renderSection({ supportsLayout: false });

    expect(screen.queryByTestId('tent-rules-section')).not.toBeInTheDocument();
  });

  it('has no critical accessibility violation', async () => {
    const { container } = renderSection({ hints: [CONFLICT] });
    await expectNoA11yViolations(container);
  });
});
