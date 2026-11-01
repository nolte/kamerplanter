/**
 * The planting dialog (REQ-053 WP 3.6: GP-FR-060…073, GP-FR-132, GP-ACC-047, W-016.5): prefill order, the
 * live preview, hints with a strength before the layout, "Trotzdem pflanzen" with a reason, alternating
 * rows, freely placed positions with the yellow ring, the pot check and the field-mode shortcut.
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { delay, http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { getActiveTenantSlug } from '@/api/client';
import { server } from '@/test/mocks/server';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import PlantingDialog from './PlantingDialog';
import type { SunExposure } from '../model/types';
import {
  BASE,
  BED_GEOMETRY,
  hint,
  species,
  usePlantingBackend,
  type PlantingBackend,
} from './plantingTestKit';

const TOMATO = species('sp_tomato', 'Tomato', { spacing_cm: '60', row_spacing_cm: '80', mature_width_cm: '50' });
const CARROT = species('sp_carrot', 'Carrot', { spacing_cm: '5', row_spacing_cm: '80' });
const BARE = species('sp_bare', 'Rhubarb');

function renderDialog(
  onPlanted = vi.fn(),
  onClose = vi.fn(),
  sunExposure: SunExposure = 'unknown',
) {
  const view = renderWithProviders(
    <PlantingDialog
      bedKey="loc_b03"
      bedName="Raised bed 3"
      geometry={BED_GEOMETRY}
      sunExposure={sunExposure}
      onClose={onClose}
      onPlanted={onPlanted}
    />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
  return { ...view, onPlanted, onClose };
}

async function choose(user: ReturnType<typeof userEvent.setup>, card: number, name: string) {
  const entry = await screen.findByTestId(`planting-entry-${card}`);
  const box = within(entry).getByRole('combobox', { name: /^Species/ });
  await user.click(box);
  await user.type(box, name.slice(0, 4));
  await user.click(await screen.findByRole('option', { name: new RegExp(name) }));
}

const lastUsedKey = () => `kp.gardenPlanner.planting.lastUsed.${getActiveTenantSlug() ?? 'default'}`;
/** Wait until every chosen species has been checked: the dialog does not submit before. */
async function hintsDone() {
  await waitFor(() => expect(screen.queryByText(/^Checking /)).toBeNull());
  await waitFor(() => expect(screen.getByTestId('planting-submit')).toBeEnabled());
}

const MIXED = '/planting-runs/mixed-culture';
const runPosts = (backend: PlantingBackend) => backend.seen.filter((s) => s.url === MIXED);
type SentRun = { name: string; entry: Record<string, unknown> & { quantity: number }; free_points?: number[][]; container_volume_l?: number };
const sentRuns = (backend: PlantingBackend): SentRun[] => (runPosts(backend)[0].body as { runs: SentRun[] }).runs;

beforeEach(() => localStorage.clear());
afterEach(() => cleanup());

