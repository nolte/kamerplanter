import { act, renderHook } from '@testing-library/react';
import i18n from 'i18next';
import { afterEach, describe, expect, it } from 'vitest';
import type { Geometry } from '../model/types';
import { useRendererLabels } from './useRendererLabels';

const RECT: Geometry = { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1.5, rotation_deg: 0 };

afterEach(async () => {
  await act(() => i18n.changeLanguage('de'));
});

describe('useRendererLabels', () => {
  it('speaks German by default and builds the bed description from its parts', async () => {
    await act(() => i18n.changeLanguage('de'));
    const { result } = renderHook(() => useRendererLabels());
    const labels = result.current;
    expect(labels.canvasRole).toBe('Gartenplan');
    expect(labels.bed({ name: 'Hochbeet 3', size: labels.size(RECT, 3), plants: 6, openTasks: 2 })).toBe(
      'Hochbeet 3, Beet, 2 × 1,5 m, 6 Pflanzen, 2 offene Aufgaben',
    );
    // zero counts drop out; singular uses the singular form
    expect(labels.bed({ name: 'B', size: '1 m²', plants: 1, openTasks: 0 })).toBe('B, Beet, 1 m², 1 Pflanze');
    expect(labels.objectType('water_source')).toBe('Wasserstelle');
  });

  it('follows the language and formats numbers for it', async () => {
    await act(() => i18n.changeLanguage('en'));
    const { result } = renderHook(() => useRendererLabels());
    const labels = result.current;
    expect(labels.size(RECT, 3)).toBe('2 × 1.5 m');
    expect(labels.size({ kind: 'circle', origin: [0, 0], radius_m: 1.25 }, 5)).toBe('Ø 2.5 m');
    expect(labels.size({ kind: 'point', origin: [0, 0] }, 12.345)).toBe('12.35 m²');
    expect(labels.plant({ id: 'TOM-1' })).toBe('Plant TOM-1');
    expect(labels.cluster({ count: 3 })).toBe('3 plants');
  });

  it('is referentially stable between renders of one language', () => {
    const { result, rerender } = renderHook(() => useRendererLabels());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
