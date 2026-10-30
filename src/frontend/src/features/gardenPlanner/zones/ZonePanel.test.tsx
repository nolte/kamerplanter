/**
 * The zone panel (REQ-053 WP 7.6 / 7.7): list, create, assign beds, delete for the lead only, the status with
 * its hint codes, technical fields for the technical scope only, and the watering round.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { useMemo } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import ZonePanel from './ZonePanel';
import { useIrrigationZones } from './useZoneData';
import { BASE, status, mockStatus, mockZoneList, zone, zoneData, zonePlan } from './zonesTestKit';
import type { IrrigationZone } from './zoneTypes';

afterEach(() => cleanup());

function renderPanel(
  zones: IrrigationZone[],
  role: 'viewer' | 'grower' | 'lead' = 'grower',
  scopes: readonly string[] = [],
  extra: { selectedBedKeys?: string[]; onChanged?: () => void; unsavedBed?: boolean } = {},
) {
  const data = zoneData(zones);
  const onChanged = extra.onChanged ?? vi.fn();
  const view = renderWithProviders(
    <ZonePanel
      plan={zonePlan(extra.unsavedBed ? [{ name: 'Unsaved bed' }] : [])}
      zoneData={data}
      selectedBedKeys={extra.selectedBedKeys ?? []}
      onChanged={onChanged}
      onClose={() => undefined}
    />,
    { store: createTestStore({ ...tenantState(role, scopes), ...authState() }) },
  );
  return { ...view, data, onChanged };
}

describe('zone list', () => {
  it('lists the zones with their bed count and says so when there are none', async () => {
    renderPanel([zone('z1', { name: 'South line', location_keys: ['loc_a', 'loc_c'] })]);
    expect(screen.getByTestId('garden-plan-zone-row-z1')).toHaveTextContent('South line');
    expect(screen.getByTestId('garden-plan-zone-row-z1')).toHaveTextContent('2 beds');
    cleanup();
    renderPanel([]);
    expect(screen.getByTestId('garden-plan-zone-empty')).toBeInTheDocument();
  });

  it('offers a viewer no way to create or change', () => {
    renderPanel([zone('z1')], 'viewer');
    expect(screen.getByTestId('garden-plan-zone-readonly')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-zone-new')).toBeNull();
  });

  it('has no axe violations', async () => {
    const { container } = renderPanel([zone('z1', { location_keys: ['loc_a'] })]);
    await expectNoA11yViolations(container);
  });
});

describe('create and assign beds', () => {
  it('creates a zone, then replaces its beds with the checked ones', async () => {
    const user = userEvent.setup();
    const created: unknown[] = [];
    const assigned: unknown[] = [];
    server.use(
      http.post(`${BASE}/sites/site_1/irrigation-zones`, async ({ request }) => {
        created.push(await request.json());
        return HttpResponse.json(zone('z_new', { name: 'Drip line' }), { status: 201 });
      }),
      http.put(`${BASE}/irrigation-zones/z_new/locations`, async ({ request }) => {
        assigned.push(await request.json());
        return HttpResponse.json({ ...zone('z_new'), added: ['loc_a'], removed: [], moved_from: {} });
      }),
    );
    const { onChanged, data } = renderPanel([], 'grower', [], { selectedBedKeys: ['loc_a'] });
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Drip line');
    await user.click(screen.getByTestId('garden-plan-zone-take-selection'));
    expect(screen.getByTestId('garden-plan-zone-bed-loc_a')).toBeChecked();
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await waitFor(() => expect(assigned).toHaveLength(1));
    expect(created[0]).toMatchObject({ name: 'Drip line', irrigation_type: 'manual' });
    expect(created[0]).not.toHaveProperty('flow_rate_l_per_min');
    expect(assigned[0]).toEqual({ location_keys: ['loc_a'] });
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    expect(data.reload).toHaveBeenCalled();
  });

  it('names the zone a bed would be taken from', async () => {
    const user = userEvent.setup();
    renderPanel([zone('z1', { name: 'Old zone', location_keys: ['loc_a'] }), zone('z2', { name: 'Other' })]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z2'));
    expect(screen.getByLabelText(/North bed \(belongs to Old zone\)/)).toBeInTheDocument();
  });

  it('shows a refusal as text, not as a silent failure', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`${BASE}/sites/site_1/irrigation-zones`, () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'irrigation_zone.quota_exceeded', message: 'x', details: [], path: '', method: 'POST' },
          { status: 422 },
        ),
      ),
    );
    renderPanel([]);
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Z');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    expect(await screen.findByTestId('garden-plan-zone-error')).toHaveTextContent(/maximum number of zones/);
  });
});

describe('delete', () => {
  it('is offered to the lead only', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    renderPanel([zone('z1')], 'grower');
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    expect(screen.queryByTestId('garden-plan-zone-delete')).toBeNull();
    cleanup();
    mockStatus('z1', status());
    renderPanel([zone('z1')], 'lead');
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    expect(screen.getByTestId('garden-plan-zone-delete')).toBeInTheDocument();
  });

  it('asks before it deletes', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    const deleted = vi.fn();
    server.use(
      http.delete(`${BASE}/irrigation-zones/z1`, () => {
        deleted();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderPanel([zone('z1', { name: 'South line' })], 'lead');
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(screen.getByTestId('garden-plan-zone-delete'));
    expect(deleted).not.toHaveBeenCalled();
    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(deleted).toHaveBeenCalled());
  });
});

describe('status', () => {
  it('words the last watering as days since, marks an allocated value, and hides an absent demand', async () => {
    const user = userEvent.setup();
    const yesterday = new Date(Date.now() - 86_400_000).toISOString();
    mockStatus(
      'z1',
      status({
        last_watering: { at: yesterday, source: 'care_event', location_key: 'loc_a', allocation: 'by_area' },
        next_planned: null,
        demand_liters_today: null,
        consumption_liters_30d: 120,
      }),
    );
    renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    const last = await screen.findByTestId('garden-plan-zone-last-watering');
    expect(last).toHaveTextContent(/1 day since/);
    expect(last).toHaveTextContent('North bed');
    expect(screen.getByTestId('garden-plan-zone-allocation-marker')).toHaveTextContent('Divided by area');
    expect(screen.queryByTestId('garden-plan-zone-demand')).toBeNull();
    expect(screen.getByTestId('garden-plan-zone-next-planned')).toHaveTextContent('No watering planned');
    expect(screen.getByTestId('garden-plan-zone-status').textContent ?? '').not.toMatch(/needs? water/i);
  });

  it('shows the demand, the gross value and the efficiency when the backend sourced them', async () => {
    const user = userEvent.setup();
    mockStatus(
      'z1',
      status({
        demand_liters_today: 84,
        demand_gross_liters_today: 95.5,
        application_efficiency: 0.88,
        efficiency_source: 'type_default',
      }),
    );
    renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    const demand = await screen.findByTestId('garden-plan-zone-demand');
    expect(demand).toHaveTextContent('84 litres net');
    expect(demand).toHaveTextContent('95.5 litres gross');
    expect(demand).toHaveTextContent('Efficiency 88 %');
    expect(demand).toHaveTextContent('default of the irrigation type');
  });

  it('translates the hint codes the backend returns, and names one it does not know', async () => {
    const user = userEvent.setup();
    mockStatus(
      'z1',
      status({
        hints: [
          { code: 'water_source_lasts_days', params: { days: 2, capacity_liters: 200, daily_liters: 95.45 } },
          { code: 'irrigation_system_differs', params: { zone_type: 'drip', location_keys: ['loc_a', 'loc_c'] } },
          { code: 'brand_new_code', params: {} },
        ],
      }),
    );
    renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    const hints = await screen.findByTestId('garden-plan-zone-hints');
    expect(hints).toHaveTextContent('lasts about 2 days (200 litres capacity, 95.5 litres a day)');
    expect(hints).toHaveTextContent('set up as Drip irrigation');
    expect(hints).toHaveTextContent('North bed, East bed');
    expect(hints).toHaveTextContent('Hint brand_new_code');
  });

  it('shows the technical fields to the technical scope only, and never the entity id', async () => {
    const user = userEvent.setup();
    const answer = status({ consumption_sources: [{ source: 'actuator_runtime_ha_rate', liters: 30 }] });
    const record = zone('z1', { flow_rate_l_per_min: 4, flow_rate_source: 'ha_entity', flow_rate_ha_entity_bound: true });
    mockStatus('z1', answer);
    renderPanel([record], 'grower');
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await screen.findByTestId('garden-plan-zone-consumption');
    expect(screen.queryByTestId('garden-plan-zone-technical')).toBeNull();
    expect(screen.queryByTestId('garden-plan-zone-flow-rate-input')).toBeNull();
    cleanup();
    mockStatus('z1', answer);
    renderPanel([record], 'grower', ['technical']);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    const technical = await screen.findByTestId('garden-plan-zone-technical');
    expect(within(technical).getByTestId('garden-plan-zone-flow-rate')).toHaveTextContent('Home Assistant entity linked');
    expect(technical.textContent ?? '').not.toMatch(/sensor\./);
    expect(screen.getByTestId('garden-plan-zone-flow-rate-input')).toBeInTheDocument();
  });
});

describe('watering round', () => {
  it('divides by area, marks the amount as allocated, lists beds without an area and the skipped ones', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    const sent: unknown[] = [];
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/log-watering`, async ({ request }) => {
        sent.push(await request.json());
        return HttpResponse.json(
          {
            event_keys: ['e1'],
            shares: [{ location_key: 'loc_a', liters: 40 }],
            allocation: 'by_area',
            performed_at: '2026-10-20T06:00:00Z',
            skipped_location_keys: ['loc_b'],
          },
          { status: 201 },
        );
      }),
    );
    renderPanel([zone('z1', { name: 'South line', location_keys: ['loc_a', 'loc_b'] })]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(await screen.findByTestId('garden-plan-zone-round-open'));
    const dialog = await screen.findByTestId('garden-plan-round-dialog');
    expect(within(dialog).getByTestId('garden-plan-round-marker')).toHaveTextContent('not measured');
    expect(within(dialog).getByTestId('garden-plan-round-no-area')).toHaveTextContent('South bed');
    // Only the two decided allocations are offered; `by_demand` is not.
    expect(within(dialog).getAllByRole('radio')).toHaveLength(2);
    expect(within(dialog).getByTestId('garden-plan-round-submit')).toBeDisabled();
    await user.type(within(dialog).getByTestId('garden-plan-round-volume'), '40');
    await user.click(within(dialog).getByTestId('garden-plan-round-submit'));
    const result = await screen.findByTestId('garden-plan-round-result');
    expect(sent[0]).toEqual({ volume_liters: 40, allocation: 'by_area', summary: null });
    expect(result).toHaveTextContent('divided, not measured');
    expect(result).toHaveTextContent('North bed: 40 litres');
    expect(screen.getByTestId('garden-plan-round-result-skipped')).toHaveTextContent('South bed');
  });

  it('sends equal parts when chosen and refuses a zone without beds', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    mockStatus('z2', status());
    const sent: unknown[] = [];
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/log-watering`, async ({ request }) => {
        sent.push(await request.json());
        return HttpResponse.json(
          { event_keys: [], shares: [], allocation: 'equal', performed_at: '2026-10-20T06:00:00Z', skipped_location_keys: [] },
          { status: 201 },
        );
      }),
    );
    renderPanel([zone('z1', { location_keys: ['loc_a'] }), zone('z2')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z2'));
    await user.click(await screen.findByTestId('garden-plan-zone-round-open'));
    expect(screen.getByTestId('garden-plan-round-submit')).toBeDisabled();
    await user.click(screen.getByTestId('garden-plan-round-cancel'));
    await user.click(screen.getByTestId('garden-plan-zone-cancel'));
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(await screen.findByTestId('garden-plan-zone-round-open'));
    await user.click(screen.getByTestId('garden-plan-round-allocation-equal'));
    await user.type(screen.getByTestId('garden-plan-round-volume'), '10,5');
    await user.click(screen.getByTestId('garden-plan-round-submit'));
    await screen.findByTestId('garden-plan-round-result');
    expect(sent[0]).toEqual({ volume_liters: 10.5, allocation: 'equal', summary: null });
  });
});

const errorBody = (code: string, status: number) =>
  HttpResponse.json({ error_id: 'e', error_code: code, message: 'x', details: [], path: '', method: 'X' }, { status });

describe('partial failure and unsaved beds', () => {
  it('does not take an unsaved bed from the plan selection and says why', async () => {
    const user = userEvent.setup();
    renderPanel([], 'grower', [], { selectedBedKeys: ['tmpunsaved0'], unsavedBed: true });
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    expect(screen.queryByTestId('garden-plan-zone-bed-tmpunsaved0')).toBeNull();
    expect(screen.getByTestId('garden-plan-zone-unsaved-hint')).toBeInTheDocument();
    await user.click(screen.getByTestId('garden-plan-zone-take-selection'));
    expect(screen.getByText(/selected bed is not saved yet/)).toBeInTheDocument();
  });

  it('shows the moved notice and leaves the form of a zone that is gone', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    server.use(
      http.put(`${BASE}/irrigation-zones/z1/locations`, () =>
        HttpResponse.json({ ...zone('z1'), added: ['loc_a'], removed: [], moved_from: { loc_a: 'z0' } }),
      ),
    );
    renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(screen.getByTestId('garden-plan-zone-bed-loc_a'));
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    expect(await screen.findByText(/Taken over from another zone: North bed/)).toBeInTheDocument();
    cleanup();
    mockStatus('z1', status());
    server.use(http.patch(`${BASE}/irrigation-zones/z1`, () => errorBody('x', 404)));
    renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.clear(screen.getByTestId('garden-plan-zone-name'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'New name');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await waitFor(() => expect(screen.queryByTestId('garden-plan-zone-form')).toBeNull());
  });

  it('maps 403 on save to the permission text', async () => {
    const user = userEvent.setup();
    server.use(http.post(`${BASE}/sites/site_1/irrigation-zones`, () => errorBody('x', 403)));
    renderPanel([]);
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Z');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    expect(await screen.findByTestId('garden-plan-zone-error')).toHaveTextContent(/permission/);
  });

  it('has no axe violations in the form', async () => {
    const user = userEvent.setup();
    const { container } = renderPanel([], 'lead');
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    await expectNoA11yViolations(container);
  });
});

describe('watering round errors', () => {
  async function openRound() {
    const user = userEvent.setup();
    mockStatus('z1', status());
    renderPanel([zone('z1', { location_keys: ['loc_a'] })]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(await screen.findByTestId('garden-plan-zone-round-open'));
    await user.type(screen.getByTestId('garden-plan-round-volume'), '5');
    return user;
  }

  it.each([
    [429, 'x', /Too many requests/],
    [403, 'x', /permission/],
    [422, 'irrigation_zone.no_beds', /no bed yet/],
    [422, 'irrigation_zone.no_bed_area', /No bed of the zone has an area/],
  ])('shows %i %s as text', async (status_, code, text) => {
    server.use(http.post(`${BASE}/irrigation-zones/z1/log-watering`, () => errorBody(code, status_)));
    const user = await openRound();
    await user.click(screen.getByTestId('garden-plan-round-submit'));
    expect(await screen.findByTestId('garden-plan-round-error')).toHaveTextContent(text);
  });

  it('has no axe violations', async () => {
    await openRound();
    await expectNoA11yViolations(screen.getByTestId('garden-plan-round-dialog'));
  });
});

/** The panel on the real zone hook: a save reloads the list from the endpoint, so `zones` really changes. */
function LivePanel({ selectedBedKeys = [], unsavedBed = false }: { selectedBedKeys?: string[]; unsavedBed?: boolean }) {
  const plan = useMemo(() => zonePlan(unsavedBed ? [{ name: 'Unsaved bed' }] : []), [unsavedBed]);
  const data = useIrrigationZones('site_1', plan.zones, true);
  return (
    <ZonePanel plan={plan} zoneData={data} selectedBedKeys={selectedBedKeys} onChanged={() => undefined} onClose={() => undefined} />
  );
}

