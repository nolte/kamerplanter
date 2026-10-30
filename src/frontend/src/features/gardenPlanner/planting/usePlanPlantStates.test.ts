import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/**
 * The data source of the plant-state layer (REQ-053 GP-UX-061, #2488, D-1): the existing bed answer per bed at
 * marker LOD, only while the layer is on, cached per bed, dropped on foreground / layer off.
 */
const mocks = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('@/api/client', () => ({ __esModule: true, default: { get: mocks.get }, tenantClient: { get: mocks.get } }));

import { markerLodBedKeys } from '../renderer/scene';
import { bed, normalizePlan, plantedBed, planResponse, viewportAt } from '../renderer/rendererTestKit';
import type { PlantStateWire } from './plantStateApi';
import { usePlanPlantStates } from './usePlanPlantStates';

const TODAY = new Date().toISOString().slice(0, 10);

function wire(plantKey: string, overdue: boolean): PlantStateWire {
  return {
    plant_key: plantKey,
    instance_id: plantKey.toUpperCase(),
    species_key: 'sp_tomato',
    species_name: 'Tomato',
    planted_on: '2026-04-01',
    lifecycle: 'active',
    phase: { key: 'ph_veg', name: 'vegetative', elapsed_d: 10 },
    last_care: {},
    attention: [],
    harvest: { ready: false },
    inputs: {
      open_tasks: overdue ? [{ category: 'pruning', due: '2020-01-01' }] : [],
      open_findings: 0,
      frost_risk: false,
      harvest_batches: 0,
      phase: { key: 'ph_veg', started_on: TODAY, typical_days: 30, allows_harvest: false, is_terminal: false },
    },
  };
}

/** Answers every bed with its three plants; the first plant of each bed has an overdue task. */
function answerBeds() {
  mocks.get.mockImplementation((url: string) => {
    const bedKey = /\/locations\/([^/]+)\/plant-states/.exec(url)?.[1] ?? '';
    return Promise.resolve({ data: [0, 1, 2].map((i) => wire(`${bedKey}_p${i}`, i === 0)) });
  });
}

/** 20 beds in a 5 × 4 grid; at 30 px/m only the three with 0.5 m spacing (15 px) reach marker LOD, the rest (0.2 m = 6 px) cluster. */
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

const plantStateCalls = () =>
  mocks.get.mock.calls.filter(([url]) => typeof url === 'string' && url.includes('/plant-states'));

beforeEach(() => {
  mocks.get.mockReset();
  answerBeds();
});
afterEach(() => vi.restoreAllMocks());

describe('usePlanPlantStates', () => {
  it('reads exactly the three beds at marker LOD of a 20-bed plan, one page each', async () => {
    const model = twentyBedPlan();
    const keys = markerLodBedKeys(model, viewportAt(-1, 13, 30));
    expect(keys.sort()).toEqual(['bed0', 'bed1', 'bed2']);
    const { result } = renderHook(() => usePlanPlantStates('site_1', keys, true));
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(9));
    expect(plantStateCalls()).toHaveLength(3);
    expect(result.current.requestCount()).toBe(3);
    for (const [url, config] of plantStateCalls()) {
      expect(url).toMatch(/^\/locations\/bed[012]\/plant-states$/);
      expect(config.params).toEqual({ offset: 0, limit: 200 });
    }
    // computed once per answer: the badge of the overdue plant, none on the others
    expect(result.current.states.bed0_p0.badge).toBe('overdue');
    expect(result.current.states.bed0_p1.badge).toBeNull();
    expect(result.current.states.bed0_p0.ariaLabel).toContain('Tomato');
    expect(result.current.phaseNames).toEqual({ ph_veg: 'vegetative' });
  });

  it('requests nothing while the layer is off', async () => {
    const keys = markerLodBedKeys(twentyBedPlan(), viewportAt(-1, 13, 30));
    const { result } = renderHook(() => usePlanPlantStates('site_1', keys, false));
    await act(async () => {
      await Promise.resolve();
    });
    expect(plantStateCalls()).toHaveLength(0);
    expect(result.current.requestCount()).toBe(0);
    expect(result.current.states).toEqual({});
  });

  it('caches per bed: panning within the same beds or back to a read bed asks nothing again', async () => {
    const { result, rerender } = renderHook(({ keys }) => usePlanPlantStates('site_1', keys, true), {
      initialProps: { keys: ['bed0', 'bed1'] as readonly string[] },
    });
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(6));
    rerender({ keys: ['bed1', 'bed0'] });
    rerender({ keys: ['bed1'] });
    rerender({ keys: ['bed0', 'bed2'] });
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(9));
    expect(plantStateCalls().map(([url]) => url)).toEqual([
      '/locations/bed0/plant-states',
      '/locations/bed1/plant-states',
      '/locations/bed2/plant-states',
    ]);
  });

  it('ignores an answer that arrives after the layer went off, and reads again when it comes back', async () => {
    let release: (value: { data: PlantStateWire[] }) => void = () => undefined;
    mocks.get.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)));
    const { result, rerender } = renderHook(({ on }) => usePlanPlantStates('site_1', ['bed0'], on), {
      initialProps: { on: true },
    });
    expect(plantStateCalls()).toHaveLength(1);
    const signal = (plantStateCalls()[0][1] as { signal: AbortSignal }).signal;
    rerender({ on: false });
    expect(signal.aborted).toBe(true);
    await act(async () => {
      release({ data: [wire('bed0_p0', true)] });
      await Promise.resolve();
    });
    expect(result.current.states).toEqual({});
    rerender({ on: true });
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(3));
    expect(plantStateCalls()).toHaveLength(2);
  });

  it('drops the cache and reads the visible beds again when the page returns to the foreground (GP-FR-191)', async () => {
    const { result } = renderHook(() => usePlanPlantStates('site_1', ['bed0'], true));
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(3));
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await waitFor(() => expect(plantStateCalls()).toHaveLength(2));
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(3));
  });

  it('does not ask a failed bed again until the cache is dropped', async () => {
    mocks.get.mockImplementationOnce(() => Promise.reject(new Error('down')));
    const { result, rerender } = renderHook(({ keys }) => usePlanPlantStates('site_1', keys, true), {
      initialProps: { keys: ['bed0'] as readonly string[] },
    });
    await act(async () => {
      await Promise.resolve();
    });
    rerender({ keys: ['bed0', 'bed1'] });
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(3));
    expect(plantStateCalls().map(([url]) => url)).toEqual([
      '/locations/bed0/plant-states',
      '/locations/bed1/plant-states',
    ]);
    act(() => result.current.refresh());
    await waitFor(() => expect(Object.keys(result.current.states)).toHaveLength(6));
    expect(plantStateCalls()).toHaveLength(4);
  });
});
