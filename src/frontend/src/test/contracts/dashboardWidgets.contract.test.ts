import { describe, it, expect } from 'vitest';
import contract from '@/contracts/dashboard-widgets.json';
import { dashboardWidgetCatalog } from '@/config/dashboardWidgetCatalog';

/**
 * REQ-045 §6 — consumer-driven contract. The frontend widget catalog keys and
 * the backend KNOWN_WIDGET_KEYS must both equal the shared contract set. The
 * backend half lives in
 * ``src/backend/tests/contracts/test_dashboard_widgets_contract.py``.
 */
describe('dashboard widget catalog contract', () => {
  const contractKeys = [...contract.widget_keys].sort();
  const catalogKeys = Object.keys(dashboardWidgetCatalog).sort();

  it('catalog keys equal the shared contract', () => {
    expect(catalogKeys).toEqual(contractKeys);
  });

  it('every catalog entry keys its own record', () => {
    for (const [key, def] of Object.entries(dashboardWidgetCatalog)) {
      expect(def.key).toBe(key);
    }
  });

  it('has no duplicate contract keys', () => {
    expect(new Set(contract.widget_keys).size).toBe(contract.widget_keys.length);
  });
});
