import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import * as api from '@/api/endpoints/aquaponik';

const T = '/api/v1/t/:tenant/aquaponics';

describe('aquaponik api endpoints', () => {
  beforeEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('listSystems / getSystem', async () => {
    server.use(
      http.get(`${T}/systems`, () => HttpResponse.json([{ key: 's1' }])),
      http.get(`${T}/systems/:key`, () => HttpResponse.json({ key: 's1' })),
    );
    expect((await api.listSystems())[0].key).toBe('s1');
    expect((await api.getSystem('s1')).key).toBe('s1');
  });

  it('createSystem / updateSystem / deleteSystem / setCyclingStatus', async () => {
    let deleted = false;
    let patched: unknown = null;
    let cyclingBody: unknown = null;
    server.use(
      http.post(`${T}/systems`, () => HttpResponse.json({ key: 's2' }, { status: 201 })),
      http.patch(`${T}/systems/:key`, async ({ request }) => {
        patched = await request.json();
        return HttpResponse.json({ key: 's2' });
      }),
      http.delete(`${T}/systems/:key`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
      http.post(`${T}/systems/:key/cycling-status`, async ({ request }) => {
        cyclingBody = await request.json();
        return HttpResponse.json({ key: 's2', cycling_status: 'cycled' });
      }),
    );
    expect(
      (await api.createSystem({
        name: 'X',
        system_type: 'media_bed',
        total_volume_liters: 100,
        grow_area_m2: 1,
      })).key,
    ).toBe('s2');
    await api.updateSystem('s2', { daily_feed_target_g: 50 });
    expect(patched).toMatchObject({ daily_feed_target_g: 50 });
    await api.deleteSystem('s2');
    expect(deleted).toBe(true);
    const updated = await api.setCyclingStatus('s2', 'cycled');
    expect(updated.cycling_status).toBe('cycled');
    expect(cyclingBody).toMatchObject({ cycling_status: 'cycled' });
  });

  it('stocks: list / create / mortality', async () => {
    let mortalityBody: unknown = null;
    server.use(
      http.get(`${T}/systems/:key/fish-stocks`, () => HttpResponse.json([{ key: 'st1' }])),
      http.post(`${T}/systems/:key/fish-stocks`, () =>
        HttpResponse.json({ key: 'st1' }, { status: 201 }),
      ),
      http.post(`${T}/systems/:key/fish-stocks/:stock/mortality`, async ({ request }) => {
        mortalityBody = await request.json();
        return HttpResponse.json({ key: 'st1', count: 0 });
      }),
    );
    expect((await api.listStocks('s1'))[0].key).toBe('st1');
    expect(
      (await api.createStock('s1', {
        name: 'C',
        species_key: 'tilapia_nile',
        count: 10,
        avg_weight_g: 100,
        stocking_date: '2026-03-01',
      })).key,
    ).toBe('st1');
    const after = await api.recordMortality('s1', 'st1', 3);
    expect(after.count).toBe(0);
    expect(mortalityBody).toMatchObject({ deaths: 3 });
  });

  it('water tests + analytics endpoints', async () => {
    server.use(
      http.get(`${T}/systems/:key/water-tests`, () => HttpResponse.json([{ key: 'wt1' }])),
      http.post(`${T}/systems/:key/water-tests`, () =>
        HttpResponse.json({ key: 'wt1', free_ammonia_mgl: 0.0057 }, { status: 201 }),
      ),
      http.get(`${T}/systems/:key/water-quality-status`, () =>
        HttpResponse.json([{ parameter: 'ph', severity: 'ok' }]),
      ),
      http.get(`${T}/systems/:key/nitrogen-cycle-chart`, () =>
        HttpResponse.json([{ nitrate_mgl: 40 }]),
      ),
      http.get(`${T}/systems/:key/cycling-progress`, () =>
        HttpResponse.json({ status: 'cycling', progress_percent: 50 }),
      ),
      http.get(`${T}/systems/:key/alerts`, () =>
        HttpResponse.json([{ parameter: 'nitrite', severity: 'critical' }]),
      ),
      http.get(`${T}/systems/:key/feeding-recommendation`, () =>
        HttpResponse.json({ recommended_g: 56.25 }),
      ),
    );
    expect((await api.listWaterTests('s1'))[0].key).toBe('wt1');
    expect((await api.recordWaterTest('s1', {
      ph: 7,
      ammonia_tan_mgl: 1,
      nitrite_mgl: 0,
      nitrate_mgl: 40,
      temperature_c: 25,
    })).free_ammonia_mgl).toBeCloseTo(0.0057);
    expect((await api.getWaterQualityStatus('s1'))[0].parameter).toBe('ph');
    expect((await api.getNitrogenCycleChart('s1'))[0].nitrate_mgl).toBe(40);
    expect((await api.getCyclingProgress('s1')).progress_percent).toBe(50);
    expect((await api.getAlerts('s1'))[0].severity).toBe('critical');
    expect((await api.getFeedingRecommendation('s1')).recommended_g).toBe(56.25);
  });

  it('listFishSpecies (global catalog)', async () => {
    server.use(
      http.get('/api/v1/fish-species', () =>
        HttpResponse.json([{ key: 'tilapia_nile', common_name_de: 'Nil-Tilapia' }]),
      ),
    );
    const species = await api.listFishSpecies();
    expect(species[0].common_name_de).toBe('Nil-Tilapia');
  });
});
