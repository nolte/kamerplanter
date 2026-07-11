import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import * as api from '@/api/endpoints/inventree';

const T = '/api/v1/t/:tenant';

describe('inventree api endpoints', () => {
  beforeEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('equipment: list / get / create / update / delete', async () => {
    let deleted = false;
    let created: unknown = null;
    let updated: unknown = null;
    server.use(
      http.get(`${T}/equipment`, () => HttpResponse.json([{ key: 'eq1', name: 'pH Pen' }])),
      http.get(`${T}/equipment/:key`, () => HttpResponse.json({ key: 'eq1', name: 'pH Pen' })),
      http.post(`${T}/equipment`, async ({ request }) => {
        created = await request.json();
        return HttpResponse.json({ key: 'eq2' }, { status: 201 });
      }),
      http.put(`${T}/equipment/:key`, async ({ request }) => {
        updated = await request.json();
        return HttpResponse.json({ key: 'eq2', status: 'maintenance' });
      }),
      http.delete(`${T}/equipment/:key`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    expect((await api.listEquipment())[0].key).toBe('eq1');
    expect((await api.getEquipment('eq1')).name).toBe('pH Pen');
    expect((await api.createEquipment({ name: 'Pump', equipment_type: 'pump' })).key).toBe('eq2');
    expect(created).toMatchObject({ name: 'Pump', equipment_type: 'pump' });
    const after = await api.updateEquipment('eq2', { status: 'maintenance' });
    expect(after.status).toBe('maintenance');
    expect(updated).toMatchObject({ status: 'maintenance' });
    await api.deleteEquipment('eq2');
    expect(deleted).toBe(true);
  });

  it('connections: list / create / health-check / delete', async () => {
    let deleted = false;
    server.use(
      http.get(`${T}/inventree/connections`, () =>
        HttpResponse.json([{ key: 'c1', name: 'Main', is_active: true }]),
      ),
      http.post(`${T}/inventree/connections`, () =>
        HttpResponse.json({ key: 'c1', api_token_set: true }, { status: 201 }),
      ),
      http.post(`${T}/inventree/connections/:key/health-check`, () =>
        HttpResponse.json({ healthy: true }),
      ),
      http.delete(`${T}/inventree/connections/:key`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    expect((await api.listConnections())[0].name).toBe('Main');
    expect(
      (await api.createConnection({ name: 'Main', base_url: 'https://it.example', api_token: 'x' }))
        .api_token_set,
    ).toBe(true);
    expect((await api.checkConnectionHealth('c1')).healthy).toBe(true);
    await api.deleteConnection('c1');
    expect(deleted).toBe(true);
  });

  it('references / transactions / sync', async () => {
    server.use(
      http.get(`${T}/inventree/references`, () =>
        HttpResponse.json([{ key: 'r1', entity_collection: 'fertilizers', auto_deduct: true }]),
      ),
      http.get(`${T}/inventree/transactions`, () =>
        HttpResponse.json([{ key: 'txn1', status: 'pending' }]),
      ),
      http.post(`${T}/inventree/sync/trigger`, () =>
        HttpResponse.json({ stock_sync: { updated: 1 }, push: { synced: 0 } }),
      ),
    );
    expect((await api.listReferences('fertilizers'))[0].auto_deduct).toBe(true);
    expect((await api.listTransactions('pending'))[0].status).toBe('pending');
    expect(await api.triggerSync()).toMatchObject({ stock_sync: { updated: 1 } });
  });
});
