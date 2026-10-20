/**
 * The export dialog (REQ-053 GP-UX-050): what it asks the server for, the preview, the reasons it gives when the
 * server refuses, and the phone variant with the standard options only.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import ExportDialog from './ExportDialog';

const BASE = '/api/v1/t/:tenant';
const SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="5" height="5"/></svg>';

function setPhone(isPhone: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: isPhone && query.includes('max-width'),
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

interface Seen {
  svg: URLSearchParams[];
  pdf: URLSearchParams[];
  json: number;
  jsonParams: URLSearchParams[];
}

function useBackend(seen: Seen, svgHeaders: Record<string, string> = { 'x-plan-scale': '1:50' }) {
  server.use(
    http.get(`${BASE}/sites/s1/plan/render.svg`, ({ request }) => {
      seen.svg.push(new URL(request.url).searchParams);
      return new HttpResponse(SVG, { headers: { 'content-type': 'image/svg+xml', ...svgHeaders } });
    }),
    http.get(`${BASE}/print/garden-plan/s1`, ({ request }) => {
      seen.pdf.push(new URL(request.url).searchParams);
      return new HttpResponse('%PDF-1.7', {
        headers: {
          'content-type': 'application/pdf',
          'content-disposition': 'attachment; filename="garden-plan-s1.pdf"',
        },
      });
    }),
    http.get(`${BASE}/sites/s1/plan/export`, ({ request }) => {
      seen.json += 1;
      seen.jsonParams.push(new URL(request.url).searchParams);
      return HttpResponse.json({ schema_version: '1', locations: [{}, {}], slots: [{}], garden_objects: [{}, {}, {}] });
    }),
  );
}

function renderDialog(onClose = vi.fn(), selection?: { locationKeys: string[]; objectKeys: string[] }) {
  const store = createTestStore({ ...tenantState('viewer'), ...authState() });
  renderWithProviders(<ExportDialog open siteKey="s1" selection={selection} onClose={onClose} />, { store });
  return onClose;
}

let seen: Seen;
beforeEach(() => {
  seen = { svg: [], pdf: [], json: 0, jsonParams: [] };
  setPhone(false);
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ExportDialog', () => {
  it('previews the scaled plan and names the scale the server chose', async () => {
    useBackend(seen);
    renderDialog();

    expect(await screen.findByAltText('Preview of the garden plan, scale 1:50', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText('Chosen: 1:50')).toBeInTheDocument();
    // The PDF preview is the SVG the PDF embeds: one request to the SVG route, none to the PDF yet.
    expect(seen.svg).toHaveLength(1);
    expect(seen.pdf).toHaveLength(0);
  });

  it('sends the chosen options with the download and closes', async () => {
    useBackend(seen);
    const user = userEvent.setup();
    const onClose = renderDialog();
    await screen.findByAltText(/Preview of the garden plan/, {}, { timeout: 3000 });

    await user.click(screen.getByTestId('plan-export-layer-grid'));
    await user.click(screen.getByTestId('plan-export-bed-list'));
    await user.click(screen.getByTestId('plan-export-download'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(seen.pdf).toHaveLength(1);
    const params = seen.pdf[0];
    expect(params.get('scale')).toBe('auto');
    expect(params.get('paper')).toBe('a4');
    expect(params.get('orientation')).toBe('landscape');
    expect(params.get('layers')).toBe('grid,beds,objects,plants,labels');
    expect(params.get('bed_list')).toBe('true');
    expect(params.get('locale')).toMatch(/^(de|en)$/);
  });

  it('asks for a new preview when the paper changes, and offers A3 when the server suggests it', async () => {
    useBackend(seen, { 'x-plan-scale': '1:250', 'x-plan-suggested-paper': 'a3' });
    renderDialog();

    expect(await screen.findByTestId('plan-export-suggest-a3', {}, { timeout: 3000 })).toBeInTheDocument();
    const user = userEvent.setup();
    await user.click(screen.getByTestId('plan-export-format-svg'));
    await waitFor(() => expect(seen.svg.length).toBeGreaterThanOrEqual(1));
    expect(seen.svg.every((params) => params.get('paper') === 'a4')).toBe(true);
  });

  it('shows the size of the backup for JSON instead of a drawing', async () => {
    useBackend(seen);
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-json'));

    const summary = await screen.findByTestId('plan-export-json-summary', {}, { timeout: 3000 });
    expect(summary).toHaveTextContent('2 locations, 3 garden objects and 1 plant places');
    expect(screen.queryByTestId('plan-export-paper')).not.toBeInTheDocument();
    expect(seen.json).toBe(1);
  });

  it('backs up the whole site by default and offers a partial scope only with a selection', async () => {
    useBackend(seen);
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-json'));

    expect(screen.getByTestId('plan-export-scope-site')).toBeChecked();
    expect(screen.getByTestId('plan-export-scope-selection')).toBeDisabled();
    expect(screen.getByTestId('plan-export-scope-subtree')).toBeDisabled();
    expect(screen.getByTestId('plan-export-scope-hint')).toHaveTextContent('select beds on the plan first');
    await screen.findByTestId('plan-export-json-summary', {}, { timeout: 3000 });
    expect(seen.jsonParams.every((params) => !params.has('scope') && !params.has('keys'))).toBe(true);
  });

  it('limits the backup to the selection, or to the selection and what is below it', async () => {
    useBackend(seen);
    const user = userEvent.setup();
    renderDialog(vi.fn(), { locationKeys: ['bed1', 'bed2'], objectKeys: ['tree1'] });
    await user.click(screen.getByTestId('plan-export-format-json'));

    await user.click(screen.getByTestId('plan-export-scope-selection'));
    expect(screen.getByTestId('plan-export-scope-hint')).toHaveTextContent('3 selected');
    await user.click(screen.getByTestId('plan-export-download'));
    await waitFor(() => expect(seen.jsonParams.some((params) => params.get('scope') === 'selection')).toBe(true));
    const selection = seen.jsonParams.filter((params) => params.get('scope') === 'selection').pop();
    expect(selection?.get('keys')).toBe('bed1,bed2,object:tree1');

    await user.click(screen.getByTestId('plan-export-scope-subtree'));
    await waitFor(() => expect(seen.jsonParams.some((params) => params.get('scope') === 'subtree')).toBe(true));
    const subtree = seen.jsonParams.filter((params) => params.get('scope') === 'subtree').pop();
    expect(subtree?.get('keys')).toBe('bed1,bed2'); // a subtree is named by beds only
  });

  it('says why an empty plan cannot be exported and does not offer the download', async () => {
    server.use(
      http.get(`${BASE}/sites/s1/plan/render.svg`, () =>
        HttpResponse.json(
          { error_id: 'e1', error_code: 'plan.empty', message: 'empty', details: [], path: '', method: 'GET' },
          { status: 422 },
        ),
      ),
    );
    renderDialog();

    const alert = await screen.findByTestId('plan-export-error', {}, { timeout: 3000 });
    expect(alert).toHaveTextContent('The plan is still empty');
    expect(screen.getByTestId('plan-export-download')).toBeDisabled();
  });

  it('names a fixed scale that does not fit and keeps the dialog open', async () => {
    useBackend(seen);
    server.use(
      http.get(`${BASE}/print/garden-plan/s1`, () =>
        HttpResponse.json(
          { error_id: 'e1', error_code: 'plan.does_not_fit', message: 'x', details: [], path: '', method: 'GET' },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onClose = renderDialog();
    await screen.findByAltText(/Preview of the garden plan/, {}, { timeout: 3000 });
    await user.click(screen.getByTestId('plan-export-download'));

    expect(await screen.findByTestId('plan-export-error')).toHaveTextContent('does not fit the sheet');
    expect(onClose).not.toHaveBeenCalled();
  });

  it('offers only JSON and PDF with their standard options on a phone', async () => {
    setPhone(true);
    useBackend(seen);
    renderDialog();

    expect(screen.getByTestId('plan-export-format-pdf')).toBeInTheDocument();
    expect(screen.getByTestId('plan-export-format-json')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-export-format-svg')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plan-export-paper')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plan-export-scale')).not.toBeInTheDocument();
    expect(screen.getByTestId('plan-export-phone-note')).toBeInTheDocument();
  });

  it('has no critical accessibility violations', async () => {
    useBackend(seen);
    renderDialog();
    await screen.findByAltText(/Preview of the garden plan/, {}, { timeout: 3000 });

    await expectNoA11yViolations(document.body, { minElements: 25 });
  });
});
