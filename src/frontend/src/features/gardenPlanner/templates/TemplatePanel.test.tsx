/**
 * The template exchange in the template panel (REQ-053 GP-FR-173, WP 9.9): "Export" downloads the picked template
 * from GP-API-070; "Import" sends the chosen file to GP-API-071 as a dry run, shows the check report and writes only
 * on confirmation - then the panel reloads the catalogue and picks the new template. A taken name (409) proposes a
 * free one the user checks again with. The server is the authority on every answer.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import TemplatePanel from './TemplatePanel';
import type { BedTemplates } from './useBedTemplates';
import type { BedTemplateExchangeFile, BedTemplateImportReport } from './templateExchange';
import { MAX_TEMPLATE_FILE_BYTES } from './templateExchange';

const BASE = '/api/v1/t/:tenant';

const FILE: BedTemplateExchangeFile = {
  format: 'kamerplanter.bed_template',
  schema_version: '1',
  name: 'Herb bed',
  location_type_key: 'raised_bed',
  default_geometry: { kind: 'rect', origin: [0, 0], width_m: 1.5, length_m: 0.8, rotation_deg: 0 },
  height_m: 0.4,
  default_layout: { row_spacing_cm: 25, spacing_cm: 20 },
  soil_profile_defaults: null,
};

function report(overrides: Partial<BedTemplateImportReport> = {}): BedTemplateImportReport {
  return {
    dry_run: true,
    schema_version: '1',
    migrated: false,
    template: FILE,
    created_key: null,
    dropped_fields: ['created_by', 'tenant_key'],
    unknown_fields_ignored: 0,
    ...overrides,
  };
}

function refusal(status: number, details: Record<string, unknown>[]) {
  return HttpResponse.json(
    { error_id: 'e1', error_code: 'X', message: 'x', details, path: '', method: 'POST' },
    { status },
  );
}

interface ImportCall {
  params: URLSearchParams;
  contentType: string | null;
  body: string;
}

function catalogue(reload = vi.fn()): BedTemplates {
  return {
    templates: [
      {
        key: 'tpl_1',
        name: 'Herb bed',
        location_type_key: 'raised_bed',
        default_geometry: FILE.default_geometry,
        recurring_task_templates: [],
        is_system: false,
      },
    ],
    loading: false,
    failed: false,
    reload,
  };
}

function renderPanel(templateKey: string | null = 'tpl_1') {
  const reload = vi.fn();
  const onTemplateKey = vi.fn();
  const store = createTestStore({ ...tenantState('grower'), ...authState() });
  renderWithProviders(
    <TemplatePanel
      catalogue={catalogue(reload)}
      templateKey={templateKey}
      onTemplateKey={onTemplateKey}
      rotationDeg={0}
      onRotate={vi.fn()}
      busy={false}
      onPlaceCenter={vi.fn()}
      onClose={vi.fn()}
    />,
    { store },
  );
  return { reload, onTemplateKey };
}

function useImportBackend(calls: ImportCall[], answer: (params: URLSearchParams) => Response | BedTemplateImportReport) {
  server.use(
    http.post(`${BASE}/bed-templates/import`, async ({ request }) => {
      const params = new URL(request.url).searchParams;
      calls.push({ params, contentType: request.headers.get('content-type'), body: await request.text() });
      const out = answer(params);
      return out instanceof Response ? out : HttpResponse.json(out);
    }),
  );
}

function templateFile(content = JSON.stringify(FILE), name = 'bed-template-tpl_1.json') {
  return new File([content], name, { type: 'application/json' });
}

async function openImport(user: ReturnType<typeof userEvent.setup>, file = templateFile()) {
  await user.click(screen.getByTestId('garden-plan-template-import'));
  await user.upload(await screen.findByTestId('garden-plan-template-import-file'), file);
}

let calls: ImportCall[];
let click: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  calls = [];
  click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('TemplatePanel - export', () => {
  it('downloads the picked template under the name the server gives', async () => {
    const requested: string[] = [];
    server.use(
      http.get(`${BASE}/bed-templates/:key/export`, ({ params }) => {
        requested.push(String(params.key));
        return HttpResponse.json(FILE, {
          headers: { 'Content-Disposition': 'attachment; filename="bed-template-tpl_1.json"' },
        });
      }),
    );
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByTestId('garden-plan-template-export'));

    expect(await screen.findByTestId('garden-plan-template-exchange-notice')).toHaveTextContent(
      'The template was downloaded as a JSON file.',
    );
    expect(requested).toEqual(['tpl_1']);
    expect(click).toHaveBeenCalledTimes(1);
    const anchor = click.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe('bed-template-tpl_1.json');
  });

  it('sends nothing while no template is picked', async () => {
    const requested = vi.fn();
    server.use(http.get(`${BASE}/bed-templates/:key/export`, requested));
    const user = userEvent.setup();
    renderPanel(null);

    const button = screen.getByTestId('garden-plan-template-export');
    expect(button).toHaveAttribute('aria-disabled', 'true');
    await user.click(button);

    expect(requested).not.toHaveBeenCalled();
    expect(click).not.toHaveBeenCalled();
  });
});

describe('TemplatePanel - import', () => {
  it('checks the file first, shows the report, writes on confirmation and picks the new template', async () => {
    useImportBackend(calls, (params) =>
      params.get('dry_run') === 'true' ? report() : report({ dry_run: false, created_key: 'tpl_new' }),
    );
    const user = userEvent.setup();
    const { reload, onTemplateKey } = renderPanel();
    await openImport(user);

    const view = await screen.findByTestId('garden-plan-template-import-report');
    expect(within(view).getByText('Name: Herb bed')).toBeInTheDocument();
    expect(within(view).getByText('Shape: Rectangle 1.5 × 0.8 m')).toBeInTheDocument();
    expect(within(view).getByText('Height: 0.4 m')).toBeInTheDocument();
    expect(within(view).getByTestId('garden-plan-template-import-dropped')).toHaveTextContent(
      '2 fields of the file are ignored',
    );
    expect(calls).toHaveLength(1);
    expect(calls[0].params.get('dry_run')).toBe('true');
    expect(calls[0].params.has('name')).toBe(false);
    expect(calls[0].contentType).toContain('application/json');
    expect(JSON.parse(calls[0].body)).toEqual(FILE); // the file itself, unchanged

    await user.click(screen.getByTestId('garden-plan-template-import-confirm'));

    await waitFor(() => expect(onTemplateKey).toHaveBeenCalledWith('tpl_new'));
    expect(calls[1].params.get('dry_run')).toBe('false');
    expect(reload).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('garden-plan-template-exchange-notice')).toHaveTextContent(
      'The template was imported and is selected.',
    );
    expect(screen.queryByTestId('garden-plan-template-import-dialog')).not.toBeInTheDocument();
  });

  it('offers the free name of a 409 and checks again with it', async () => {
    useImportBackend(calls, (params) =>
      params.get('name') === null
        ? refusal(409, [{ field: 'name', code: 'bed_template.name_taken', suggested_name: 'Herb bed (2)' }])
        : params.get('dry_run') === 'true'
          ? report({ template: { ...FILE, name: params.get('name') ?? '' } })
          : report({ dry_run: false, created_key: 'tpl_2' }),
    );
    const user = userEvent.setup();
    const { onTemplateKey } = renderPanel();
    await openImport(user);

    expect(await screen.findByTestId('garden-plan-template-import-error')).toHaveTextContent(
      'A template of this name exists already.',
    );
    expect(screen.getByTestId('garden-plan-template-import-name')).toHaveValue('Herb bed (2)');
    expect(screen.getByTestId('garden-plan-template-import-confirm')).toBeDisabled();

    await user.click(screen.getByTestId('garden-plan-template-import-recheck'));
    expect(await screen.findByText('Name: Herb bed (2)')).toBeInTheDocument();
    expect(calls[1].params.get('name')).toBe('Herb bed (2)');

    await user.click(screen.getByTestId('garden-plan-template-import-confirm'));
    await waitFor(() => expect(onTemplateKey).toHaveBeenCalledWith('tpl_2'));
    expect(calls[2].params.get('name')).toBe('Herb bed (2)');
    expect(calls[2].params.get('dry_run')).toBe('false');
  });

  it('refuses a file above 256 KB without sending it', async () => {
    useImportBackend(calls, () => report());
    const user = userEvent.setup();
    renderPanel();
    await openImport(user, templateFile('x'.repeat(MAX_TEMPLATE_FILE_BYTES + 1)));

    expect(await screen.findByTestId('garden-plan-template-import-error')).toHaveTextContent(
      'The file is larger than 256 KB.',
    );
    expect(calls).toHaveLength(0);
  });

  it('translates the published code of a refused file', async () => {
    useImportBackend(calls, () =>
      refusal(422, [{ field: 'schema_version', code: 'bed_template.schema_version_unsupported' }]),
    );
    const user = userEvent.setup();
    renderPanel();
    await openImport(user);

    expect(await screen.findByTestId('garden-plan-template-import-error')).toHaveTextContent(
      'This version of the template file is no longer read.',
    );
    expect(screen.queryByTestId('garden-plan-template-import-report')).not.toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-template-import-confirm')).toBeDisabled();
  });
});
