import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import type { ReactNode } from 'react';
import tenantsReducer from '@/store/slices/tenantSlice';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { AdminScope, TenantRole, TenantWithRole } from '@/api/types';

/**
 * REQ-049 (#780) — the UI's single read of both permission axes.
 *
 * Every case here exists to hold the two axes apart. If they ever collapse back
 * into one, the symptom is silent: a button appears for someone the backend
 * then rejects, or disappears for someone entitled to it.
 */

function tenant(role: TenantRole, adminScopes: AdminScope[]): TenantWithRole {
  return {
    key: 't1',
    name: 'Garten',
    slug: 'garten',
    tenant_type: 'organization',
    description: null,
    role,
    admin_scopes: adminScopes,
    avatar_url: null,
    owner_key: 'u1',
    max_members: 50,
    created_at: null,
    updated_at: null,
  };
}

function permissionsFor(activeTenant: TenantWithRole | null) {
  const store = configureStore({
    reducer: { tenants: tenantsReducer },
    preloadedState: {
      tenants: { activeTenant, myTenants: [], isLoading: false, error: null },
    },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
  return renderHook(() => useTenantPermissions(), { wrapper }).result.current;
}

describe('useTenantPermissions — axis 1 (domain role)', () => {
  it('lets a lead edit and delete', () => {
    const p = permissionsFor(tenant('lead', []));
    expect(p.canEdit).toBe(true);
    expect(p.canDelete).toBe(true);
  });

  it('lets a grower edit but never delete', () => {
    // The deliberate REQ-049 correction: the grower/lead boundary runs along
    // irreversibility. REQ-024 §1a.1 always said so.
    const p = permissionsFor(tenant('grower', []));
    expect(p.canEdit).toBe(true);
    expect(p.canDelete).toBe(false);
  });

  it('lets a viewer do neither', () => {
    const p = permissionsFor(tenant('viewer', []));
    expect(p.canEdit).toBe(false);
    expect(p.canDelete).toBe(false);
  });
});

describe('useTenantPermissions — axis 2 (administrative scopes)', () => {
  it('grants member management to a viewer holding the scope', () => {
    // The club secretary: keeps the member list, changes nothing in the garden.
    const p = permissionsFor(tenant('viewer', ['management']));
    expect(p.canManageMembers).toBe(true);
    expect(p.canInvite).toBe(true);
    expect(p.canEdit).toBe(false);
  });

  it('denies member management to a lead without the scope', () => {
    // Without this, "lead" quietly becomes the old "admin" again.
    const p = permissionsFor(tenant('lead', []));
    expect(p.canManageMembers).toBe(false);
    expect(p.canConfigureIntegrations).toBe(false);
  });

  it('keeps the two scopes from substituting for each other', () => {
    const p = permissionsFor(tenant('grower', ['technical']));
    expect(p.canConfigureIntegrations).toBe(true);
    expect(p.canManageMembers).toBe(false);
  });
});

describe('useTenantPermissions — edge cases', () => {
  it('grants nothing without an active tenant', () => {
    const p = permissionsFor(null);
    expect(p.hasTenant).toBe(false);
    expect(p.role).toBeNull();
    expect(p.canEdit).toBe(false);
    expect(p.canManageMembers).toBe(false);
  });

  it('treats a tenant cached before REQ-049 as having no scopes', () => {
    // A record persisted by an older build carries no admin_scopes at all;
    // reading that as "no administrative rights" beats crashing.
    const legacy = { ...tenant('lead', []), admin_scopes: undefined } as unknown as TenantWithRole;
    const p = permissionsFor(legacy);
    expect(p.adminScopes).toEqual([]);
    expect(p.canManageMembers).toBe(false);
    expect(p.canDelete).toBe(true);
  });
});
