/**
 * The bed view (REQ-053 WP 3.5: GP-FR-041/047/120/121, GP-API-012/018): header, tabs in the URL,
 * the plan tab, the soil form, the status change and the read-only viewer.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedView from './BedView';
import { careTask, useCareBackend } from '../care/careTestKit';
import { careItem, timeline, useHistoryBackend, year } from '../history/historyTestKit';
import { bedSummary } from './bedTestKit';
import type { BedSummary } from './types';

const BASE = '/api/v1/t/:tenant';

function store(role: 'viewer' | 'grower' | 'lead' = 'lead') {
  return createTestStore({ ...tenantState(role), ...authState() });
}

function useBackend(extra: Parameters<typeof server.use> = []) {
  server.use(
    http.get('/api/v1/location-types', () =>
      HttpResponse.json([{ key: 'raised_bed', name: 'Hochbeet', name_en: 'Raised bed' }]),
    ),
    http.get('/api/v1/tenants/:slug/members', () =>
      HttpResponse.json([{ key: 'mem_1', user_key: 'user-1', display_name: 'Tester' }]),
    ),
    http.get('/api/v1/tenants/:slug/assignments', () =>
      HttpResponse.json([{ key: 'as_1', membership_key: 'mem_1', location_key: 'loc_b03', tenant_key: 't' }]),
    ),
    http.get(`${BASE}/sites/:key/plan`, () =>
      HttpResponse.json(
        planResponse({
          locations: [bed('loc_b03', 1, 1), bed('loc_other', 8, 8)],
          garden_objects: [],
          slots: [
            { key: 's1', slot_id: 'A1', location_key: 'loc_b03', plan_geometry: { origin: [1.3, 1.3] } },
            { key: 's2', slot_id: 'A2', location_key: 'loc_b03', plan_geometry: { origin: [1.6, 1.6] } },
            { key: 's3', slot_id: 'B1', location_key: 'loc_other', plan_geometry: { origin: [8.3, 8.3] } },
          ],
          plants: [{ key: 'pl_1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1' }],
        }),
      ),
    ),
    ...extra,
  );
}

function renderBed(summary: BedSummary, route: string, role: 'viewer' | 'grower' | 'lead' = 'lead', onReload = () => undefined) {
  return renderWithProviders(
    <BedView summary={summary} details={<div data-testid="details-stub">master data</div>} onReload={onReload} />,
    { store: store(role), route },
  );
}

afterEach(() => cleanup());

describe('BedView', () => {
  it('shows the bed head from the summary (GP-FR-047)', async () => {
    useBackend();
    renderBed(bedSummary(), '/standorte/locations/loc_b03#soil');
    const header = await screen.findByTestId('bed-header');
    expect(within(header).getByTestId('bed-header-area')).toHaveTextContent('2.4 m²');
    expect(within(header).getByTestId('bed-header-status')).toHaveTextContent('Active');
    expect(within(header).getByTestId('bed-header-soil')).toHaveTextContent('Loam');
    expect(within(header).getByTestId('bed-header-sun')).toHaveTextContent('Partial shade');
    expect(within(header).getByTestId('bed-header-plants')).toHaveTextContent('6 plants');
    expect(within(header).getByTestId('bed-header-plants')).toHaveTextContent('2 species');
    expect(within(header).getByTestId('bed-header-tasks')).toHaveTextContent('3 tasks');
    expect(within(header).getByTestId('bed-header-tasks')).toHaveTextContent('1 overdue');
    // The type name and the assignment arrive from their own requests.
    await waitFor(() => expect(within(header).getByTestId('bed-header-type')).toHaveTextContent('Raised bed'));
    await waitFor(() => expect(within(header).getByTestId('bed-header-assigned')).toHaveTextContent('Tester'));
    expect(within(header).getByTestId('bed-header-previous-year')).toHaveTextContent('Previous year (');
  });

  it('opens on the plan tab and draws the bed with its places and plants (GP-FR-041)', async () => {
    useBackend();
    const { container } = renderBed(bedSummary(), '/standorte/locations/loc_b03');
    expect(await screen.findByTestId('bed-plan-canvas')).toBeInTheDocument();
    // Only this bed's places are counted; the neighbouring bed is not part of the view.
    expect(screen.getByTestId('bed-plan-dimensions')).toHaveTextContent('2 places · 1 plants');
    expect(container.querySelector('[data-plan-key="loc_b03"]')).not.toBeNull();
    expect(container.querySelector('[data-plan-key="loc_other"]')).toBeNull();
    expect(screen.getByRole('tab', { name: 'Plan' })).toHaveAttribute('aria-selected', 'true');
  });

  it('says so when the bed is not on the garden plan yet', async () => {
    useBackend();
    renderBed(bedSummary({ geometry: null, bbox: null }), '/standorte/locations/loc_b03');
    expect(await screen.findByText('This bed is not on the garden plan yet')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-plan-canvas')).toBeNull();
  });

  it('keeps the tab in the URL hash: a deep link opens the planting placeholder, which points at the details', async () => {
    useBackend();
    const user = userEvent.setup();
    renderBed(bedSummary(), '/standorte/locations/loc_b03#planting');
    expect(await screen.findByTestId('bed-planting-tab')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Planting' })).toHaveAttribute('aria-selected', 'true');
    await user.click(screen.getByRole('button', { name: 'Go to details' }));
    expect(await screen.findByTestId('details-stub')).toBeInTheDocument();
  });

  it('opens the care tab with the open tasks of the bed (GP-FR-083) and the history tab with its timeline (GP-FR-102)', async () => {
    useBackend();
    useHistoryBackend({ items: [careItem('h1', { summary: 'Mulched' })], timeline: timeline([year(2026), year(2025), year(2024), year(2023), year(2022)]) });
    useCareBackend([careTask('t1', { name: 'Water the bed' })]);
    const user = userEvent.setup();
    renderBed(bedSummary(), '/standorte/locations/loc_b03#care');
    expect(await screen.findByTestId('care-task-t1')).toHaveTextContent('Water the bed');
    expect(screen.getByRole('tab', { name: 'Care' })).toHaveAttribute('aria-selected', 'true');
    await user.click(screen.getByRole('tab', { name: 'History' }));
    expect(await screen.findByTestId('bed-history-tab')).toHaveTextContent('What grew here');
    expect(await screen.findByTestId('history-item-care:h1')).toHaveTextContent('Mulched');
  });

  it('reloads the summary after a task was completed, so the head counters follow', async () => {
    useBackend();
    useCareBackend([careTask('t1', { name: 'Weed', category: 'weeding' })]);
    const user = userEvent.setup();
    let reloads = 0;
    renderBed(bedSummary(), '/standorte/locations/loc_b03#care', 'lead', () => {
      reloads += 1;
    });
    await user.click(await screen.findByTestId('care-done-t1'));
    await user.click(await screen.findByTestId('care-complete-submit'));
    await waitFor(() => expect(reloads).toBeGreaterThan(0));
  });

  it('hides the plan tab when the garden planner module is switched off', async () => {
    useBackend();
    const off = createTestStore({
      ...tenantState('lead'),
      ...authState(),
      userPreferences: {
        preferences: { module_visibility: { garden_planner: 'disabled' }, smart_home_enabled: false },
        loading: false,
        error: null,
      },
    });
    renderWithProviders(
      <BedView summary={bedSummary()} details={<div />} onReload={() => undefined} />,
      { store: off, route: '/standorte/locations/loc_b03' },
    );
    expect(await screen.findByTestId('bed-tabs')).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: 'Plan' })).toBeNull();
    // The first remaining tab is the default.
    expect(screen.getByRole('tab', { name: 'Planting' })).toHaveAttribute('aria-selected', 'true');
  });

  describe('soil tab (GP-FR-120/121)', () => {
    it('shows the stored profile and saves a changed one through PATCH', async () => {
      let body: unknown = null;
      useBackend([
        http.patch(`${BASE}/locations/:key`, async ({ request }) => {
          body = await request.json();
          return HttpResponse.json({ key: 'loc_b03', bed_status: 'active', plan_revision: 4 });
        }),
      ]);
      const user = userEvent.setup();
      let reloaded = 0;
      renderBed(bedSummary(), '/standorte/locations/loc_b03#soil', 'grower', () => {
        reloaded += 1;
      });
      const form = await screen.findByTestId('bed-soil-tab');
      expect(within(form).getByTestId('form-field-soil_texture')).toHaveTextContent('Loam');
      expect(within(form).getByTestId('form-submit-button')).toBeDisabled();

      await user.click(within(screen.getByTestId('form-field-drainage')).getByRole('combobox'));
      await user.click(await screen.findByTestId('form-option-drainage-poor'));
      expect(screen.getByTestId('form-submit-button')).toBeEnabled();
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(body).not.toBeNull());
      expect(body).toMatchObject({
        soil_profile: {
          soil_texture: 'loam',
          drainage: 'poor',
          site_water_regime: 'fresh',
          conditions: ['stony'],
          ph: 6.5,
          ph_method: 'cacl2',
        },
      });
      await waitFor(() => expect(reloaded).toBe(1));
    });

    it('explains the finger test', async () => {
      useBackend();
      const user = userEvent.setup();
      renderBed(bedSummary(), '/standorte/locations/loc_b03#soil');
      await user.click(await screen.findByRole('button', { name: /Finger test/ }));
      expect(await screen.findByText(/Very easy to shape, shiny/)).toBeVisible();
    });

    it('is read-only for a viewer', async () => {
      useBackend();
      renderBed(bedSummary(), '/standorte/locations/loc_b03#soil', 'viewer');
      const form = await screen.findByTestId('bed-soil-tab');
      expect(within(form).getByText(/view it but not change it/)).toBeInTheDocument();
      expect(within(form).queryByTestId('form-submit-button')).toBeNull();
      expect(within(form).getByRole('textbox', { name: /Notes/ })).toBeDisabled();
    });
  });

  describe('status change (GP-FR-046, GP-API-018)', () => {
    it('needs a reason to retire a bed and posts it', async () => {
      let body: unknown = null;
      useBackend([
        http.post(`${BASE}/locations/:key/status`, async ({ request }) => {
          body = await request.json();
          return HttpResponse.json({ key: 'loc_b03', bed_status: 'retired', plan_revision: 5 });
        }),
      ]);
      const user = userEvent.setup();
      let reloaded = 0;
      renderBed(bedSummary(), '/standorte/locations/loc_b03#soil', 'lead', () => {
        reloaded += 1;
      });
      await user.click(await screen.findByTestId('bed-status-change-button'));
      const dialog = await screen.findByTestId('bed-status-dialog');
      // An active bed can only be retired; that needs a reason.
      expect(within(dialog).getByTestId('bed-status-submit')).toBeDisabled();
      await user.type(within(dialog).getByRole('textbox', { name: /Reason/ }), 'Dismantled for the shed');
      await user.click(within(dialog).getByTestId('bed-status-submit'));
      await waitFor(() => expect(body).toEqual({ bed_status: 'retired', reason: 'Dismantled for the shed' }));
      await waitFor(() => expect(reloaded).toBe(1));
      await waitFor(() => expect(screen.queryByTestId('bed-status-dialog')).toBeNull());
    });

    it('offers a grower no status change for an active bed', async () => {
      useBackend();
      renderBed(bedSummary(), '/standorte/locations/loc_b03#soil', 'grower');
      await screen.findByTestId('bed-header');
      expect(screen.queryByTestId('bed-status-change-button')).toBeNull();
    });

    it('lets a grower bring a planned bed into use without a reason', async () => {
      let body: unknown = null;
      useBackend([
        http.post(`${BASE}/locations/:key/status`, async ({ request }) => {
          body = await request.json();
          return HttpResponse.json({ key: 'loc_b03', bed_status: 'active', plan_revision: 5 });
        }),
      ]);
      const user = userEvent.setup();
      renderBed(bedSummary({ bed_status: 'planned' }), '/standorte/locations/loc_b03#soil', 'grower');
      await user.click(await screen.findByTestId('bed-status-change-button'));
      const dialog = await screen.findByTestId('bed-status-dialog');
      await user.click(within(dialog).getByTestId('bed-status-submit'));
      await waitFor(() => expect(body).toEqual({ bed_status: 'active' }));
    });
  });

  it('reads the season from ?year=, falls back to this year for a bad value and keeps the tab', async () => {
    useBackend();
    const user = userEvent.setup();
    const current = new Date().getFullYear();
    renderBed(bedSummary(), `/standorte/locations/loc_b03?year=${current - 2}#soil`);
    const header = await screen.findByTestId('bed-header-season');
    expect(within(header).getByTestId('bed-header-previous-year')).toHaveTextContent(`(${current - 3})`);
    await user.click(within(header).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: String(current) }));
    await waitFor(() =>
      expect(screen.getByTestId('bed-header-previous-year')).toHaveTextContent(`(${current - 1})`),
    );
    expect(screen.getByRole('tab', { name: 'Soil' })).toHaveAttribute('aria-selected', 'true');
  });

  it('ignores a year outside the offered window', async () => {
    useBackend();
    renderBed(bedSummary(), '/standorte/locations/loc_b03?year=1900#soil');
    const current = new Date().getFullYear();
    expect(await screen.findByTestId('bed-header-previous-year')).toHaveTextContent(`(${current - 1})`);
  });

  it('has no critical accessibility violations on the plan and the soil tab (GP-NFR-028)', async () => {
    useBackend();
    const { container } = renderBed(bedSummary(), '/standorte/locations/loc_b03');
    await screen.findByTestId('bed-plan-canvas');
    await expectNoA11yViolations(container);
    const user = userEvent.setup();
    await user.click(screen.getByRole('tab', { name: 'Soil' }));
    await screen.findByTestId('bed-soil-tab');
    await expectNoA11yViolations(container);
  });
});