function renderLive(
  role: 'viewer' | 'grower' | 'lead' = 'grower',
  extra: { selectedBedKeys?: string[]; unsavedBed?: boolean } = {},
) {
  return renderWithProviders(<LivePanel {...extra} />, {
    store: createTestStore({ ...tenantState(role), ...authState() }),
  });
}

describe('a zone that is gone (404)', () => {
  it('says so after a save, not only by leaving the form', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    server.use(http.patch(`${BASE}/irrigation-zones/z1`, () => errorBody('x', 404)));
    const { data } = renderPanel([zone('z1')]);
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.clear(screen.getByTestId('garden-plan-zone-name'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'New name');
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    expect(await screen.findByText('The zone no longer exists. The list is reloaded.')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-zone-form')).toBeNull();
    expect(data.reload).toHaveBeenCalled();
  });

  it('says so after a delete, not only by leaving the form', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    server.use(http.delete(`${BASE}/irrigation-zones/z1`, () => errorBody('x', 404)));
    const { data } = renderPanel([zone('z1', { name: 'South line' })], 'lead');
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    await user.click(screen.getByTestId('garden-plan-zone-delete'));
    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('The zone no longer exists. The list is reloaded.')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId('garden-plan-zone-form')).toBeNull());
    expect(screen.getByTestId('garden-plan-zone-row-z1')).toBeInTheDocument();
    expect(data.reload).toHaveBeenCalled();
  });
});

