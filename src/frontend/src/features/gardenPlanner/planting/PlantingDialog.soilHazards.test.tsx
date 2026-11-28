/**
 * Soil hazards of the bed in the planting dialog (REQ-053 §11.3a Nr. 4 and 6, GP-FR-193, #2888 F-21).
 *
 * The dialog words what `validate-planting` answers and computes nothing itself (acceptance-6): the strength, the
 * "Trotzdem pflanzen" step and the lines follow the server answer, also on a bed whose rotation check is off
 * (acceptance-1). A warning asks for a reason, a hint does not (acceptance-2/3); the residual hint of a loss follows
 * its cause class (acceptance-7).
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import PlantingDialog from './PlantingDialog';
import { BED_GEOMETRY, hint, species, usePlantingBackend } from './plantingTestKit';
import type { RotationFinding, RotationSeverity } from './plantingTypes';

const CABBAGE = species('sp_cabbage', 'Cabbage', { spacing_cm: '40', row_spacing_cm: '50' });

function renderDialog() {
  return renderWithProviders(
    <PlantingDialog
      bedKey="loc_b03"
      bedName="Raised bed 3"
      geometry={BED_GEOMETRY}
      gridStepM={0.1}
      sunExposure="unknown"
      onClose={vi.fn()}
      onPlanted={vi.fn()}
    />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
}

async function chooseCabbage(user: ReturnType<typeof userEvent.setup>) {
  const entry = await screen.findByTestId('planting-entry-0');
  const box = within(entry).getByRole('combobox', { name: /^Species/ });
  await user.click(box);
  await user.type(box, 'Cabb');
  await user.click(await screen.findByRole('option', { name: /Cabbage/ }));
}

async function hintsDone() {
  await waitFor(() => expect(screen.queryByText(/^Checking /)).toBeNull());
  await waitFor(() => expect(screen.getByTestId('planting-submit')).toBeEnabled());
}

function soilFinding(
  code: string,
  severity: RotationSeverity,
  extra: Partial<RotationFinding> = {},
): RotationFinding {
  return {
    severity,
    code,
    message: 'english server text',
    species_key: 'sp_cabbage',
    hazard: 'clubroot',
    hazard_confirmed_at: '2022-07-01',
    hazard_stage: 'pause',
    hazard_until: null,
    host_level: 'family',
    host_name: 'Brassicaceae',
    ...extra,
  };
}

/** The backend options: the dialog's one species and the `validate-planting` answer the test describes. */
function answer(findings: RotationFinding[], severity: RotationSeverity, applicable = true) {
  return {
    species: [CABBAGE],
    hints: {
      sp_cabbage: hint({
        species_key: 'sp_cabbage',
        severity,
        rotation_applicable: applicable,
        not_applicable_reason: applicable ? null : 'rotation.not_applicable.rotation_exempt',
        rotation: findings,
      }),
    },
  };
}

/** Choose the species and wait until its hints are in. */
async function openPanel() {
  const user = userEvent.setup();
  renderDialog();
  await chooseCabbage(user);
  const panel = await screen.findByTestId('planting-hint-sp_cabbage');
  await hintsDone();
  return panel;
}

beforeEach(() => localStorage.clear());
afterEach(() => cleanup());

describe('a host of a soil hazard of the bed (acceptance-1)', () => {
  it('warns inside the pause with its end and asks for a reason, never blocks', async () => {
    usePlantingBackend(
      answer(
        [soilFinding('soil_hazard.pause', 'WARNING', { hazard_until: '2029-07-01' })],
        'WARNING',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('Clubroot was confirmed in this bed on');
    expect(panel).toHaveTextContent('this plant is a host (family Brassicaceae)');
    expect(panel).toHaveTextContent('keeping host plants out of this bed until 2029');
    expect(panel).not.toHaveTextContent('english server text');
    expect(screen.getByTestId('planting-override-check')).toBeInTheDocument();
    // The server's code, strength and stage on the line - what the browser test compares with the route.
    const line = panel.querySelector('li[data-code="soil_hazard.pause"]');
    expect(line).not.toBeNull();
    expect(line).toHaveAttribute('data-severity', 'WARNING');
    expect(line).toHaveAttribute('data-hazard-stage', 'pause');
  });

  it('names the location above the bed that holds an inherited hazard (review S3)', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.no_evidenced_pause', 'WARNING', {
            hazard: 'juglone',
            hazard_stage: 'no_evidenced_pause',
            hazard_location_key: 'loc_garden',
            hazard_location_name: 'Obstwiese',
          }),
        ],
        'WARNING',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('was recorded at “Obstwiese” above this bed on');
    expect(panel).not.toHaveTextContent('confirmed in this bed');
  });

  it('words juglone without a pathogen and without advice to renew the substrate (confirm review SF-2)', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.no_evidenced_pause', 'WARNING', {
            hazard: 'juglone',
            hazard_stage: 'no_evidenced_pause',
            host_level: 'species',
            host_name: 'Solanum lycopersicum',
          }),
          soilFinding('soil_hazard.uncertain_host', 'INFO', {
            hazard: 'juglone',
            hazard_stage: 'no_evidenced_pause',
            host_level: 'genus',
            host_name: 'Brassica',
          }),
        ],
        'WARNING',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('Juglone comes from the roots and leaves of the walnut tree');
    expect(panel).toHaveTextContent('The warning stays until a lead removes the entry');
    expect(panel).toHaveTextContent("sensitive to juglone from the walnut tree's roots");
    expect(panel).not.toHaveTextContent('renew the substrate');
    expect(panel).not.toHaveTextContent('pathogen');
  });

  it('shows the hazard on a bed whose rotation check is off, with a note why it still applies', async () => {
    usePlantingBackend(
      answer(
        [soilFinding('soil_hazard.pause', 'WARNING', { hazard_until: '2029-07-01' })],
        'WARNING',
        false,
      ),
    );
    const panel = await openPanel();
    expect(within(panel).getByTestId('planting-hint-sp_cabbage-rotation-off')).toHaveTextContent(
      'The crop rotation check is off for this bed. Soil hazards still apply',
    );
    expect(panel).toHaveTextContent('until 2029');
    expect(screen.getByTestId('planting-override-check')).toBeInTheDocument();
  });

  it('says only "no rotation check" for a bed that is off and has nothing to report', async () => {
    usePlantingBackend(answer([], 'OK', false));
    const panel = await openPanel();
    expect(panel).toHaveTextContent('No crop rotation check applies to this bed');
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
  });

  it('words the residual risk after the pause as a hint with its end, without a reason', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.residual', 'INFO', {
            hazard_stage: 'residual',
            hazard_until: '2037-07-01',
          }),
        ],
        'INFO',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('can survive in the soil at least until 2037; after that, Kamerplanter no longer reports it');
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
  });

  it('words a residual risk without an evidenced survival as open until a lead removes the hazard', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.residual', 'INFO', {
            hazard: 'cyst_nematode',
            hazard_stage: 'residual',
          }),
        ],
        'INFO',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('Cyst nematodes was confirmed');
    expect(panel).toHaveTextContent('until a lead removes the soil hazard from the bed');
  });
});

