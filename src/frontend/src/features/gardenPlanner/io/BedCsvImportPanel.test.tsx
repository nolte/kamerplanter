/**
 * The CSV bed list path of the import wizard (REQ-053 GP-FR-174, WP 8.27): the file goes to the server as it is,
 * the dry run's report names faulty lines by line and column, the confirmation sends the checked revision and
 * hands the new bed keys to the page. The server is the authority on every answer.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import ImportWizard from './ImportWizard';
import type { BedCsvImportReport } from './types';

const BASE = '/api/v1/t/:tenant';
const CSV = 'Name;Typ;Breite_m;Länge_m\r\nHochbeet 1;Hochbeet;2,0;1,2\r\nBeet 2;Hochbeet;x;1\r\n';

function report(overrides: Partial<BedCsvImportReport> = {}): BedCsvImportReport {
  return {
    dry_run: true,
    rows_total: 2,
    rows: [
      {
        line: 2,
        name: 'Hochbeet 1',
        location_type_key: 'raised_bed',
        width_m: 2,
        length_m: 1.2,
        origin: [0, 8.8],
        sun_exposure: 'full_sun',
        soil_texture: null,
        irrigation_zone_key: null,
        location_key: null,
      },
    ],
    rows_valid: 1,
    rows_skipped: 1,
    errors: [{ line: 3, column: 'Breite_m', code: 'csv.invalid_number' }],
    errors_total: 1,
    warnings: [],
    warnings_total: 0,
    ignored_columns: [],
    applied: false,
    plan_revision: 12,
    ...overrides,
  };
}

function applied(): BedCsvImportReport {
  const base = report();
  return {
    ...base,
    dry_run: false,
    applied: true,
    plan_revision: 13,
    rows: base.rows.map((row) => ({ ...row, location_key: 'loc_new' })),
  };
}

function failure(status: number, code: string, details: Record<string, unknown>[] = []) {
  return HttpResponse.json(
    { error_id: 'e1', error_code: code, message: 'x', details, path: '', method: 'POST' },
    { status },
  );
}

interface Call {
  params: URLSearchParams;
  contentType: string | null;
  body: string;
}

function useBackend(calls: Call[], answer: (params: URLSearchParams) => Response | BedCsvImportReport) {
  server.use(
    http.post(`${BASE}/sites/s1/beds/import-csv`, async ({ request }) => {
      const params = new URL(request.url).searchParams;
      calls.push({ params, contentType: request.headers.get('content-type'), body: await request.text() });
      const out = answer(params);
      return out instanceof Response ? out : HttpResponse.json(out);
    }),
  );
}

function renderCsv(onBedsImported = vi.fn(), onImported = vi.fn()) {
  const store = createTestStore({ ...tenantState('lead'), ...authState() });
  renderWithProviders(
    <ImportWizard
      open
      siteKey="s1"
      siteName="Mein Garten"
      initialView="csv"
      onClose={vi.fn()}
      onImported={onImported}
      onBedsImported={onBedsImported}
    />,
    { store },
  );
  return { onBedsImported, onImported };
}

function csvFile(content = CSV, name = 'beete.csv') {
  return new File([content], name, { type: 'text/csv' });
}

async function choose(user: ReturnType<typeof userEvent.setup>, file = csvFile()) {
  await user.upload(await screen.findByTestId('plan-csv-file'), file);
}

let calls: Call[];
beforeEach(() => {
  calls = [];
});
afterEach(() => cleanup());

describe('BedCsvImportPanel', () => {
  it('checks the file with a dry run, reports per line, and writes the valid lines on confirmation', async () => {
    useBackend(calls, (params) => (params.get('dry_run') === 'true' ? report() : applied()));
    const user = userEvent.setup();
    const { onBedsImported } = renderCsv();
    await choose(user);

    const view = await screen.findByTestId('plan-csv-report');
    expect(within(view).getByTestId('plan-csv-summary')).toHaveTextContent('1 of 2 lines are valid, 1 will be skipped.');
    expect(within(view).getByText('Hochbeet 1')).toBeInTheDocument();
    expect(calls).toHaveLength(1);
    expect(calls[0].params.get('dry_run')).toBe('true');
    expect(calls[0].params.has('expected_revision')).toBe(false);
    expect(calls[0].contentType).toContain('text/csv');
    expect(calls[0].body).toBe(CSV);

    await user.click(screen.getByTestId('plan-csv-apply'));
    expect(await screen.findByTestId('plan-csv-done')).toHaveTextContent('1 bed was created');
    expect(screen.getByTestId('plan-csv-done')).toHaveTextContent('1 faulty line was skipped.');
    expect(calls[1].params.get('dry_run')).toBe('false');
    expect(calls[1].params.get('expected_revision')).toBe('12');
    expect(onBedsImported).toHaveBeenCalledWith(['loc_new']);
    expect(screen.getByTestId('plan-csv-close')).toHaveTextContent('Go to the plan');
  });

  it('names each faulty line by line number, column and a translated message', async () => {
    useBackend(calls, () =>
      report({
        errors: [
          { line: 3, column: 'Breite_m', code: 'csv.invalid_number' },
          { line: 4, column: null, code: 'bed.overlap' },
        ],
        errors_total: 2,
        warnings: [{ line: 2, column: 'Name', code: 'csv.formula_stripped' }],
        warnings_total: 1,
        ignored_columns: ['Notiz'],
      }),
    );
    const user = userEvent.setup();
    renderCsv();
    await choose(user);

    const errors = await screen.findByTestId('plan-csv-errors');
    expect(within(errors).getByText('Line 3, column Breite_m: This is not a valid number (example: 2.5).')).toBeInTheDocument();
    expect(within(errors).getByText('Line 4: The bed would overlap another bed.')).toBeInTheDocument();
    expect(screen.getByTestId('plan-csv-warnings')).toHaveTextContent('Line 2, column Name');
    expect(screen.getByTestId('plan-csv-ignored')).toHaveTextContent('Notiz');
    // The lists are named for screen readers.
    expect(screen.getByRole('list', { name: '2 errors – these lines will be skipped' })).toBeInTheDocument();
  });

  it('offers nothing to apply when no line is valid', async () => {
    useBackend(calls, () => report({ rows: [], rows_valid: 0, rows_skipped: 2 }));
    const user = userEvent.setup();
    renderCsv();
    await choose(user);

    expect(await screen.findByTestId('plan-csv-nothing')).toBeInTheDocument();
    expect(screen.getByTestId('plan-csv-apply')).toBeDisabled();
  });

  it('shows the translated whole-file refusal, with the missing columns it names', async () => {
    useBackend(calls, () => failure(422, 'csv.missing_column', [{ field: 'file', code: 'csv.missing_column', columns: ['Breite_m', 'Länge_m'] }]));
    const user = userEvent.setup();
    renderCsv();
    await choose(user);

    expect(await screen.findByTestId('plan-csv-failure')).toHaveTextContent('The header row lacks: Breite_m, Länge_m.');
    expect(screen.queryByTestId('plan-csv-report')).not.toBeInTheDocument();
  });

  it('explains a wrong delimiter and the bed list limit', async () => {
    useBackend(calls, () => failure(422, 'csv.invalid_delimiter'));
    const user = userEvent.setup();
    renderCsv();
    await choose(user);
    expect(await screen.findByTestId('plan-csv-failure')).toHaveTextContent('semicolon (;)');

    useBackend(calls, () => failure(422, 'plan.quota_exceeded', [{ field: 'file', code: 'plan.quota_exceeded', limit: 500, current: 612 }]));
    await choose(user);
    await waitFor(() => expect(screen.getByTestId('plan-csv-failure')).toHaveTextContent('The limit of 500 would be exceeded (612)'));
  });

  it('asks for a new check when the plan changed since the dry run (409)', async () => {
    useBackend(calls, (params) =>
      params.get('dry_run') === 'true' ? report() : failure(409, 'plan.revision_conflict'),
    );
    const user = userEvent.setup();
    const { onBedsImported } = renderCsv();
    await choose(user);
    await user.click(await screen.findByTestId('plan-csv-apply'));

    expect(await screen.findByTestId('plan-csv-failure')).toHaveTextContent('Someone changed the plan since you checked the file');
    expect(screen.getByTestId('plan-csv-apply')).toBeDisabled();
    expect(onBedsImported).not.toHaveBeenCalled();

    await user.click(screen.getByTestId('plan-csv-recheck'));
    await waitFor(() => expect(screen.getByTestId('plan-csv-apply')).toBeEnabled());
    expect(calls.filter((call) => call.params.get('dry_run') === 'true')).toHaveLength(2);
  });

  it('refuses a file over 1 MB, an empty file and a non-CSV file without asking the server', async () => {
    useBackend(calls, () => report());
    const user = userEvent.setup({ applyAccept: false });
    renderCsv();

    const big = csvFile('x');
    Object.defineProperty(big, 'size', { value: 1024 * 1024 + 1 });
    await choose(user, big);
    expect(await screen.findByTestId('plan-csv-file-error')).toHaveTextContent('larger than 1 MB');

    await choose(user, csvFile(''));
    expect(await screen.findByTestId('plan-csv-file-error')).toHaveTextContent('The file is empty.');

    await choose(user, new File(['{}'], 'plan.json', { type: 'application/json' }));
    expect(await screen.findByTestId('plan-csv-file-error')).toHaveTextContent('not a CSV file');
    expect(calls).toHaveLength(0);
  });

  it('maps a server 413 to the size message', async () => {
    useBackend(calls, () => failure(413, 'REQUEST_BODY_TOO_LARGE'));
    const user = userEvent.setup();
    renderCsv();
    await choose(user);
    expect(await screen.findByTestId('plan-csv-failure')).toHaveTextContent('larger than 1 MB');
  });

  it('is reachable from the backup import and leads back to it', async () => {
    const user = userEvent.setup();
    const store = createTestStore({ ...tenantState('lead'), ...authState() });
    renderWithProviders(
      <ImportWizard open siteKey="s1" siteName="Mein Garten" onClose={vi.fn()} onImported={vi.fn()} />,
      { store },
    );
    await user.click(screen.getByTestId('plan-import-csv'));
    expect(await screen.findByTestId('plan-csv-import')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Import a bed list (CSV)' })).toBeInTheDocument();
    await user.click(screen.getByTestId('plan-csv-back'));
    expect(await screen.findByTestId('plan-import-choose')).toBeInTheDocument();
  });

  it('has no accessibility violations on the file step and the report', async () => {
    useBackend(calls, () =>
      report({ warnings: [{ line: 2, column: 'Name', code: 'csv.formula_stripped' }], warnings_total: 1 }),
    );
    const user = userEvent.setup();
    renderCsv();
    await screen.findByTestId('plan-csv-choose');
    await expectNoA11yViolations(document.body, { minElements: 15 });
    await choose(user);
    await screen.findByTestId('plan-csv-report');
    await expectNoA11yViolations(document.body, { minElements: 25 });
  });
});
