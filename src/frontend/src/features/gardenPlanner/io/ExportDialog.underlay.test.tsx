/**
 * "Print the underlay" in the export dialog (REQ-053 GP-FR-033, #2895): offered only for a PDF of a plan that has an
 * underlay, off by default, and the only way `underlay=true` reaches `GET /print/garden-plan/{site}`.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { planResponse } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import { normalizePlan } from '../model/planModel';
import type { PlanUnderlay } from '../model/types';
import type { GardenPlanState } from '../state/gardenPlanSlice';
import ExportDialog from './ExportDialog';

const loaded = vi.hoisted(() => ({ state: null as unknown }));

vi.mock('../state/gardenPlanSlice', async (importOriginal) => {
  const original = await importOriginal<typeof import('../state/gardenPlanSlice')>();
  return { ...original, selectGardenPlanState: () => loaded.state as GardenPlanState };
});

const SITE = 'site_1';
const UNDERLAY: PlanUnderlay = {
  attachment_key: 'att_1',
  calibration: { p1_px: [0, 0], p2_px: [100, 0], distance_m: 5 },
  origin: [0, 10],
  rotation_deg: 0,
  opacity: 0.5,
};

function loadPlan(underlay: PlanUnderlay | null) {
  const response = planResponse();
  loaded.state = {
    plan: normalizePlan({ ...response, plan: response.plan ? { ...response.plan, underlay } : null }),
  } as unknown as GardenPlanState;
}

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

let pdfParams: URLSearchParams[];

beforeEach(() => {
  pdfParams = [];
  setPhone(false);
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
  server.use(
    http.get('/api/v1/t/:tenant/sites/:site/plan/render.svg', () =>
      new HttpResponse('<svg xmlns="http://www.w3.org/2000/svg"/>', {
        headers: { 'content-type': 'image/svg+xml', 'x-plan-scale': '1:50' },
      }),
    ),
    http.get('/api/v1/t/:tenant/print/garden-plan/:site', ({ request }) => {
      pdfParams.push(new URL(request.url).searchParams);
      return new HttpResponse('%PDF-1.7', { headers: { 'content-type': 'application/pdf' } });
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderDialog(onClose = vi.fn()) {
  const store = createTestStore({ ...tenantState('viewer'), ...authState() });
  renderWithProviders(<ExportDialog open siteKey={SITE} onClose={onClose} />, { store });
  return onClose;
}

describe('ExportDialog underlay', () => {
  it('offers the underlay for a PDF of a plan that has one, off by default, with its hint', async () => {
    loadPlan(UNDERLAY);
    const onClose = renderDialog();

    const toggle = screen.getByTestId('plan-export-underlay');
    expect(toggle).not.toBeChecked();
    expect(toggle).toHaveAccessibleDescription(/aerial view can reveal where you live/);
    expect(screen.getByText('Print the underlay')).toBeInTheDocument();
    await userEvent.setup().click(screen.getByTestId('plan-export-download'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(pdfParams[0].has('underlay')).toBe(false);
  });

  it('sends underlay=true with the PDF once it is switched on', async () => {
    loadPlan(UNDERLAY);
    const user = userEvent.setup();
    const onClose = renderDialog();

    await user.click(screen.getByTestId('plan-export-underlay'));
    await user.click(screen.getByTestId('plan-export-download'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(pdfParams[0].get('underlay')).toBe('true');
  });

  it('does not offer it for a plan without an underlay', () => {
    loadPlan(null);
    renderDialog();

    expect(screen.getByTestId('plan-export-bed-list')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-export-underlay')).not.toBeInTheDocument();
  });

  it('does not offer it for the SVG, which never carries the underlay', async () => {
    loadPlan(UNDERLAY);
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByTestId('plan-export-format-svg'));

    expect(screen.queryByTestId('plan-export-underlay')).not.toBeInTheDocument();
  });

  it('does not offer it on a phone, where the PDF keeps its standard options', () => {
    setPhone(true);
    loadPlan(UNDERLAY);
    renderDialog();

    expect(screen.queryByTestId('plan-export-underlay')).not.toBeInTheDocument();
  });
});
