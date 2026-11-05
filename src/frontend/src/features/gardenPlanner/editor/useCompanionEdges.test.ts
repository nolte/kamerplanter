import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/**
 * The data source of the companion-planting layer (REQ-053 GP-FR-134, WP 8.16): the per-bed companion-edges answer
 * for the visible beds at marker LOD only, while the layer is on, cached per bed and aborted on unmount.
 */
const mocks = vi.hoisted(() => ({ get: vi.fn(), capture: vi.fn() }));
vi.mock('@/api/client', () => ({ __esModule: true, default: { get: mocks.get }, tenantClient: { get: mocks.get } }));
vi.mock('@/observability/errorTracking', () => ({ captureHandledError: mocks.capture }));

import type { CompanionEdgeWire, CompanionEdgesWire } from '../api/companionEdges';
import { bed, normalizePlan, plantedBed, planResponse, viewportAt } from '../renderer/rendererTestKit';
import { COMPANION_CONCURRENCY, companionBedKeys, companionLinesOf, useCompanionEdges } from './useCompanionEdges';

function edge(a: string, b: string, status: CompanionEdgeWire['status'], positioned = true): CompanionEdgeWire {
  return {
    slot_a: { slot_key: a, position: positioned ? { x: 1, y: 1 } : null, species_keys: ['sp_a'] },
    slot_b: { slot_key: b, position: { x: 1.5, y: 1 }, species_keys: ['sp_b'] },
    status,
    reason_code: `companion.${status}`,
    reason: status === 'incompatible' ? 'Fennel inhibits most neighbours.' : null,
    score: status === 'compatible' ? 0.9 : null,
    deciding: null,
    distance_cm: 50,
  };
}

/** Every bed answers two drawable pairs. */
function answerBeds() {
  mocks.get.mockImplementation((url: string) => {
    const bedKey = /\/locations\/([^/]+)\/companion-edges/.exec(url)?.[1] ?? '';
    const answer: CompanionEdgesWire = {
      location_key: bedKey,
      edges: [edge(`${bedKey}_s0`, `${bedKey}_s1`, 'incompatible'), edge(`${bedKey}_s1`, `${bedKey}_s2`, 'compatible')],
      total: 2,
      truncated: false,
    };
    return Promise.resolve({ data: answer });
  });
}

/** 20 beds in a 5 x 4 grid; at 30 px/m only the three with 0.5 m spacing (15 px) reach marker LOD, the rest cluster. */
function twentyBedPlan() {
  const locations = [];
  const slots = [];
  const plants = [];
  for (let i = 0; i < 20; i += 1) {
    const key = `bed${i}`;
    const x = (i % 5) * 2;
    const y = Math.floor(i / 5) * 3;
    locations.push(bed(key, x, y));
    const planted = plantedBed(key, x, y, 3, i < 3 ? 0.5 : 0.2);
    slots.push(...planted.slots);
    plants.push(...planted.plants);
  }
  return normalizePlan(planResponse({ locations, garden_objects: [], slots, plants }));
}

const companionCalls = () =>
  mocks.get.mock.calls.filter(([url]) => typeof url === 'string' && url.includes('/companion-edges'));

beforeEach(() => {
  mocks.get.mockReset();
  mocks.capture.mockReset();
  answerBeds();
});
afterEach(() => vi.restoreAllMocks());

describe('companionBedKeys (LOD gate)', () => {
  it('names only the visible beds at marker LOD', () => {
    const model = twentyBedPlan();
    expect(companionBedKeys(model, viewportAt(-1, 13, 30)).sort()).toEqual(['bed0', 'bed1', 'bed2']);
    // below marker LOD every bed is a cluster: no bed, no read
    expect(companionBedKeys(model, viewportAt(-1, 13, 10))).toEqual([]);
    // closer in, all 20 beds reach marker LOD; a view over the first row only keeps the beds it shows
    expect(companionBedKeys(model, viewportAt(-1, 1, 60, 600, 60)).sort()).toEqual([
      'bed0',
      'bed1',
      'bed2',
      'bed3',
      'bed4',
    ]);
  });
});

describe('companionLinesOf', () => {
  it('skips an edge without a position and keeps the rest in answer order', () => {
    const answer: CompanionEdgesWire = {
      location_key: 'b',
      edges: [edge('s0', 's1', 'incompatible', false), edge('s1', 's2', 'compatible'), edge('s2', 's3', 'unknown')],
      total: 3,
      truncated: true,
    };
    const result = companionLinesOf({ b: answer }, ['b']);
    expect(result.lines.map((line) => line.id)).toEqual(['b:s1|s2', 'b:s2|s3']);
    expect(result.lines[0]).toEqual({ id: 'b:s1|s2', a: [1, 1], b: [1.5, 1], status: 'compatible' });
    expect(Object.keys(result.edges)).toEqual(['b:s1|s2', 'b:s2|s3']);
    expect(result.truncated).toBe(true);
    // a bed outside `bedKeys` draws nothing even when its answer is cached
    expect(companionLinesOf({ b: answer }, ['other']).lines).toEqual([]);
  });
});

