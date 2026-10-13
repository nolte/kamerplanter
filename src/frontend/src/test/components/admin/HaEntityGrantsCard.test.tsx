import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import HaEntityGrantsCard from '@/components/admin/HaEntityGrantsCard';
import { renderWithProviders } from '../../helpers';
import { server } from '../../mocks/server';

/**
 * MT-015 (#2112) — the platform admin releases Home Assistant entities per garden.
 * The three admin endpoints are doubled at the process boundary; what reaches
 * them (path + body) is recorded, so a toggle is asserted as the request it makes.
 */

const TENANT = 'tenant-a';
const BASE = `/api/v1/admin/ha-entity-grants/tenants/${TENANT}`;

interface Calls {
  posts: unknown[];
  deletes: string[];
}

function registerHandlers(opts: { configured?: boolean; fail?: boolean } = {}): Calls {
  const calls: Calls = { posts: [], deletes: [] };
  server.use(
    http.get(`${BASE}/inventory`, () =>
      opts.fail
        ? HttpResponse.json({ message: 'x' }, { status: 500 })
        : HttpResponse.json({
            ha_configured: opts.configured ?? true,
            entities: [
              {
                entity_id: 'binary_sensor.front_door',
                domain: 'binary_sensor',
                friendly_name: 'Haustür',
                unit_of_measurement: null,
                device_class: 'door',
                granted: false,
                present: true,
              },
              {
                entity_id: 'sensor.old_probe',
                domain: 'sensor',
                friendly_name: null,
                unit_of_measurement: null,
                device_class: null,
                granted: true,
                present: false,
              },
              {
                entity_id: 'sensor.tent_temp',
                domain: 'sensor',
                friendly_name: 'Zelt Temperatur',
                unit_of_measurement: '°C',
                device_class: 'temperature',
                granted: true,
                present: true,
              },
            ],
          }),
    ),
    http.post(BASE, async ({ request }) => {
      calls.posts.push(await request.json());
      return HttpResponse.json({ created: 1, grants: [] });
    }),
    http.delete(`${BASE}/:entityId`, ({ params }) => {
      calls.deletes.push(String(params.entityId));
      return new HttpResponse(null, { status: 204 });
    }),
  );
  return calls;
}

function mount() {
  return renderWithProviders(<HaEntityGrantsCard tenantKey={TENANT} tenantName="Gemeinschaftsgarten" />);
}

describe('HaEntityGrantsCard', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('lists the inventory with the release state per entity and counts the releases', async () => {
    registerHandlers();
    mount();
    expect(await screen.findByTestId('ha-entity-grants-list')).toBeInTheDocument();
    expect(screen.getByTestId('ha-entity-grant-toggle-sensor-tent-temp').querySelector('input')).toBeChecked();
    expect(screen.getByTestId('ha-entity-grant-toggle-binary-sensor-front-door').querySelector('input')).not.toBeChecked();
    expect(screen.getByText(i18n.t('pages.admin.haGrants.grantedCount', { count: 2 }))).toBeInTheDocument();
    // a granted entity Home Assistant no longer reports is marked, not hidden
    expect(screen.getByTestId('ha-entity-grant-row-sensor-old-probe')).toHaveTextContent(
      i18n.t('pages.admin.haGrants.notPresent'),
    );
  });

  it('releases an entity by toggling it on', async () => {
    const user = userEvent.setup();
    const calls = registerHandlers();
    mount();
    const toggle = await screen.findByTestId('ha-entity-grant-toggle-binary-sensor-front-door');
    await user.click(toggle.querySelector('input')!);
    await waitFor(() => expect(calls.posts).toEqual([{ entity_ids: ['binary_sensor.front_door'] }]));
    await waitFor(() => expect(toggle.querySelector('input')).toBeChecked());
  });

  it('withdraws a release by toggling it off', async () => {
    const user = userEvent.setup();
    const calls = registerHandlers();
    mount();
    const toggle = await screen.findByTestId('ha-entity-grant-toggle-sensor-tent-temp');
    await user.click(toggle.querySelector('input')!);
    await waitFor(() => expect(calls.deletes).toEqual(['sensor.tent_temp']));
    await waitFor(() => expect(toggle.querySelector('input')).not.toBeChecked());
  });

  it('filters by search text and by release state', async () => {
    const user = userEvent.setup();
    registerHandlers();
    mount();
    await screen.findByTestId('ha-entity-grants-list');
    await user.type(screen.getByTestId('ha-entity-grants-search').querySelector('input')!, 'haustür');
    expect(screen.getByTestId('ha-entity-grant-row-binary-sensor-front-door')).toBeInTheDocument();
    expect(screen.queryByTestId('ha-entity-grant-row-sensor-tent-temp')).not.toBeInTheDocument();
    await user.clear(screen.getByTestId('ha-entity-grants-search').querySelector('input')!);
    await user.click(screen.getByTestId('ha-entity-grants-only-granted').querySelector('input')!);
    expect(screen.queryByTestId('ha-entity-grant-row-binary-sensor-front-door')).not.toBeInTheDocument();
    expect(screen.getByTestId('ha-entity-grant-row-sensor-tent-temp')).toBeInTheDocument();
  });

  it('releases a notify service by ID and refuses a malformed ID before sending', async () => {
    const user = userEvent.setup();
    const calls = registerHandlers();
    mount();
    await screen.findByTestId('ha-entity-grants-list');
    const input = screen.getByTestId('ha-entity-grants-manual-input').querySelector('input')!;
    await user.type(input, 'Notify Phone');
    expect(screen.getByTestId('ha-entity-grants-manual-submit')).toBeDisabled();
    expect(screen.getByText(i18n.t('pages.admin.haGrants.manualInvalid'))).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, 'notify.mobile_app_phone');
    await user.click(screen.getByTestId('ha-entity-grants-manual-submit'));
    await waitFor(() => expect(calls.posts).toEqual([{ entity_ids: ['notify.mobile_app_phone'] }]));
    expect(await screen.findByTestId('ha-entity-grant-row-notify-mobile-app-phone')).toBeInTheDocument();
  });

  it('says so when Home Assistant is not connected', async () => {
    registerHandlers({ configured: false });
    mount();
    expect(await screen.findByTestId('ha-entity-grants-not-configured')).toBeInTheDocument();
  });

  it('offers a retry when the inventory cannot be loaded', async () => {
    registerHandlers({ fail: true });
    mount();
    expect(await screen.findByTestId('ha-entity-grants-load-error')).toBeInTheDocument();
    registerHandlers();
    await userEvent.setup().click(screen.getByTestId('ha-entity-grants-retry'));
    expect(await screen.findByTestId('ha-entity-grants-list')).toBeInTheDocument();
  });
});