describe('prefill and preview', () => {
  it('fills the spacings from the Steckbrief, says so and shows how many plants fit', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();

    await choose(user, 0, 'Tomato');

    const entry = screen.getByTestId('planting-entry-0');
    expect(within(entry).getByTestId('planting-entry-0-spacing')).toHaveValue('60');
    expect(within(entry).getByText('Taken from the species profile.')).toBeInTheDocument();
    const result = await within(entry).findByTestId('planting-entry-0-result');
    expect(result).toHaveTextContent(/\d+ plants, at most \d+ fit/);
    // The preview is drawn on the bed.
    expect(screen.getByTestId('planting-canvas')).toBeInTheDocument();
  });

  it('leaves the spacing empty with a hint when neither the Steckbrief nor last use has a value (E-10)', async () => {
    usePlantingBackend({ species: [BARE] });
    const user = userEvent.setup();
    renderDialog();

    await choose(user, 0, 'Rhubarb');

    const entry = screen.getByTestId('planting-entry-0');
    expect(within(entry).getByTestId('planting-entry-0-spacing')).toHaveValue('');
    expect(within(entry).getByText('The species profile gives no value. Enter the spacing yourself.')).toBeInTheDocument();
  });

  it('falls back to what the tenant used last for the species (F-11)', async () => {
    localStorage.setItem(
      lastUsedKey(),
      JSON.stringify({ sp_bare: { spacing_cm: 45 } }),
    );
    usePlantingBackend({ species: [BARE] });
    const user = userEvent.setup();
    renderDialog();

    await choose(user, 0, 'Rhubarb');

    const entry = screen.getByTestId('planting-entry-0');
    expect(within(entry).getByTestId('planting-entry-0-spacing')).toHaveValue('45');
    expect(within(entry).getByText('Last used for this species.')).toBeInTheDocument();
  });

  it('shows the server count once it answers, where it differs from the port', async () => {
    usePlantingBackend({
      species: [TOMATO],
      preview: () => ({ slots: [], count: 7, capacity_max: 9, warnings: [] }),
    });
    const user = userEvent.setup();
    renderDialog();

    await choose(user, 0, 'Tomato');

    await waitFor(() =>
      expect(screen.getByTestId('planting-entry-0-result')).toHaveTextContent('7 plants, at most 9 fit'),
    );
  });

  it('warns when the spacing is below 70 % of the mature width', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    const spacing = screen.getByTestId('planting-entry-0-spacing');
    await user.clear(spacing);
    await user.type(spacing, '20');

    expect(await screen.findByText(/below 70 % of the mature width \(50 cm\)/)).toBeInTheDocument();
  });

  it('names the refusal of a spacing out of range instead of a blank preview', async () => {
    usePlantingBackend({ species: [BARE] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Rhubarb');

    await user.type(screen.getByTestId('planting-entry-0-spacing'), '2');

    expect(await screen.findByTestId('planting-entry-0-result')).toHaveTextContent(
      'The spacing must be between 5 and 1500 cm.',
    );
  });
});