describe('useCompanionEdges', () => {
  it('reads nothing while the layer is off or no bed is at marker LOD', async () => {
    const model = twentyBedPlan();
    const off = renderHook(() => useCompanionEdges('site_1', companionBedKeys(model, viewportAt(-1, 13, 30)), false));
    const far = renderHook(() => useCompanionEdges('site_1', companionBedKeys(model, viewportAt(-1, 13, 10)), true));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(companionCalls()).toHaveLength(0);
    expect(off.result.current.lines).toEqual([]);
    expect(far.result.current.lines).toEqual([]);
  });

  it('reads each visible bed once and caches it across pans inside the same beds', async () => {
    const model = twentyBedPlan();
    const { result, rerender } = renderHook(({ keys }) => useCompanionEdges('site_1', keys, true), {
      initialProps: { keys: companionBedKeys(model, viewportAt(-1, 13, 30)) },
    });
    await waitFor(() => expect(result.current.lines).toHaveLength(6));
    expect(companionCalls().map(([url]) => url).sort()).toEqual([
      '/locations/bed0/companion-edges',
      '/locations/bed1/companion-edges',
      '/locations/bed2/companion-edges',
    ]);
    // a pan that keeps the same beds in view, in another order, reads nothing again
    rerender({ keys: ['bed2', 'bed0', 'bed1'] });
    rerender({ keys: companionBedKeys(model, viewportAt(-0.9, 13.1, 30)) });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(result.current.requestCount()).toBe(3);
    // a bed that leaves the view draws nothing, and comes back from the cache without a read
    rerender({ keys: ['bed0'] });
    expect(result.current.lines.map((line) => line.id.split(':')[0])).toEqual(['bed0', 'bed0']);
    rerender({ keys: ['bed0', 'bed1'] });
    expect(result.current.lines).toHaveLength(4);
    expect(result.current.requestCount()).toBe(3);
  });

  it(`runs at most ${COMPANION_CONCURRENCY} reads at once and aborts them on unmount`, async () => {
    const signals: AbortSignal[] = [];
    mocks.get.mockImplementation((_url: string, config: { signal: AbortSignal }) => {
      signals.push(config.signal);
      return new Promise(() => undefined);
    });
    const keys = Array.from({ length: 10 }, (_, i) => `b${i}`);
    const { unmount } = renderHook(() => useCompanionEdges('site_1', keys, true));
    await waitFor(() => expect(signals).toHaveLength(COMPANION_CONCURRENCY));
    expect(signals.every((signal) => !signal.aborted)).toBe(true);
    unmount();
    expect(signals.every((signal) => signal.aborted)).toBe(true);
  });

  it('drops the answers when the layer goes off and reads again on refresh', async () => {
    const keys = ['b0'];
    const { result, rerender } = renderHook(({ on }) => useCompanionEdges('site_1', keys, on), {
      initialProps: { on: true },
    });
    await waitFor(() => expect(result.current.lines).toHaveLength(2));
    rerender({ on: false });
    expect(result.current.lines).toEqual([]);
    rerender({ on: true });
    await waitFor(() => expect(result.current.lines).toHaveLength(2));
    expect(result.current.requestCount()).toBe(2);
    result.current.refresh();
    await waitFor(() => expect(result.current.requestCount()).toBe(3));
  });

  it('keeps a failed bed without lines and does not ask it again for the same view', async () => {
    mocks.get.mockRejectedValue(new Error('boom'));
    const keys = ['b0'];
    const { result, rerender } = renderHook(({ k }) => useCompanionEdges('site_1', k, true), {
      initialProps: { k: keys },
    });
    await waitFor(() => expect(mocks.capture).toHaveBeenCalledTimes(1));
    rerender({ k: ['b0'] });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(result.current.requestCount()).toBe(1);
    expect(result.current.lines).toEqual([]);
  });

  it('returns the same object while nothing changed (useMemo)', async () => {
    const keys = ['b0'];
    const { result, rerender } = renderHook(() => useCompanionEdges('site_1', keys, true));
    await waitFor(() => expect(result.current.lines).toHaveLength(2));
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
