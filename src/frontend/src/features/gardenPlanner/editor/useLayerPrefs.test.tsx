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
  it('has the grid on by default and the irrigation layers off', () => {
    expect(DEFAULT_LAYER_PREFS).toEqual({ grid: true, zones: false, lastWatered: false });
    expect(TOGGLE_LAYERS).toEqual(['zones', 'lastWatered']);
    expect(LAYERS.map((layer) => layer.id)).toEqual(['grid', 'zones', 'lastWatered']);
  });
});

describe('useLayerPrefs', () => {
  it('keeps the default of a layer that an older stored choice does not know', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: false }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ grid: false, zones: false, lastWatered: false });
  });

  it('ignores non-boolean values and unknown layers', () => {
    window.localStorage.setItem(KEY, JSON.stringify({ grid: 'yes', zones: true, plants: true }));
    const { result } = renderHook(() => useLayerPrefs());
    expect(result.current.prefs).toEqual({ grid: true, zones: true, lastWatered: false });
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
});
