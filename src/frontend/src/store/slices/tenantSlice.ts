import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import * as tenantApi from '@/api/endpoints/tenants';
import type { TenantWithRole, TenantCreate } from '@/api/types';
import { isLightMode } from '@/config/mode';
import { setActiveTenantSlug } from '@/api/client';
import { isApiError, parseApiError } from '@/api/errors';

interface TenantState {
  activeTenant: TenantWithRole | null;
  myTenants: TenantWithRole[];
  isLoading: boolean;
  error: string | null;
}

const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

function loadPersistedSlug(): string | null {
  if (isLightMode) return 'mein-garten';
  try {
    return localStorage.getItem(ACTIVE_TENANT_KEY);
  } catch {
    return null;
  }
}

const initialState: TenantState = {
  activeTenant: null,
  myTenants: [],
  isLoading: false,
  error: null,
};

export const loadMyTenants = createAsyncThunk('tenants/loadMyTenants', async () => {
  const tenants = await tenantApi.listMyTenants();
  return tenants;
});

/** Why founding an organisation was refused: the message and the backend's stable `error_code`. */
export interface CreateOrganizationRejection {
  message: string;
  errorCode: string | null;
}

/**
 * Found an organisation and reload the account's tenants. A refusal is passed on with its
 * `error_code` (REQ-056 §6.2: `ORGANIZATION_LIMIT_REACHED`) — the serialised default error of a
 * thunk keeps only the English message, which the page could not translate.
 */
export const createOrganization = createAsyncThunk<
  TenantWithRole[],
  TenantCreate,
  { rejectValue: CreateOrganizationRejection }
>('tenants/createOrganization', async (data, { rejectWithValue }) => {
  try {
    await tenantApi.createOrganization(data);
  } catch (err) {
    return rejectWithValue({
      message: parseApiError(err),
      errorCode: isApiError(err) ? err.errorCode : null,
    });
  }
  const tenants = await tenantApi.listMyTenants();
  return tenants;
});

const tenantSlice = createSlice({
  name: 'tenants',
  initialState,
  reducers: {
    switchTenant(state, action: PayloadAction<string>) {
      const slug = action.payload;
      const tenant = state.myTenants.find((t) => t.slug === slug);
      if (tenant) {
        state.activeTenant = tenant;
        setActiveTenantSlug(slug);
        try {
          localStorage.setItem(ACTIVE_TENANT_KEY, slug);
        } catch {
          // ignore storage errors
        }
      }
    },
    /**
     * Drop the active tenant while keeping the tenant list — stale-slug recovery.
     *
     * Dispatched by the recovery handler the composition root registers on the
     * API client (#1091 A-4): the backend refused the persisted slug, so it names
     * a tenant the user was removed from (or one that no longer exists) and every
     * global catalogue request would keep failing until it is gone.
     *
     * Distinct from {@link clearTenants}, which belongs to logout and wipes
     * `myTenants` too: here the list is about to be *reloaded*, and emptying it
     * meanwhile would make the tenant switcher vanish from the toolbar for the
     * duration. `loadMyTenants.fulfilled` then picks a tenant that still exists
     * and re-persists it, so `kp_active_tenant_slug` heals on its own.
     */
    clearActiveTenant(state) {
      state.activeTenant = null;
      setActiveTenantSlug(null);
      try {
        localStorage.removeItem(ACTIVE_TENANT_KEY);
      } catch {
        // ignore storage errors
      }
    },
    clearTenants(state) {
      state.activeTenant = null;
      state.myTenants = [];
      setActiveTenantSlug(null);
      try {
        localStorage.removeItem(ACTIVE_TENANT_KEY);
      } catch {
        // ignore
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadMyTenants.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loadMyTenants.fulfilled, (state, action) => {
        state.isLoading = false;
        state.myTenants = action.payload;
        // Restore persisted tenant or default to first
        const persistedSlug = loadPersistedSlug();
        const persisted = persistedSlug
          ? action.payload.find((t) => t.slug === persistedSlug)
          : null;
        state.activeTenant = persisted ?? action.payload[0] ?? null;
        const resolvedSlug = state.activeTenant?.slug ?? null;
        setActiveTenantSlug(resolvedSlug);
        try {
          if (resolvedSlug) {
            localStorage.setItem(ACTIVE_TENANT_KEY, resolvedSlug);
          } else {
            localStorage.removeItem(ACTIVE_TENANT_KEY);
          }
        } catch {
          // ignore
        }
      })
      .addCase(loadMyTenants.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'errors.tenantsLoadFailed';
      })
      .addCase(createOrganization.fulfilled, (state, action) => {
        state.myTenants = action.payload;
      });
  },
});

export const { switchTenant, clearActiveTenant, clearTenants } = tenantSlice.actions;
export default tenantSlice.reducer;
