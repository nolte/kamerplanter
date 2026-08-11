import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import type { ReactNode } from 'react';
import { useCanCreateCatalogEntry } from '@/hooks/useCanCreateCatalogEntry';
import { createTestStore } from '../helpers';
import type { TenantRole } from '@/api/types';

/**
 * #1091 A-7 — the predicate behind the species/cultivar create affordance.
 *
 * The gate that matters is the backend one (`_authorize_tenant_owned_create`,
 * SEC-005/#1113); this hook only decides whether a *dead* affordance is drawn.
 * Its whole risk is over-hiding: three states look like "no edit permission" from
 * the outside while the API in fact answers the create, so each of them gets its
 * own case here.
 */

function permissionsFor(
  role: TenantRole | null,
  { platformAdmin = false }: { platformAdmin?: boolean } = {},
): boolean {
  const store = createTestStore({
    tenants: {
      activeTenant:
        role === null ? null : { key: 't1', slug: 'garten', name: 'Garten', role },
      myTenants: [],
      isLoading: false,
      error: null,
    },
    auth: {
      user: { key: 'u1', is_platform_admin: platformAdmin },
      accessToken: null,
      isAuthenticated: true,
      isLoading: false,
      error: null,
      initialized: true,
    },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
  return renderHook(() => useCanCreateCatalogEntry(), { wrapper }).result.current;
}

describe('useCanCreateCatalogEntry — the role that may create', () => {
  it('offers the action to a grower', () => {
    // Creating is the edit boundary, not the lead boundary (REQ-049 §2.3).
    expect(permissionsFor('grower')).toBe(true);
  });

  it('offers the action to a lead', () => {
    expect(permissionsFor('lead')).toBe(true);
  });

  it('withholds the action from a viewer of the active tenant', () => {
    // The one case the package exists for: since #1091 A-2 the active tenant is a
    // request-borne input, so an organisation viewer would otherwise click a
    // button that answers 403.
    expect(permissionsFor('viewer')).toBe(false);
  });
});

describe('useCanCreateCatalogEntry — states that only look like a refusal', () => {
  it('keeps the action without an active tenant', () => {
    // NOT a refusal: full mode answers 422 ("pick a tenant"), light mode takes the
    // platform-admin arm and answers 201. Hiding here would remove the only create
    // path a light-mode installation has.
    expect(permissionsFor(null)).toBe(true);
  });

  it('keeps the action for a platform admin holding only a viewer membership', () => {
    // The backend gate bypasses the domain rank for a platform admin, so hiding on
    // `canEdit` alone would contradict a 201.
    expect(permissionsFor('viewer', { platformAdmin: true })).toBe(true);
  });

  it('keeps the action for a platform admin without any active tenant', () => {
    expect(permissionsFor(null, { platformAdmin: true })).toBe(true);
  });
});
