import { describe, it, expect } from 'vitest';
import { getWidgetComponent, widgetRegistry } from '@/components/dashboard/widgetRegistry';

describe('widgetRegistry', () => {
  it('resolves a bespoke widget key to a component', () => {
    expect(getWidgetComponent('quick_actions')).not.toBeNull();
    expect(getWidgetComponent('weather_forecast')).not.toBeNull();
    expect(getWidgetComponent('winter_protection')).not.toBeNull();
  });

  it('resolves generic-shell widget keys to a component', () => {
    expect(getWidgetComponent('tasks_today')).not.toBeNull();
    expect(getWidgetComponent('care_reminders')).not.toBeNull();
  });

  it('returns null for an unknown widget key', () => {
    expect(getWidgetComponent('does_not_exist')).toBeNull();
    expect(getWidgetComponent('')).toBeNull();
  });

  it('resolves daily_tip to its own component, not the generic shell', () => {
    // Review SCR-004 — `DailyTipCard` was written, tested and mounted nowhere:
    // `daily_tip` fell through to `GenericWidget`, so REQ-031 §6.3's card had
    // never been on a screen and the `GET /ai/daily-tip` work behind it was
    // unreachable from the product.
    //
    // Identity, not "not null": every key resolves to *something*, so
    // `not.toBeNull()` is exactly the assertion that stayed green while the
    // widget was the generic fallback. The generic shell is named explicitly as
    // the thing this key must not be.
    const dailyTip = getWidgetComponent('daily_tip');
    const genericShell = getWidgetComponent('onboarding_progress');

    expect(dailyTip).not.toBeNull();
    expect(genericShell).not.toBeNull();
    expect(dailyTip).not.toBe(genericShell);
  });

  it('still shares one generic shell between the keys that have no bespoke view', () => {
    // The control for the test above: if every key resolved to its own object,
    // "is not the generic shell" would be true for all of them and say nothing.
    expect(getWidgetComponent('onboarding_progress')).toBe(getWidgetComponent('ipm_alerts'));
  });

  it('maps every catalog key to a lazy component reference', () => {
    for (const comp of Object.values(widgetRegistry)) {
      expect(comp).toBeTypeOf('object');
    }
    expect(Object.keys(widgetRegistry).length).toBeGreaterThan(10);
  });
});
