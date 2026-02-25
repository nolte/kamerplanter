import { renderHook } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

describe('useDocumentTitle', () => {
  afterEach(() => {
    document.title = '';
  });

  it('sets document title with suffix', () => {
    renderHook(() => useDocumentTitle('My Page'));
    expect(document.title).toBe('My Page — Kamerplanter');
  });

  it('resets title on unmount', () => {
    const { unmount } = renderHook(() => useDocumentTitle('Test'));
    expect(document.title).toBe('Test — Kamerplanter');
    unmount();
    expect(document.title).toBe('Kamerplanter');
  });

  it('updates title when value changes', () => {
    const { rerender } = renderHook(({ title }) => useDocumentTitle(title), {
      initialProps: { title: 'First' },
    });
    expect(document.title).toBe('First — Kamerplanter');
    rerender({ title: 'Second' });
    expect(document.title).toBe('Second — Kamerplanter');
  });
});
