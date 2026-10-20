/**
 * The import assistant (REQ-053 GP-UX-051): file, check report, mode. The server is the authority on every
 * answer; what is pinned here is what the person is shown and asked, and which requests that sends.
 */
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import ImportWizard from './ImportWizard';
import type { PlanImportReport, PlanSnapshot } from './types';

const BASE = '/api/v1/t/:tenant';
const counts = (locations = 0, garden_objects = 0, slots = 0, plan_settings = 0) => ({
  locations,
  garden_objects,
  slots,
  plan_settings,
  zones: 0,
});

function report(overrides: Partial<PlanImportReport> = {}): PlanImportReport {
  return {
    mode: 'replace',
    dry_run: true,
    target: 'same_site',
    offset_m: null,
    would_create: counts(5, 3, 20),
    would_update: counts(0, 0, 0, 1),
    would_delete: counts(4, 2, 12),
    kept_locations: 0,
    dropped_references: [],
    dropped_references_total: 0,
    errors: [],
    errors_total: 0,
    applied: false,
    plan_revision: null,
    snapshot_written: false,
    ...overrides,
  };
}

const FILE = JSON.stringify({ schema_version: '1', locations: [], slots: [], garden_objects: [] });

function backup(content = FILE, name = 'garden.json') {
  return new File([content], name, { type: 'application/json' });
}

interface Calls {
  bodies: Record<string, unknown>[];
}

function useBackend(calls: Calls, answer: (body: Record<string, unknown>) => Response | PlanImportReport) {
  server.use(
    http.post(`${BASE}/sites/s1/plan/import`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      calls.bodies.push(body);
      const out = answer(body);
      return out instanceof Response ? out : HttpResponse.json(out);
    }),
  );
}

function renderWizard(onImported = vi.fn(), onClose = vi.fn()) {
  const store = createTestStore({ ...tenantState('lead'), ...authState() });
  renderWithProviders(
    <ImportWizard open siteKey="s1" siteName="Mein Garten" onClose={onClose} onImported={onImported} />,
    { store },
  );
  return { onImported, onClose };
}

async function choose(user: ReturnType<typeof userEvent.setup>, file = backup()) {
  await user.upload(screen.getByTestId('plan-import-file'), file);
}

let calls: Calls;
beforeEach(() => {
  calls = { bodies: [] };
});
afterEach(() => cleanup());

