/**
 * The editor on an indoor plan (REQ-053 WP 10.8, GP-FR-182, §9.8): no frost layer, and a plan without a stored grid
 * starts on its site type's 5 cm. Each site type once; the garden types are the counter-check (unchanged).
 */
import { cleanup, screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { SiteType } from '@/api/types';
import { server } from '@/test/mocks/server';
import { openPanelTab, setupEditor } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

beforeEach(() => {
  server.use(http.get('/api/v1/t/:tenant/sites/:key/irrigation-zones', () => HttpResponse.json([])));
});
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

const INDOOR: SiteType[] = ['indoor', 'windowsill', 'grow_tent'];
const GARDEN: SiteType[] = ['outdoor', 'greenhouse', 'balcony'];

function layerSwitches(): HTMLElement {
  openPanelTab('layers');
  return screen.getByTestId('garden-plan-side-panel-tabpanel-layers');
}

function gridStep(): string | null {
  openPanelTab('view');
  return (screen.getByTestId('garden-plan-grid-step') as HTMLInputElement).value;
}

describe('the frost layer', () => {
  it.each(INDOOR)('is not offered on a %s plan', (siteType) => {
    setupEditor({ plan: { ...testPlan(), siteType } });
    const layers = layerSwitches();
    expect(within(layers).queryByTestId('garden-plan-layer-frost')).toBeNull();
    // The other condition layers stay: sun and moisture are features of a windowsill too.
    expect(within(layers).getByTestId('garden-plan-layer-sun')).toBeInTheDocument();
    expect(within(layers).getByTestId('garden-plan-layer-moisture')).toBeInTheDocument();
  });

  it.each([...GARDEN, null])('is offered on a garden plan (%s), as before', (siteType) => {
    setupEditor({ plan: { ...testPlan(), siteType } });
    expect(within(layerSwitches()).getByTestId('garden-plan-layer-frost')).toBeInTheDocument();
  });
});

describe('the grid of a plan without a stored grid', () => {
  it.each(INDOOR)('starts on 5 cm on a %s plan', (siteType) => {
    setupEditor({ plan: { ...testPlan(), settings: null, siteType, defaultGridM: 0.05 } });
    expect(gridStep()).toBe('0.05');
  });

  it.each(GARDEN)('starts on 10 cm on a %s plan', (siteType) => {
    setupEditor({ plan: { ...testPlan(), settings: null, siteType, defaultGridM: 0.1 } });
    expect(gridStep()).toBe('0.1');
  });

  it('keeps a stored grid on an indoor plan: the default is for a new plan only', () => {
    setupEditor({ plan: { ...testPlan(), siteType: 'indoor', defaultGridM: 0.05 } });
    expect(gridStep()).toBe('0.1');
  });
});