describe('a create whose bed assignment failed', () => {
  it('turns into the form of the created zone, keeps the ticked beds and says what is missing', async () => {
    const user = userEvent.setup();
    let list: IrrigationZone[] = [];
    let posts = 0;
    let puts = 0;
    const patches: unknown[] = [];
    const assigned: unknown[] = [];
    mockZoneList(() => list);
    mockStatus('z_new', status());
    server.use(
      http.post(`${BASE}/sites/site_1/irrigation-zones`, () => {
        posts += 1;
        const created = zone('z_new', { name: 'Drip line', irrigation_type: 'manual' });
        list = [created];
        return HttpResponse.json(created, { status: 201 });
      }),
      http.put(`${BASE}/irrigation-zones/z_new/locations`, async ({ request }) => {
        puts += 1;
        assigned.push(await request.json());
        if (puts === 1) return errorBody('reference.not_found', 422);
        list = [zone('z_new', { name: 'Drip line', irrigation_type: 'manual', location_keys: ['loc_a'] })];
        return HttpResponse.json({ ...list[0], added: ['loc_a'], removed: [], moved_from: {} });
      }),
      http.patch(`${BASE}/irrigation-zones/z_new`, async ({ request }) => {
        patches.push(await request.json());
        return HttpResponse.json(list[0]);
      }),
    );
    renderLive('lead');
    await user.click(await screen.findByTestId('garden-plan-zone-new'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Drip line');
    await user.click(screen.getByTestId('garden-plan-zone-bed-loc_a'));
    await user.click(screen.getByTestId('garden-plan-zone-save'));

    // The form is now the one of the created zone: its title, its delete, the beds still ticked.
    const error = await screen.findByTestId('garden-plan-zone-error');
    expect(error).toHaveTextContent('Zone Drip line was created, but its beds are not assigned yet.');
    expect(error).toHaveTextContent(/Save the plan first/);
    expect(screen.getByRole('heading', { name: 'Zone Drip line' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'New zone' })).toBeNull();
    expect(screen.getByTestId('garden-plan-zone-delete')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-zone-bed-loc_a')).toBeChecked();
    expect(screen.getByTestId('garden-plan-zone-name')).toHaveValue('Drip line');

    // Saving again assigns the beds only: no second zone, and no field is sent again.
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await waitFor(() => expect(puts).toBe(2));
    expect(assigned[1]).toEqual({ location_keys: ['loc_a'] });
    expect(posts).toBe(1);
    expect(patches).toEqual([]);
  });

  it('lists the created zone after a cancel, so "new" is not the way back to it', async () => {
    const user = userEvent.setup();
    let list: IrrigationZone[] = [];
    mockZoneList(() => list);
    mockStatus('z_new', status());
    server.use(
      http.post(`${BASE}/sites/site_1/irrigation-zones`, () => {
        list = [zone('z_new', { name: 'Drip line' })];
        return HttpResponse.json(list[0], { status: 201 });
      }),
      http.put(`${BASE}/irrigation-zones/z_new/locations`, () => errorBody('reference.not_found', 422)),
    );
    renderLive();
    await user.click(await screen.findByTestId('garden-plan-zone-new'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'Drip line');
    await user.click(screen.getByTestId('garden-plan-zone-bed-loc_a'));
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await screen.findByTestId('garden-plan-zone-error');
    await user.click(screen.getByTestId('garden-plan-zone-cancel'));
    expect(await screen.findByTestId('garden-plan-zone-row-z_new')).toHaveTextContent('Drip line');
  });
});

describe('a change whose bed assignment failed', () => {
  it('keeps the form, reloads the zone and sends only what is still different on the second save', async () => {
    const user = userEvent.setup();
    let list: IrrigationZone[] = [zone('z1', { name: 'Old name' })];
    let puts = 0;
    const patches: unknown[] = [];
    mockZoneList(() => list);
    mockStatus('z1', status());
    server.use(
      http.patch(`${BASE}/irrigation-zones/z1`, async ({ request }) => {
        const body = (await request.json()) as Partial<IrrigationZone>;
        patches.push(body);
        list = [{ ...list[0], ...body }];
        return HttpResponse.json(list[0]);
      }),
      http.put(`${BASE}/irrigation-zones/z1/locations`, () => {
        puts += 1;
        if (puts === 1) return errorBody('x', 500);
        list = [{ ...list[0], location_keys: ['loc_a'] }];
        return HttpResponse.json({ ...list[0], added: ['loc_a'], removed: [], moved_from: {} });
      }),
    );
    renderLive();
    await user.click(await screen.findByTestId('garden-plan-zone-row-z1'));
    await user.clear(screen.getByTestId('garden-plan-zone-name'));
    await user.type(screen.getByTestId('garden-plan-zone-name'), 'New name');
    await user.click(screen.getByTestId('garden-plan-zone-bed-loc_a'));
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    expect(await screen.findByTestId('garden-plan-zone-error')).toHaveTextContent('That did not work');
    // The reload brought the new name: the title follows, the ticked bed stays.
    expect(await screen.findByRole('heading', { name: 'Zone New name' })).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-zone-bed-loc_a')).toBeChecked();
    await user.click(screen.getByTestId('garden-plan-zone-save'));
    await waitFor(() => expect(puts).toBe(2));
    expect(patches).toEqual([{ name: 'New name' }]);
  });
});

describe('taking over the plan selection', () => {
  it('takes the saved beds of a mixed selection and says how many unsaved ones it skipped', async () => {
    const user = userEvent.setup();
    renderPanel([], 'grower', [], { selectedBedKeys: ['loc_a', 'tmpunsaved0'], unsavedBed: true });
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    await user.click(screen.getByTestId('garden-plan-zone-take-selection'));
    expect(screen.getByTestId('garden-plan-zone-bed-loc_a')).toBeChecked();
    expect(screen.getByRole('status')).toHaveTextContent(
      '1 selected bed is not saved yet and was not taken over. Save the plan, then take over the selection again.',
    );
  });
});

describe('headings', () => {
  it('ranks the form title below the panel title', async () => {
    const user = userEvent.setup();
    mockStatus('z1', status());
    renderPanel([zone('z1', { name: 'South line' })]);
    expect(screen.getByRole('heading', { level: 3, name: 'Irrigation zones' })).toBeInTheDocument();
    await user.click(screen.getByTestId('garden-plan-zone-row-z1'));
    expect(screen.getByRole('heading', { level: 4, name: 'Zone South line' })).toBeInTheDocument();
    await user.click(screen.getByTestId('garden-plan-zone-cancel'));
    await user.click(screen.getByTestId('garden-plan-zone-new'));
    expect(screen.getByRole('heading', { level: 4, name: 'New zone' })).toBeInTheDocument();
  });
});