describe('hints with a strength (GP-FR-132, GP-ACC-047)', () => {
  const critical = hint({
    species_key: 'sp_tomato',
    severity: 'CRITICAL',
    rotation: [
      {
        severity: 'CRITICAL',
        code: 'rotation.pause_not_elapsed',
        message: 'english server text',
        family_key: 'Solanaceae',
        family_name: 'Solanaceae',
        years_since: 1,
        pause_years: 4,
        pause_source: 'family',
      },
    ],
  });

  it('shows the hint with reason and strength before the layout is chosen, and does not block', async () => {
    usePlantingBackend({ species: [TOMATO], hints: { sp_tomato: critical } });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    const panel = await screen.findByTestId('planting-hint-sp_tomato');
    expect(panel).toHaveTextContent('critical');
    expect(panel).toHaveTextContent('The family Solanaceae stood in this bed 1 year(s) ago');
    expect(panel).toHaveTextContent('rotation pause is 4 years (value of the family)');
    // The hint comes before the entry's layout field in the document.
    const layout = screen.getByTestId('planting-entry-0-layout');
    expect(panel.compareDocumentPosition(layout) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('explains the terms of the hints and of the spacing fields (GP-UX-011)', async () => {
    usePlantingBackend({ species: [TOMATO], hints: { sp_tomato: critical } });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    const hints = await screen.findByTestId('planting-hints');
    const glossary = within(hints).getByRole('group', { name: 'Terms explained' });
    for (const name of [/^Crop rotation — /, /^Rotation pause — /, /^Companion planting — /, /^Perennial crop — /]) {
      expect(within(glossary).getByRole('button', { name })).toBeInTheDocument();
    }
    const entry = screen.getByTestId('planting-entry-0');
    expect(within(entry).getByRole('button', { name: /^Plant spacing — / })).toBeInTheDocument();
    await user.click(within(entry).getByTestId('planting-entry-0-more'));
    expect(await within(entry).findByRole('button', { name: /^Edge margin — / })).toBeInTheDocument();
  });

  const findingOf = (code: string, family: { family_key: string; family_name?: string | null }) =>
    hint({
      species_key: 'sp_cauli',
      severity: 'WARNING',
      rotation: [
        {
          severity: 'WARNING',
          code,
          message: 'english server text',
          ...family,
          years_since: 1,
          pause_years: 4,
          pause_source: 'family',
        },
      ],
    });

  it('names the family of the finding by the name the server sends, not by its database key', async () => {
    const cauliflower = species('sp_cauli', 'Cauliflower', { spacing_cm: '50' });
    const named = findingOf('rotation.pause_not_elapsed', { family_key: '5504', family_name: 'Brassicaceae' });
    usePlantingBackend({ species: [cauliflower], hints: { sp_cauli: named } });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Cauliflower');

    const panel = await screen.findByTestId('planting-hint-sp_cauli');
    expect(panel).toHaveTextContent('The family Brassicaceae stood in this bed 1 year(s) ago');
    expect(panel).not.toHaveTextContent('5504');
  });

  it.each([
    ['rotation.pause_not_elapsed', 'The same family stood in this bed 1 year(s) ago'],
    ['rotation.pest_risk', 'High pest risk with a family that stood here recently'],
  ])('leaves the family out of the %s sentence when it has no name and never shows the key', async (code, text) => {
    // The catalogue knows the name of the family, but the server sent none: the client does not look it up.
    const cauliflower = species('sp_cauli', 'Cauliflower', {
      spacing_cm: '50',
      family_key: '5504',
      family_name: 'Brassicaceae',
    });
    const unnamed = findingOf(code, { family_key: '5504', family_name: null });
    usePlantingBackend({ species: [cauliflower], hints: { sp_cauli: unnamed } });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Cauliflower');

    const panel = await screen.findByTestId('planting-hint-sp_cauli');
    expect(panel).toHaveTextContent(text);
    expect(panel).not.toHaveTextContent('5504');
    expect(panel).not.toHaveTextContent('Brassicaceae');
  });

  it('plants nothing until "Plant anyway" is confirmed with a reason, then stores the reason on the run', async () => {
    const backend = usePlantingBackend({ species: [TOMATO], hints: { sp_tomato: critical } });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await screen.findByTestId('planting-hint-sp_tomato');
    await screen.findByText(/plants, at most/);
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));
    expect(runPosts(backend)).toHaveLength(0);

    await user.click(screen.getByTestId('planting-override-check'));
    await user.click(screen.getByTestId('planting-submit'));
    expect(await screen.findByText('Give a reason to plant anyway.')).toBeInTheDocument();
    expect(runPosts(backend)).toHaveLength(0);

    await user.type(screen.getByTestId('planting-override-reason'), 'No other bed is free');
    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalled());
    const [post] = runPosts(backend);
    expect(post.body).toMatchObject({
      rotation_override_reason: 'No other bed is free',
      location_key: 'loc_b03',
      plan_role: 'main_crop',
      source: 'manual',
    });
  });

  it('asks for no reason when nothing is amiss, and sends none', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await screen.findByText(/No hint on crop rotation or neighbours/);
    await screen.findByText(/plants, at most/);
    expect(screen.queryByTestId('planting-override-check')).toBeNull();
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalledWith(expect.objectContaining({ runKeys: ['run_1'], quick: false })));
    expect(runPosts(backend)[0].body).not.toHaveProperty('rotation_override_reason');
  });

  it('says the check was not possible instead of showing an all-clear when the request fails', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const { server } = await import('@/test/mocks/server');
    const { http, HttpResponse } = await import('msw');
    server.use(
      http.post('/api/v1/t/:tenant/locations/:key/validate-planting', () =>
        HttpResponse.json({ error_code: 'INTERNAL', message: 'boom', details: [] }, { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    expect(await screen.findByText(/Crop rotation could not be checked/)).toBeInTheDocument();
    expect(screen.queryByText(/No hint on crop rotation/)).toBeNull();
  });
});

describe('what is sent', () => {
  it('plans "as many as fit" with the previewed count and the layout fields of the entry', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    const result = await screen.findByTestId('planting-entry-0-result');
    const fit = Number(/at most (\d+) fit/.exec(result.textContent ?? '')?.[1]);
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(runPosts(backend)).toHaveLength(1));
    const [{ entry }] = sentRuns(backend);
    expect(entry).toMatchObject({
      species_key: 'sp_tomato',
      quantity: fit,
      id_prefix: 'TOM',
      spacing_cm: 60,
      layout_strategy: 'grid',
      row_direction: 'along_length',
    });
  });

  it('plans a fixed number when one is given', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(screen.getByTestId('planting-entry-0-count-number'));
    await user.type(screen.getByTestId('planting-entry-0-count'), '3');
    await screen.findByText('3 plants, at most', { exact: false });
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(runPosts(backend)).toHaveLength(1));
    expect(sentRuns(backend)[0].entry.quantity).toBe(3);
  });

  it('refuses a missing spacing with the field error and sends nothing', async () => {
    const backend = usePlantingBackend({ species: [BARE] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Rhubarb');
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    expect(await screen.findByText('Enter the plant spacing.')).toBeInTheDocument();
    expect(runPosts(backend)).toHaveLength(0);
  });

  it('remembers the spacing for the species after a planting (F-11)', async () => {
    usePlantingBackend({ species: [BARE] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Rhubarb');
    await user.type(screen.getByTestId('planting-entry-0-spacing'), '45');
    await screen.findByText(/plants, at most/);
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalled());
    expect(JSON.parse(localStorage.getItem(lastUsedKey()) ?? '{}')).toEqual({
      sp_bare: { spacing_cm: 45, layout_strategy: 'grid' },
    });
  });

  it('records plants at once through the field-mode shortcut when they are in the ground already', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await screen.findByText(/plants, at most/);

    await hintsDone();
    await user.click(screen.getByTestId('planting-already'));
    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalledWith({ runKeys: ['run_q'], plantCount: 2, quick: true }));
    const post = backend.seen.find((s) => s.url === '/locations/loc_b03/quick-planting');
    expect(post?.body).toMatchObject({ species_key: 'sp_tomato', spacing_cm: 60, layout_strategy: 'grid' });
    expect(runPosts(backend)).toHaveLength(0);
  });
});

