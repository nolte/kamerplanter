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
    expect(getWidgetComponent('vpd_gauge')).not.toBeNull();
  });

  it('returns null for an unknown widget key', () => {
    expect(getWidgetComponent('does_not_exist')).toBeNull();
    expect(getWidgetComponent('')).toBeNull();
  });

  it('maps every catalog key to a lazy component reference', () => {
    for (const comp of Object.values(widgetRegistry)) {
      expect(comp).toBeTypeOf('object');
    }
    expect(Object.keys(widgetRegistry).length).toBeGreaterThan(10);
  });
});
