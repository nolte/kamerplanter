import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import * as api from '@/api/endpoints/propagation';

const T = '/api/v1/t/:tenant';

describe('propagation api endpoints', () => {
  beforeEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('listPropagationEvents / getPropagationEvent', async () => {
    server.use(
      http.get(`${T}/propagation/events`, () => HttpResponse.json([{ _key: 'e1' }])),
      http.get(`${T}/propagation/events/:key`, () => HttpResponse.json({ _key: 'e1' })),
    );
    expect((await api.listPropagationEvents({ method: 'cutting' }))[0]._key).toBe('e1');
    expect((await api.getPropagationEvent('e1'))._key).toBe('e1');
  });

  it('createPropagationEvent / recordEventOutcome', async () => {
    let body: unknown = null;
    let outcome: unknown = null;
    server.use(
      http.post(`${T}/propagation/events`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ _key: 'e2' }, { status: 201 });
      }),
      http.patch(`${T}/propagation/events/:key/outcome`, async ({ request }) => {
        outcome = await request.json();
        return HttpResponse.json({ _key: 'e2', status: 'completed' });
      }),
    );
    const created = await api.createPropagationEvent({
      method: 'cutting',
      quantity: 5,
      parent_plant_keys: ['m1'],
      child_plant_keys: [],
    });
    expect(created._key).toBe('e2');
    expect(body).toMatchObject({ method: 'cutting', quantity: 5 });

    const updated = await api.recordEventOutcome('e2', { survived_count: 4 });
    expect(updated.status).toBe('completed');
    expect(outcome).toMatchObject({ survived_count: 4 });
  });

  it('getLineage / getDescendants', async () => {
    server.use(
      http.get(`${T}/plant-instances/:key/lineage`, () =>
        HttpResponse.json({ plant_key: 'p1', paths: [['m1']], ancestors: [{ key: 'm1' }] }),
      ),
      http.get(`${T}/plant-instances/:key/descendants`, () =>
        HttpResponse.json({ plant_key: 'p1', descendants: [{ key: 'c1' }] }),
      ),
    );
    expect((await api.getLineage('p1')).ancestors[0].key).toBe('m1');
    expect((await api.getDescendants('p1')).descendants[0].key).toBe('c1');
  });

  it('checkGraftCompatibility', async () => {
    let params: URLSearchParams | null = null;
    server.use(
      http.get(`${T}/propagation/graft-compatibility`, ({ request }) => {
        params = new URL(request.url).searchParams;
        return HttpResponse.json({
          scion_key: 's1',
          rootstock_key: 'r1',
          scion_species_key: 'tomato',
          rootstock_species_key: 'tomato2',
          compatible: true,
          level: 'compatible',
          same_genus: true,
          same_family: true,
          message: 'ok',
        });
      }),
    );
    const result = await api.checkGraftCompatibility('s1', 'r1');
    expect(result.compatible).toBe(true);
    expect(params!.get('scion_key')).toBe('s1');
    expect(params!.get('rootstock_key')).toBe('r1');
  });
});