describe('no evidenced pause (acceptance-2)', () => {
  it('warns without a time statement', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.no_evidenced_pause', 'WARNING', {
            hazard: 'white_rot',
            hazard_stage: 'no_evidenced_pause',
            host_level: 'genus',
            host_name: 'Allium',
          }),
        ],
        'WARNING',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('How long to pause with host plants is not reliably known');
    expect(panel).toHaveTextContent('(genus Allium)');
    expect(panel).not.toHaveTextContent(/until \d{4}/);
    expect(screen.getByTestId('planting-override-check')).toBeInTheDocument();
  });
});

describe('soft hazards and uncertain hosts (acceptance-3)', () => {
  it('gives a hint for a soft hazard and asks for no reason', async () => {
    usePlantingBackend(
      answer([soilFinding('soil_hazard.soft', 'INFO', { hazard: 'root_knot_nematode' })], 'INFO'),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('Root-knot nematodes was confirmed');
    expect(panel).toHaveTextContent('attacks almost every vegetable');
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
  });

  it('gives a hint for a host whose evidence is uncertain', async () => {
    usePlantingBackend(
      answer(
        [
          soilFinding('soil_hazard.uncertain_host', 'INFO', {
            hazard: 'verticillium',
            host_name: 'Solanaceae',
          }),
        ],
        'INFO',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent(
      'Whether it attacks this plant (family Solanaceae) is not reliably known',
    );
  });
});

describe('one source of truth (acceptance-6)', () => {
  it('follows the strength the server sends, not one it would derive from the code', async () => {
    // A contrived answer: a pause code sent as a hint. The dialog must not upgrade it on its own.
    const backend = usePlantingBackend(
      answer([soilFinding('soil_hazard.pause', 'INFO', { hazard_until: '2029-07-01' })], 'INFO'),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('until 2029');
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
    expect(backend.validations).toEqual([{ species_key: 'sp_cabbage' }]);
  });

  it('lists a rotation finding of an earlier year next to the soil hazard unchanged', async () => {
    usePlantingBackend(
      answer(
        [
          {
            severity: 'CRITICAL',
            code: 'rotation.pause_not_elapsed',
            message: 'x',
            family_key: 'f1',
            family_name: 'Brassicaceae',
            years_since: 1,
            pause_years: 4,
            pause_source: 'family',
          },
          soilFinding('soil_hazard.pause', 'WARNING', { hazard_until: '2029-07-01' }),
        ],
        'CRITICAL',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('The family Brassicaceae stood in this bed 1 year ago.');
    expect(panel).toHaveTextContent('until 2029');
  });
});

describe('the residual hint follows the cause class (acceptance-7)', () => {
  const replant = (
    code: string,
    severity: RotationSeverity,
    cause: string,
    cls: string,
  ): RotationFinding => ({
    severity,
    code,
    message: 'english server text',
    family_key: 'f1',
    family_name: 'Brassicaceae',
    species_key: 'sp_cabbage',
    termination_cause: cause,
    failure_cause_class: cls,
  });

  it('a leaf disease says to remove the remains and keep them off the compost', async () => {
    usePlantingBackend(
      answer(
        [replant('rotation.replant_foliar_disease', 'INFO', 'disease', 'disease_foliar')],
        'INFO',
      ),
    );
    const panel = await openPanel();
    expect(panel).toHaveTextContent('keep them off the garden compost');
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
  });

  it.each([
    ['disease', 'disease_soil', 'died from a soil-borne disease'],
    ['pest', 'pest_soil', 'died from pests in the soil'],
    // The class decides, not the cause: an "unknown" loss the grower placed in the soil as pests.
    ['unknown', 'pest_soil', 'died from pests in the soil'],
  ])(
    'an unconfirmed soil-borne %s is a warning that asks for a reason',
    async (cause, cls, text) => {
      usePlantingBackend(
        answer([replant('rotation.replant_soil_borne', 'WARNING', cause, cls)], 'WARNING'),
      );
      const panel = await openPanel();
      expect(panel).toHaveTextContent(text);
      expect(screen.getByTestId('planting-override-check')).toBeInTheDocument();
    },
  );
});
