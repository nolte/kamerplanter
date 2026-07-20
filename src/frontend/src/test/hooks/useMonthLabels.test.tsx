import { renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import { useMonthLabels } from '@/hooks/useMonthLabels';

describe('useMonthLabels', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('returns twelve long localised month names in order', () => {
    const { result } = renderHook(() => useMonthLabels('long'));
    expect(result.current).toHaveLength(12);
    expect(result.current[0]).toBe('Januar');
    expect(result.current[9]).toBe('Oktober');
    expect(result.current[11]).toBe('Dezember');
  });

  it('returns short month names when asked', () => {
    const { result } = renderHook(() => useMonthLabels('short'));
    expect(result.current).toHaveLength(12);
    // Short form is locale-specific but must differ from the long form.
    expect(result.current[0]).not.toBe('Januar');
    expect(result.current[0].length).toBeLessThan('Januar'.length);
  });

  it('follows the active locale', () => {
    i18n.changeLanguage('en');
    const { result } = renderHook(() => useMonthLabels('long'));
    expect(result.current[0]).toBe('January');
    expect(result.current[11]).toBe('December');
  });

  it('keeps a stable reference across re-renders for the same locale', () => {
    const { result, rerender } = renderHook(() => useMonthLabels('long'));
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
