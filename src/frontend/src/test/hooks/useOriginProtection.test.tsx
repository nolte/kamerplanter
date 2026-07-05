import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n/i18n';
import { createTestStore } from '@/test/helpers';
import { useOriginProtection, resolveOrigin } from '@/hooks/useOriginProtection';

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={createTestStore()}>
      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
    </Provider>
  );
}

describe('useOriginProtection', () => {
  it('treats system origin as fully protected', () => {
    const { result } = renderHook(() => useOriginProtection({ origin: 'system' }), { wrapper });
    expect(result.current.origin).toBe('system');
    expect(result.current.isReadOnly).toBe(true);
    expect(result.current.isDeletionProtected).toBe(true);
    expect(result.current.canCopyAsTemplate).toBe(true);
  });

  it('treats enrichment as read-only but deletable', () => {
    const { result } = renderHook(() => useOriginProtection({ origin: 'enrichment' }), { wrapper });
    expect(result.current.isReadOnly).toBe(true);
    expect(result.current.isDeletionProtected).toBe(false);
    expect(result.current.canCopyAsTemplate).toBe(false);
  });

  it('treats import as fully editable', () => {
    const { result } = renderHook(() => useOriginProtection({ origin: 'import' }), { wrapper });
    expect(result.current.isReadOnly).toBe(false);
    expect(result.current.isDeletionProtected).toBe(false);
  });

  it('falls back to tenant when nothing is provided', () => {
    const { result } = renderHook(() => useOriginProtection({}), { wrapper });
    expect(result.current.origin).toBe('tenant');
    expect(result.current.isReadOnly).toBe(false);
    expect(result.current.isDeletionProtected).toBe(false);
  });

  it('upgrades isSystem=true to system protection', () => {
    const { result } = renderHook(() => useOriginProtection({ isSystem: true }), { wrapper });
    expect(result.current.origin).toBe('system');
    expect(result.current.isReadOnly).toBe(true);
  });

  it('exposes a localised tooltip text', () => {
    const { result } = renderHook(() => useOriginProtection({ origin: 'system' }), { wrapper });
    expect(result.current.tooltipText.length).toBeGreaterThan(0);
    expect(result.current.tooltipText).not.toMatch(/common\.origin/);
  });
});

describe('resolveOrigin', () => {
  it('returns the origin when present', () => {
    expect(resolveOrigin({ origin: 'system' })).toBe('system');
    expect(resolveOrigin({ origin: 'enrichment' })).toBe('enrichment');
  });

  it('returns undefined when the entity has no origin', () => {
    expect(resolveOrigin({})).toBeUndefined();
  });

  it('returns undefined for null and undefined entities', () => {
    expect(resolveOrigin(null)).toBeUndefined();
    expect(resolveOrigin(undefined)).toBeUndefined();
  });
});