describe('ImportWizard', () => {
  it('checks the chosen file with a dry run and shows the report before anything is written', async () => {
    useBackend(calls, () => report({ dropped_references_total: 1, dropped_references: [
      { entity: 'location', key: 'loc_7', field: 'irrigation_zone_key', reason: 'not_found' },
    ] }));
    const user = userEvent.setup();
    renderWizard();
    await choose(user);

    const view = await screen.findByTestId('plan-import-report');
    expect(within(view).getByText(/5 locations, 3 garden objects, 20 plant places/)).toBeInTheDocument();
    expect(within(view).getByTestId('plan-import-ok')).toBeInTheDocument();
    expect(within(view).getByTestId('plan-import-dropped')).toHaveTextContent('irrigation_zone_key');
    expect(calls.bodies).toHaveLength(1);
    expect(calls.bodies[0]).toMatchObject({ mode: 'replace', dry_run: true, force: false, confirm_site_name: null });
    expect((calls.bodies[0].document as { schema_version: string }).schema_version).toBe('1');
  });

  it('names a reference that left the file as "not in the file"', async () => {
    useBackend(calls, () =>
      report({
        dropped_references_total: 1,
        dropped_references: [{ entity: 'location', key: 'b5', field: 'parent_location_key', reason: 'outside_file' }],
      }),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);

    expect(await screen.findByTestId('plan-import-dropped')).toHaveTextContent('is not in the file');
  });

  it('refuses a file that is too large, not JSON, or not a backup, without asking the server', async () => {
    useBackend(calls, () => report());
    const user = userEvent.setup();
    renderWizard();

    await choose(user, backup('not json'));
    expect(await screen.findByTestId('plan-import-file-error')).toHaveTextContent('not valid JSON');
    await choose(user, backup('{"hello": 1}'));
    expect(await screen.findByTestId('plan-import-file-error')).toHaveTextContent('not a garden plan backup');
    const big = backup('x');
    Object.defineProperty(big, 'size', { value: 5 * 1024 * 1024 + 1 });
    await choose(user, big);
    expect(await screen.findByTestId('plan-import-file-error')).toHaveTextContent('larger than 5 MB');
    expect(calls.bodies).toHaveLength(0);
  });

  it('blocks the next step while the report lists problems', async () => {
    useBackend(calls, () =>
      report({ errors_total: 1, errors: [{ field: 'locations[1]', code: 'bed.overlap', key: 'loc_2' }] }),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);

    expect(await screen.findByTestId('plan-import-errors')).toHaveTextContent('Two beds overlap');
    expect(screen.getByTestId('plan-import-next')).toBeDisabled();
  });

  it('replace asks for the exact site name and names the snapshot, then writes with the name', async () => {
    useBackend(calls, (body) =>
      body.dry_run ? report() : report({ dry_run: false, applied: true, plan_revision: 7, snapshot_written: true }),
    );
    const user = userEvent.setup();
    const { onImported } = renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));

    expect(screen.getByTestId('plan-import-snapshot-notice')).toHaveTextContent('snapshot');
    const apply = screen.getByTestId('plan-import-apply');
    expect(apply).toBeDisabled();
    await user.type(screen.getByTestId('plan-import-confirm-name'), 'mein garten');
    expect(apply).toBeDisabled(); // the name must match exactly, case included
    await user.clear(screen.getByTestId('plan-import-confirm-name'));
    await user.type(screen.getByTestId('plan-import-confirm-name'), 'Mein Garten');
    expect(apply).toBeEnabled();
    await user.click(apply);

    expect(await screen.findByTestId('plan-import-done')).toHaveTextContent('5 locations, 3 garden objects and 20 plant places');
    expect(onImported).toHaveBeenCalledTimes(1);
    expect(calls.bodies).toHaveLength(2);
    expect(calls.bodies[1]).toMatchObject({ mode: 'replace', dry_run: false, confirm_site_name: 'Mein Garten' });
  });

  it('applies the replace with Enter in the name field once the name matches', async () => {
    useBackend(calls, (body) => (body.dry_run ? report() : report({ dry_run: false, applied: true, snapshot_written: true })));
    const user = userEvent.setup();
    renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));
    await user.type(screen.getByTestId('plan-import-confirm-name'), 'Mein{Enter}');
    expect(calls.bodies).toHaveLength(1); // wrong name: Enter does nothing
    await user.type(screen.getByTestId('plan-import-confirm-name'), ' Garten{Enter}');
    expect(await screen.findByTestId('plan-import-done')).toBeInTheDocument();
    expect(calls.bodies[1]).toMatchObject({ dry_run: false, confirm_site_name: 'Mein Garten' });
  });

  it('merge needs no name, but a changed mode has to be checked again before it can be applied', async () => {
    useBackend(calls, (body) =>
      body.dry_run ? report({ mode: body.mode as 'merge' }) : report({ mode: 'merge', dry_run: false, applied: true }),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));
    await user.click(screen.getByTestId('plan-import-mode-merge'));

    expect(screen.getByTestId('plan-import-recheck-hint')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-import-apply')).not.toBeInTheDocument();
    await user.click(screen.getByTestId('plan-import-check'));
    const apply = await screen.findByTestId('plan-import-apply');
    expect(screen.queryByTestId('plan-import-confirm-name')).not.toBeInTheDocument();
    await user.click(apply);

    await screen.findByTestId('plan-import-done');
    expect(calls.bodies.map((body) => [body.mode, body.dry_run, body.confirm_site_name])).toEqual([
      ['replace', true, null],
      ['merge', true, null],
      ['merge', false, null],
    ]);
  });

  it('offers to keep planted beds when the report says a bed holds active plants, and checks again with force', async () => {
    useBackend(calls, (body) =>
      body.force
        ? report({ kept_locations: 2 })
        : report({ errors_total: 1, errors: [{ field: 'mode', code: 'import.not_empty', key: null }] }),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));

    await user.click(screen.getByTestId('plan-import-force'));
    expect(screen.getByTestId('plan-import-recheck-hint')).toBeInTheDocument();
    await user.click(screen.getByTestId('plan-import-check'));
    await screen.findByTestId('plan-import-apply');
    expect(calls.bodies.map((body) => body.force)).toEqual([false, true]);
  });

  it('says what went wrong when the server refuses the write', async () => {
    useBackend(calls, (body) =>
      body.dry_run
        ? report()
        : HttpResponse.json(
            { error_id: 'e1', error_code: 'plan.revision_conflict', message: 'x', details: [], path: '', method: 'POST' },
            { status: 409 },
          ),
    );
    const user = userEvent.setup();
    const { onImported } = renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));
    await user.type(screen.getByTestId('plan-import-confirm-name'), 'Mein Garten');
    await user.click(screen.getByTestId('plan-import-apply'));

    expect(await screen.findByTestId('plan-import-failure')).toHaveTextContent('Someone changed the plan');
    expect(onImported).not.toHaveBeenCalled();
  });

  it('tells the person to wait when the import budget is used up', async () => {
    useBackend(calls, () =>
      HttpResponse.json(
        { error_id: 'e1', error_code: 'RATE_LIMITED', message: 'x', details: [], path: '', method: 'POST' },
        { status: 429 },
      ),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);

    await waitFor(() => expect(screen.getByTestId('plan-import-failure')).toHaveTextContent('Wait a minute'));
  });

  it('has no critical accessibility violations at the report and mode steps', async () => {
    useBackend(calls, () => report());
    const user = userEvent.setup();
    renderWizard();
    await expectNoA11yViolations(document.body, { minElements: 25 });
    await choose(user);
    await screen.findByTestId('plan-import-report');
    await expectNoA11yViolations(document.body, { minElements: 25 });
    await user.click(screen.getByTestId('plan-import-next'));
    await expectNoA11yViolations(document.body, { minElements: 25 });
  });

  it('sends the target and, for a merge, the offset - and checks again when either changes', async () => {
    useBackend(calls, (body) =>
      body.dry_run
        ? report({ mode: 'merge', target: body.target as 'other_site', offset_m: body.offset_m as [number, number] })
        : report({ mode: 'merge', dry_run: false, applied: true }),
    );
    const user = userEvent.setup();
    renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));
    await user.click(screen.getByTestId('plan-import-mode-merge'));
    expect(screen.getByTestId('plan-import-offset-x')).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByRole('combobox', { name: /Where is the file going/i }));
    await user.click(await screen.findByRole('option', { name: /another site/i }));
    await user.type(screen.getByTestId('plan-import-offset-x'), '2,5');
    await user.type(screen.getByTestId('plan-import-offset-y'), '-1');
    await user.click(screen.getByTestId('plan-import-check'));
    await user.click(await screen.findByTestId('plan-import-apply'));

    await screen.findByTestId('plan-import-done');
    const [, dry, applied] = calls.bodies;
    expect(dry).toMatchObject({ mode: 'merge', dry_run: true, target: 'other_site', offset_m: [2.5, -1] });
    expect(applied).toMatchObject({ mode: 'merge', dry_run: false, target: 'other_site', offset_m: [2.5, -1] });
    expect(calls.bodies[0]).toMatchObject({ mode: 'replace', target: 'same_site', offset_m: null });
  });

  it('sends no offset for a replace and refuses a value outside the plan frame', async () => {
    useBackend(calls, () => report({ mode: 'merge' }));
    const user = userEvent.setup();
    renderWizard();
    await choose(user);
    await user.click(await screen.findByTestId('plan-import-next'));
    await user.click(screen.getByTestId('plan-import-mode-merge'));

    await user.type(screen.getByTestId('plan-import-offset-x'), '5000');
    expect(screen.getByTestId('plan-import-offset-hint')).toHaveTextContent('between -1000 and 1000');
    expect(screen.getByTestId('plan-import-check')).toBeDisabled();
    await user.clear(screen.getByTestId('plan-import-offset-x'));
    await user.type(screen.getByTestId('plan-import-offset-x'), 'abc');
    expect(screen.getByTestId('plan-import-check')).toBeDisabled();
    await user.click(screen.getByTestId('plan-import-mode-replace'));
    expect(screen.queryByTestId('plan-import-offset-x')).not.toBeInTheDocument();
    expect(calls.bodies.every((body) => body.offset_m === null)).toBe(true);
  });
});