describe('site fit (GP-FR-160, E-05, TC-053-037)', () => {
  const SUNNY = species('sp_tomato', 'Tomato', { spacing_cm: '60', light_requirement: 'full_sun' });

  it('shows a red verdict in words for a full-sun crop on a shade bed, and does not block', async () => {
    const backend = usePlantingBackend({ species: [SUNNY] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog(vi.fn(), vi.fn(), 'shade');
    await choose(user, 0, 'Tomato');

    const verdict = await screen.findByTestId('planting-site-fit-sp_tomato');
    expect(verdict).toHaveTextContent('site poorly suited');
    expect(verdict).toHaveTextContent(/Bed: Shade — Tomato .* needs full sun\./);
    expect(verdict).toHaveTextContent('The bed is too shady.');
    expect(verdict).toHaveAttribute('role', 'alert');

    await screen.findByText(/plants, at most/);
    await hintsDone();
    await user.click(screen.getByTestId('planting-submit'));

    // No reason is asked for, nothing is refused: a site hint is advice only.
    await waitFor(() => expect(onPlanted).toHaveBeenCalled());
    expect(runPosts(backend)[0].body).not.toHaveProperty('rotation_override_reason');
  });

  it('gives no hint when the bed class is unknown', async () => {
    usePlantingBackend({ species: [SUNNY] });
    const user = userEvent.setup();
    renderDialog(vi.fn(), vi.fn(), 'unknown');
    await choose(user, 0, 'Tomato');
    await screen.findByTestId('planting-hint-sp_tomato');

    expect(screen.queryByTestId('planting-site-fit-sp_tomato')).toBeNull();
  });

  it('gives no hint when the species has no recorded light requirement, whatever its tolerance says (E-05)', async () => {
    const tolerant = species('sp_tomato', 'Tomato', { spacing_cm: '60', shade_tolerance: 'deep_shade' });
    usePlantingBackend({ species: [tolerant] });
    const user = userEvent.setup();
    renderDialog(vi.fn(), vi.fn(), 'shade');
    await choose(user, 0, 'Tomato');
    await screen.findByTestId('planting-hint-sp_tomato');

    expect(screen.queryByTestId('planting-site-fit-sp_tomato')).toBeNull();
  });

  it('widens to yellow when the tolerance covers the bed, and says when it is not recorded', async () => {
    usePlantingBackend({
      species: [species('sp_tomato', 'Tomato', { spacing_cm: '60', light_requirement: 'full_sun', shade_tolerance: 'partial_shade' })],
    });
    const user = userEvent.setup();
    const first = renderDialog(vi.fn(), vi.fn(), 'partial_shade');
    await choose(user, 0, 'Tomato');
    const covered = await screen.findByTestId('planting-site-fit-sp_tomato');
    expect(covered).toHaveTextContent('site only partly suited');
    expect(covered).toHaveTextContent('it grows down to Partial shade');
    first.unmount();

    usePlantingBackend({ species: [SUNNY] });
    renderDialog(vi.fn(), vi.fn(), 'partial_shade');
    await choose(user, 0, 'Tomato');
    const unknown = await screen.findByTestId('planting-site-fit-sp_tomato');
    expect(unknown).toHaveTextContent('Tolerance unknown');
  });

  it('is green on the matching bed', async () => {
    usePlantingBackend({ species: [SUNNY] });
    const user = userEvent.setup();
    renderDialog(vi.fn(), vi.fn(), 'full_sun');
    await choose(user, 0, 'Tomato');

    expect(await screen.findByTestId('planting-site-fit-sp_tomato')).toHaveTextContent('site well suited');
  });
});

describe('submit waits for the hints', () => {
  it('cannot be pressed while a species is still being checked, so a warning cannot be skipped', async () => {
    const { server } = await import('@/test/mocks/server');
    const { http, HttpResponse, delay } = await import('msw');
    const backend = usePlantingBackend({ species: [TOMATO] });
    server.use(
      http.post('/api/v1/t/:tenant/locations/:key/validate-planting', async () => {
        await delay(400);
        return HttpResponse.json(hint({ species_key: 'sp_tomato', severity: 'CRITICAL' }));
      }),
    );
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    expect(screen.getByTestId('planting-submit')).toBeDisabled();
    await hintsDone();
    expect(runPosts(backend)).toHaveLength(0);
  });

  it('is not held back by a check that failed: the hint is shown as unknown', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const { server } = await import('@/test/mocks/server');
    const { http, HttpResponse } = await import('msw');
    server.use(
      http.post('/api/v1/t/:tenant/locations/:key/validate-planting', () =>
        HttpResponse.json({ error_code: 'INTERNAL', message: 'boom', details: [] }, { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await screen.findByText(/Crop rotation could not be checked/);

    expect(screen.getByTestId('planting-submit')).toBeEnabled();
  });
});

describe('already planted and edge margins', () => {
  it('cannot be combined: the shortcut has no margin fields, so the plants would not stand where the preview shows', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(screen.getByTestId('planting-entry-0-more'));
    const margin = await screen.findByLabelText('Edge margin along the row');
    await user.type(margin, '10');

    expect(screen.getByTestId('planting-already')).toBeDisabled();
    expect(screen.getByTestId('planting-already-margins')).toBeInTheDocument();
  });
});

describe('mixed culture (GP-FR-070)', () => {
  it('creates one run per species - a monoculture run holds one entry - with disjoint rows and the same row spacing', async () => {
    const backend = usePlantingBackend({ species: [TOMATO, CARROT] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(screen.getByTestId('planting-add-entry'));
    await choose(user, 1, 'Carrot');
    await waitFor(() =>
      expect(within(screen.getByTestId('planting-entry-1')).getByTestId('planting-entry-1-result')).toHaveTextContent(/plants/),
    );
    // The second entry has no layout of its own while the rows alternate.
    expect(within(screen.getByTestId('planting-entry-1')).getByText('This species shares the rows with species 1.')).toBeInTheDocument();
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalledWith(expect.objectContaining({ runKeys: ['run_1', 'run_2'] })));
    // One request carries every species: the server writes all runs in one transaction.
    expect(runPosts(backend)).toHaveLength(1);
    const runs = sentRuns(backend);
    expect(runs).toHaveLength(2);
    const [first, second] = runs.map((run) => run.entry as unknown as { row_assignment: number[]; layout_strategy: string; species_key: string });
    expect([first.species_key, second.species_key]).toEqual(['sp_tomato', 'sp_carrot']);
    expect(first.row_assignment.length).toBeGreaterThan(0);
    expect(second.row_assignment.length).toBeGreaterThan(0);
    expect(first.row_assignment.filter((row) => second.row_assignment.includes(row))).toEqual([]);
    expect(second.layout_strategy).toBe(first.layout_strategy);
  });

  it('creates nothing and takes nothing back when the mixed culture is refused - the server wrote nothing', async () => {
    const backend = usePlantingBackend({ species: [TOMATO, CARROT], failRun: true });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(screen.getByTestId('planting-add-entry'));
    await choose(user, 1, 'Carrot');
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(runPosts(backend)).toHaveLength(1));
    expect(onPlanted).not.toHaveBeenCalled();
    // No client-side rollback (it needed the lead role): not one DELETE, and not one run-by-run request.
    expect(backend.seen.some((s) => s.body === 'DELETE' || s.url.startsWith('/planting-runs/run_'))).toBe(false);
    expect(backend.seen.some((s) => s.url === '/planting-runs')).toBe(false);
    expect(screen.getByTestId('planting-submit')).toBeEnabled();
  });

  it('tells the grower when two chosen species do not get along', async () => {
    usePlantingBackend({
      species: [TOMATO, CARROT],
      incompatible: { sp_carrot: [{ species_key: 'sp_tomato', reason: 'Competes for light.' }] },
    });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(screen.getByTestId('planting-add-entry'));
    await choose(user, 1, 'Carrot');

    expect(await screen.findByTestId('planting-mix-sp_carrot-sp_tomato')).toHaveTextContent(
      'Carrot (Carrot scientificus) and Tomato (Tomato scientificus) do not get along. Competes for light.',
    );
  });
});

describe('free positions (GP-FR-072)', () => {
  function mockCanvasRect() {
    return vi
      .spyOn(Element.prototype, 'getBoundingClientRect')
      .mockImplementation(() => ({ left: 0, top: 0, width: 400, height: 400, right: 400, bottom: 400, x: 0, y: 0, toJSON: () => ({}) }));
  }

  function tapCanvas(x: number, y: number) {
    const svg = screen.getByTestId('planting-canvas');
    act(() => {
      svg.dispatchEvent(new MouseEvent('pointerup', { clientX: x, clientY: y, bubbles: true }));
    });
  }

  it('sets points by tapping and rings the ones closer than the spacing, without blocking', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const rect = mockCanvasRect();
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: 'Layout' }));
    await user.click(await screen.findByRole('option', { name: 'Free positions' }));

    tapCanvas(200, 200); // -> (0.60, 1.00)
    tapCanvas(210, 200); // 0.036 m away: closer than the 0.60 m spacing
    tapCanvas(40, 40);

    expect(await screen.findByText('3 positions set · 2 too close')).toBeInTheDocument();
    expect(screen.getAllByTestId('planting-canvas-ring')).toHaveLength(2);

    await hintsDone();
    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalledWith(expect.objectContaining({ plantCount: 3 })));
    // The points travel with the run: the server stores and reserves them in the same transaction.
    expect(sentRuns(backend)[0].free_points).toEqual([
      [0.6, 1],
      [0.64, 1],
      [0.02, 1.9],
    ]);
    expect(sentRuns(backend)[0].entry).toMatchObject({ layout_strategy: 'free', quantity: 3 });
    expect(backend.seen.some((s) => s.url.endsWith('/slots/batch') || s.url.endsWith('/plan-slots'))).toBe(false);
    rect.mockRestore();
  });

  it('plants free positions without any spacing: the minimum spacing only draws the ring', async () => {
    const backend = usePlantingBackend({ species: [BARE] });
    const rect = mockCanvasRect();
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Rhubarb');
    await user.click(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: 'Layout' }));
    await user.click(await screen.findByRole('option', { name: 'Free positions' }));
    tapCanvas(200, 200);
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    await waitFor(() => expect(onPlanted).toHaveBeenCalled());
    expect(sentRuns(backend)[0].free_points).toHaveLength(1);
    rect.mockRestore();
  });

  it('does not take a position outside the bed - the server would refuse it (V-04)', async () => {
    usePlantingBackend({ species: [TOMATO] });
    const rect = mockCanvasRect();
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: 'Layout' }));
    await user.click(await screen.findByRole('option', { name: 'Free positions' }));

    tapCanvas(5, 5); // in the padding around the bed
    tapCanvas(200, 200);

    expect(await screen.findByText('1 position set')).toBeInTheDocument();
    rect.mockRestore();
  });

  it('sets a point at the bed centre by button and moves it with the arrows (keyboard route)', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    const { onPlanted } = renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: 'Layout' }));
    await user.click(await screen.findByRole('option', { name: 'Free positions' }));

    expect(screen.queryByTestId('planting-entry-0-nudge-up')).toBeNull();
    await user.click(screen.getByTestId('planting-entry-0-add-centre'));
    expect(await screen.findByText('1 position set')).toBeInTheDocument();
    await user.click(screen.getByTestId('planting-entry-0-nudge-right'));
    await user.click(screen.getByTestId('planting-entry-0-nudge-up'));
    expect(screen.getByText('1 position set')).toBeInTheDocument();

    await hintsDone();
    await user.click(screen.getByTestId('planting-submit'));
    await waitFor(() => expect(onPlanted).toHaveBeenCalledWith(expect.objectContaining({ plantCount: 1 })));
    expect(sentRuns(backend)[0].free_points?.[0]).toEqual([0.65, 1.05]); // centre (0.60, 1.00) + 5 cm right + 5 cm up
  });

  it('names the reason while the hints are still being checked', async () => {
    usePlantingBackend({ species: [TOMATO] });
    server.use(
      http.post(`${BASE}/locations/:key/validate-planting`, async () => {
        await delay(150);
        return HttpResponse.json(hint());
      }),
    );
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');

    expect(await screen.findByTestId('planting-submit-reason')).toHaveTextContent('still being checked');
    expect(screen.getByTestId('planting-submit')).toBeDisabled();
    await hintsDone();
    expect(screen.queryByTestId('planting-submit-reason')).toBeNull();
  });

  it('refuses to plan with no point set', async () => {
    const backend = usePlantingBackend({ species: [TOMATO] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await user.click(within(screen.getByTestId('planting-entry-0')).getByRole('combobox', { name: 'Layout' }));
    await user.click(await screen.findByRole('option', { name: 'Free positions' }));
    await hintsDone();

    await user.click(screen.getByTestId('planting-submit'));

    expect(await screen.findByText('Set at least one position on the bed.')).toBeInTheDocument();
    expect(runPosts(backend)).toHaveLength(0);
  });
});

