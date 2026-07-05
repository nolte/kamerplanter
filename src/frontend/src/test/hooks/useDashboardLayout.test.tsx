import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import type { ReactNode } from 'react';
import { useDashboardLayout } from '@/hooks/useDashboardLayout';
import { createStoreWithExpertise, createStoreWithModuleOverrides } from '../helpers';

/**
 * REQ-045 §4.3 — useDashboardLayout hook tests.
 *
 * Covers default layout derivation from experience_level and gating logic
 * (server availability + module visibility).
 */

describe('useDashboardLayout', () => {
  it('should derive default layout from beginner experience level when no stored layout exists', () => {
    const store = createStoreWithExpertise('beginner');
    const wrapper = ({ children }: { children: ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useDashboardLayout(), { wrapper });

    // Default layout should include beginner widgets
    expect(result.current.layout.widgets.length).toBeGreaterThan(0);
    const widgetKeys = result.current.layout.widgets.map((w) => w.widget_key);
    expect(widgetKeys).toContain('quick_actions');
    expect(widgetKeys).toContain('tasks_today');

    // Default layout should use deterministic instance ids (d-<key> format)
    expect(result.current.layout.widgets[0].instance_id).toMatch(/^d-/);

    // isCustomized should be false (no stored layout)
    expect(result.current.isCustomized).toBe(false);
  });

  it('should include expert widgets when experience level is expert', () => {
    const store = createStoreWithExpertise('expert');
    const wrapper = ({ children }: { children: ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useDashboardLayout(), { wrapper });

    // Expert layout should include expert-only widgets
    const widgetKeys = result.current.layout.widgets.map((w) => w.widget_key);
    expect(widgetKeys).toContain('phase_timeline');
    expect(widgetKeys).toContain('vpd_gauge');
  });

  it('should mark widget as not-renderable when module is hidden (REQ-042)', () => {
    // Create store with tasks module hidden
    const store = createStoreWithModuleOverrides('beginner', { tasks: 'disabled' });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useDashboardLayout(), { wrapper });

    // tasks_today widget requires 'tasks' module; when hidden, should not be renderable
    expect(result.current.isWidgetRenderable('tasks_today')).toBe(false);

    // quick_actions has no requiredModule — should be renderable
    expect(result.current.isWidgetRenderable('quick_actions')).toBe(true);
  });
});
