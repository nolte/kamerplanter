import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import PestScanButton from '@/components/pests/PestScanButton';

vi.mock('@/config/mode', () => ({
  isLightMode: false,
  isFullMode: true,
  KAMERPLANTER_MODE: 'full',
}));

// The dialog is not under test here; the button's whole decision is whether to
// render at all.
vi.mock('@/components/pests/PestDetectionDialog', () => ({
  default: () => null,
}));

const STATUS_AVAILABLE = {
  pestDetection: {
    status: {
      available: true,
      feature_enabled: true,
      primary_adapter: 'local_pest_symptom',
      active_adapter: 'local_pest_symptom',
      adapters: {},
    },
    statusLoading: false,
    result: null,
    detecting: false,
    history: [],
    historyLoading: false,
    error: null,
    errorCode: null,
  },
};

function tenantState(role: 'lead' | 'grower' | 'viewer' | null) {
  return {
    tenants: {
      activeTenant: role ? { key: 't1', slug: 't1', name: 'Garten', role, admin_scopes: [] } : null,
      myTenants: [],
      isLoading: false,
      error: null,
    },
  };
}

function render(role: 'lead' | 'grower' | 'viewer' | null) {
  return renderWithProviders(<PestScanButton plantKey="p1" />, {
    store: createTestStore({ ...STATUS_AVAILABLE, ...tenantState(role) }),
  });
}

describe('PestScanButton', () => {
  // #1333 — the server refuses the plant-bound detect and the feedback write
  // below grower. The plant detail page mounts this button for every member,
  // so the gate has to live here: a button that opens a dialog only to end in
  // a 403 is a guard that is visible and inert.
  it('is not offered to a viewer', () => {
    render('viewer');

    expect(screen.queryByTestId('pest-scan-button')).not.toBeInTheDocument();
  });

  it.each(['grower', 'lead'] as const)('is offered to a %s', (role) => {
    render(role);

    expect(screen.getByTestId('pest-scan-button')).toBeInTheDocument();
  });

  // No active tenant yet is the bootstrap, not a refusal (same reading as
  // `RequireRole`); the button must not flash away while `loadMyTenants` runs.
  it('stays while no active tenant is known yet', () => {
    render(null);

    expect(screen.getByTestId('pest-scan-button')).toBeInTheDocument();
  });
});
