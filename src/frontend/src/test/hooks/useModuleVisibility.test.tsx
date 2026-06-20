import { renderHook } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Provider } from 'react-redux';
import { type ReactNode } from 'react';

import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import {
  createStoreWithExpertise,
  createStoreWithModuleOverrides,
  type TestStore,
} from '@/test/helpers';

function wrapperFor(store: TestStore) {
  return ({ children }: { children: ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
}

function renderForStore(store: TestStore) {
  return renderHook(() => useModuleVisibility(), { wrapper: wrapperFor(store) });
}

describe('useModuleVisibility', () => {
  it('always reports core modules as visible regardless of level', () => {
    const { result } = renderForStore(createStoreWithExpertise('beginner'));
    expect(result.current.isModuleVisible('dashboard')).toBe(true);
    expect(result.current.isModuleVisible('plants')).toBe(true);
    expect(result.current.isModuleVisible('settings')).toBe(true);
  });

  it('hides a module with a disabled override even if the level would show it', () => {
    // 'calendar' defaults to beginner — visible at every level by default.
    const { result } = renderForStore(
      createStoreWithModuleOverrides('expert', { calendar: 'disabled' }),
    );
    expect(result.current.isModuleVisible('calendar')).toBe(false);
  });

  it('shows a module with an enabled override even at a lower level', () => {
    // 'tanks' defaults to expert — hidden for a beginner by default.
    const { result } = renderForStore(
      createStoreWithModuleOverrides('beginner', { tanks: 'enabled' }),
    );
    expect(result.current.isModuleVisible('tanks')).toBe(true);
  });

  it('follows the experience level when no override is set', () => {
    const beginner = renderForStore(createStoreWithExpertise('beginner'));
    expect(beginner.result.current.isModuleVisible('tanks')).toBe(false);
    expect(beginner.result.current.isModuleVisible('calendar')).toBe(true);

    const expert = renderForStore(createStoreWithExpertise('expert'));
    expect(expert.result.current.isModuleVisible('tanks')).toBe(true);
  });

  it('isPathVisible resolves owned paths through the owning module', () => {
    const { result } = renderForStore(
      createStoreWithModuleOverrides('expert', { tanks: 'disabled' }),
    );
    expect(result.current.isPathVisible('/standorte/tanks')).toBe(false);
    // Detail sub-path of a disabled module is also hidden.
    expect(result.current.isPathVisible('/standorte/tanks/123')).toBe(false);
  });

  it('isPathVisible returns true for paths owned by no module', () => {
    const { result } = renderForStore(createStoreWithExpertise('beginner'));
    expect(result.current.isPathVisible('/some/unknown/path')).toBe(true);
  });

  it('findModuleByPath matches detail paths to the owning module', () => {
    const { result } = renderForStore(createStoreWithExpertise('beginner'));
    expect(result.current.findModuleByPath('/standorte/tanks/123')?.key).toBe('tanks');
    expect(result.current.findModuleByPath('/standorte/tanks')?.key).toBe('tanks');
    expect(result.current.findModuleByPath('/nowhere')).toBeUndefined();
  });

  it('returns a stable memoized object across re-renders', () => {
    const { result, rerender } = renderForStore(createStoreWithExpertise('beginner'));
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