describe('ImportWizard - earlier states (WP 7.19)', () => {
  const snapshot = (overrides: Partial<PlanSnapshot> = {}): PlanSnapshot => ({
    audit_key: 'snap1',
    revision: 5,
    at: '2026-10-17T09:12:33Z',
    summary: 'state before the replace import (revision 5)',
    changed_by_name: 'Sabine',
    locations: 6,
    garden_objects: 3,
    slots: 20,
    zones: 1,
    ...overrides,
  });

  function useSnapshots(list: PlanSnapshot[] | Response, restore: (body: Record<string, unknown>) => Response | PlanImportReport) {
    server.use(
      http.get(`${BASE}/sites/s1/plan/snapshots`, () => (list instanceof Response ? list : HttpResponse.json(list))),
      http.post(`${BASE}/sites/s1/plan/snapshots/:auditKey/restore`, async ({ request, params }) => {
        const body = (await request.json()) as Record<string, unknown>;
        calls.bodies.push({ ...body, audit_key: params.auditKey });
        const out = restore(body);
        return out instanceof Response ? out : HttpResponse.json(out);
      }),
    );
  }

  it('lists the snapshots, checks one with a dry run and restores it with the site name', async () => {
    useSnapshots([snapshot(), snapshot({ audit_key: 'snap0', locations: 2 })], (body) =>
      body.dry_run ? report() : report({ dry_run: false, applied: true, snapshot_written: true }),
    );
    const user = userEvent.setup();
    const { onImported } = renderWizard();

    await user.click(screen.getByTestId('plan-import-snapshots'));
    expect(await screen.findByTestId('plan-snapshot-snap1')).toHaveTextContent('6 locations, 3 garden objects, 20 planting slots');
    const restore = screen.getByTestId('plan-snapshots-restore');
    expect(restore).toBeDisabled();
    await user.click(screen.getByTestId('plan-snapshot-snap1'));
    expect(await screen.findByTestId('plan-snapshots-notice')).toBeInTheDocument();
    expect(restore).toBeDisabled(); // the name is still missing
    await user.type(screen.getByTestId('plan-snapshots-confirm-name'), 'Mein Garten');
    expect(restore).toBeEnabled();
    await user.click(restore);

    expect(await screen.findByTestId('plan-import-done')).toBeInTheDocument();
    expect(onImported).toHaveBeenCalledTimes(1);
    expect(calls.bodies).toEqual([
      { dry_run: true, force: false, confirm_site_name: null, audit_key: 'snap1' },
      { dry_run: false, force: false, confirm_site_name: 'Mein Garten', audit_key: 'snap1' },
    ]);
  });

  it('says so when there is no earlier state, and goes back to the file step', async () => {
    useSnapshots([], () => report());
    const user = userEvent.setup();
    renderWizard();

    await user.click(screen.getByTestId('plan-import-snapshots'));
    expect(await screen.findByTestId('plan-snapshots-empty')).toBeInTheDocument();
    await user.click(screen.getByTestId('plan-snapshots-back'));
    expect(screen.getByTestId('plan-import-choose')).toBeInTheDocument();
  });

  it('names a refusal: a grower may not list, and planted beds need the force confirmation', async () => {
    useSnapshots(
      HttpResponse.json(
        { error_id: 'e1', error_code: 'import.forbidden', message: 'x', details: [], path: '', method: 'GET' },
        { status: 403 },
      ),
      () => report(),
    );
    const user = userEvent.setup();
    renderWizard();
    await user.click(screen.getByTestId('plan-import-snapshots'));
    expect(await screen.findByTestId('plan-snapshots-error')).toHaveTextContent('Only a lead');
    cleanup();

    calls.bodies.length = 0;
    useSnapshots([snapshot()], (body) =>
      body.force
        ? report()
        : report({ errors_total: 1, errors: [{ field: 'mode', code: 'import.not_empty', key: null }] }),
    );
    const again = userEvent.setup();
    renderWizard();
    await again.click(screen.getByTestId('plan-import-snapshots'));
    await again.click(await screen.findByTestId('plan-snapshot-snap1'));
    await again.click(await screen.findByTestId('plan-snapshots-force'));
    await waitFor(() => expect(calls.bodies.map((body) => body.force)).toEqual([false, true]));
  });

  it('has no critical accessibility violations in the list of earlier states', async () => {
    useSnapshots([snapshot()], () => report());
    const user = userEvent.setup();
    renderWizard();
    await user.click(screen.getByTestId('plan-import-snapshots'));
    await screen.findByTestId('plan-snapshot-snap1');
    await expectNoA11yViolations(document.body, { minElements: 15 });
  });
});
