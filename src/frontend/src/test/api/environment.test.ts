import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import * as api from '@/api/endpoints/environment';

const T = '/api/v1/t/:tenant';

describe('environment api endpoints', () => {
  beforeEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('listActuators / listLocationActuators', async () => {
    server.use(
      http.get(`${T}/actuators`, () => HttpResponse.json([{ key: 'a1' }])),
      http.get(`${T}/locations/:key/actuators`, () => HttpResponse.json([{ key: 'a2' }])),
    );
    expect((await api.listActuators())[0].key).toBe('a1');
    expect((await api.listLocationActuators('loc1'))[0].key).toBe('a2');
  });

  it('createActuator / deleteActuator', async () => {
    let deleted = false;
    let body: unknown = null;
    server.use(
      http.post(`${T}/locations/:key/actuators`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ key: 'a3' }, { status: 201 });
      }),
      http.delete(`${T}/actuators/:key`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const created = await api.createActuator('loc1', {
      name: 'Light',
      actuator_type: 'light',
      protocol: 'home_assistant',
      ha_entity_id: 'light.zelt',
    });
    expect(created.key).toBe('a3');
    expect(body).toMatchObject({ name: 'Light', actuator_type: 'light' });
    await api.deleteActuator('a3');
    expect(deleted).toBe(true);
  });

  it('sendCommand posts command + value', async () => {
    let body: unknown = null;
    server.use(
      http.post(`${T}/actuators/:key/command`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ key: 'ev1', success: true, new_state: 'on' });
      }),
    );
    const event = await api.sendCommand('a1', 'set_value', 75);
    expect(event.success).toBe(true);
    expect(body).toMatchObject({ command: 'set_value', value: 75 });
  });

  it('setOverride / clearOverride / getActuatorState', async () => {
    let cleared = false;
    server.use(
      http.post(`${T}/actuators/:key/override`, () =>
        HttpResponse.json({ key: 'ov1', expires_at: '2026-07-11T12:00:00Z', is_active: true }),
      ),
      http.delete(`${T}/actuators/:key/override`, () => {
        cleared = true;
        return new HttpResponse(null, { status: 204 });
      }),
      http.get(`${T}/actuators/:key/state`, () =>
        HttpResponse.json({
          actuator_key: 'a1',
          current_state: 'on',
          current_value: 100,
          is_online: true,
          last_state_change: null,
          has_override: true,
        }),
      ),
    );
    const ov = await api.setOverride('a1', { expires_at: '2026-07-11T12:00:00Z', override_state: 'on' });
    expect(ov.key).toBe('ov1');
    await api.clearOverride('a1');
    expect(cleared).toBe(true);
    const state = await api.getActuatorState('a1');
    expect(state.has_override).toBe(true);
  });

  it('listActuatorEvents / emergencyStop', async () => {
    let scenario: unknown = null;
    server.use(
      http.get(`${T}/actuators/:key/events`, () => HttpResponse.json([{ key: 'ev1' }])),
      http.post(`${T}/emergency-stop`, async ({ request }) => {
        scenario = await request.json();
        return HttpResponse.json({
          scenario: 'fire_alarm',
          stopped: ['a1'],
          forced_on: [],
          failed: [],
        });
      }),
    );
    expect((await api.listActuatorEvents('a1'))[0].key).toBe('ev1');
    const result = await api.emergencyStop('fire_alarm');
    expect(result.stopped).toEqual(['a1']);
    expect(scenario).toMatchObject({ scenario: 'fire_alarm' });
  });
});