describe('pot volume (W-016.5)', () => {
  it('warns when the pot is below the recommended volume', async () => {
    usePlantingBackend({ species: [species('sp_basil', 'Basil', { spacing_cm: '20', recommended_container_volume_l: '5-10' })] });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Basil');
    await user.click(screen.getByTestId('planting-entry-0-more'));

    const volume = await screen.findByTestId('planting-entry-0-container');
    await user.type(volume, '3');

    expect(await screen.findByTestId('planting-entry-0-container-warning')).toHaveTextContent('smaller than the recommended 5 l');
    await user.clear(volume);
    await user.type(volume, '8');
    expect(screen.queryByTestId('planting-entry-0-container-warning')).toBeNull();
  });
});

describe('accessibility', () => {
  it('has no violations with a species chosen and a hint shown', async () => {
    usePlantingBackend({ species: [TOMATO], hints: { sp_tomato: hint({ severity: 'WARNING', rotation: [{ severity: 'WARNING', code: 'rotation.pause_not_elapsed', message: 'm', family_key: 'Solanaceae', years_since: 2, pause_years: 4, pause_source: 'family' }] }) } });
    const user = userEvent.setup();
    renderDialog();
    await choose(user, 0, 'Tomato');
    await screen.findByTestId('planting-hint-sp_tomato');
    await screen.findByTestId('planting-entry-0-result');

    await expectNoA11yViolations(screen.getByTestId('planting-dialog'));
  });
});
