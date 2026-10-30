import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_LAYER_PREFS, LAYERS, TOGGLE_LAYERS } from './layers';
import { useLayerPrefs } from './useLayerPrefs';

const KEY = 'kp_garden_plan_layers';

afterEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe('layer registry', () => {
  it('has the grid and the underlay on by default and the irrigation, site-condition and plant-state layers off', () => {
    expect(DEFAULT_LAYER_PREFS).toEqual({
      grid: true,
      zones: false,
      lastWatered: false,
      underlay: true,
      sun: false,
      moisture: false,
      frost: false,
      plantState: false,
    });
    expect(TOGGLE_LAYERS).toEqual(['zones', 'lastWatered', 'underlay', 'sun', 'moisture', 'frost', 'plantState']);
    expect(LAYERS.map((layer) => layer.id)).toEqual([
      'grid',
      'zones',
      'lastWatered',
      'underlay',
      'sun',
      'moisture',
      'frost',
      'plantState',
    ]);
  });
});

describe('useLayerPrefs', () => {
  it('keeps the default of a layer that an older stored choice does not know', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: false }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ ...DEFAULT_LAYER_PREFS, grid: false });
  });

  it('ignores non-boolean values and unknown layers', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: 'yes', zones: true, plants: true }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ ...DEFAULT_LAYER_PREFS, zones: true });
  });

  it('restores a stored site-condition layer and defaults the ones it does not know (#2487)', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: true, zones: false, sun: true }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ ...DEFAULT_LAYER_PREFS, sun: true });
    act(() => result.current.setLayer('frost', true));
    expect(JSON.parse(window.localStorage.getItem(KEY) ?? '{}')).toMatchObject({ sun: true, frost: true });
  });

  it('restores a stored plant-state layer and keeps it off for an older stored choice (#2488)', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: true, frost: true }));
    expect(renderHook(() => useLayerPrefs()).result.current.prefs.plantState).toBe(false);
    window.localStorage.setItem(KEY, JSON.stringify({ plantState: true }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ ...DEFAULT_LAYER_PREFS, plantState: true });
  });

  it('stores a switch and survives a blocked storage', () => {
    const { result } = renderHook(() => useLayerPrefs());
    act(() => result.current.setLayer('zones', true));
    expect(JSON.parse(window.localStorage.getItem(KEY) ?? '{}')).toMatchObject({ zones: true });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    act(() => result.current.setLayer('lastWatered', true));
    expect(result.current.prefs.lastWatered).toBe(true);
  });

  it('keeps the visibility of the underlay per user in localStorage, never on the server', () => {
    const { result } = renderHook(() => useLayerPrefs());
    act(() => result.current.setLayer('underlay', false));
    expect(JSON.parse(window.localStorage.getItem(KEY) ?? '{}')).toMatchObject({ underlay: false });
    const again = renderHook(() => useLayerPrefs());
    expect(again.result.current.prefs.underlay).toBe(false);
  });
});
