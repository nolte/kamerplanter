import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import * as tenantApi from '@/api/endpoints/tenants';
import type { TenantWithRole, TenantCreate } from '@/api/types';
import { isLightMode } from '@/config/mode';

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

export const createOrganization = createAsyncThunk(
  'tenants/createOrganization',
  async (data: TenantCreate) => {
    await tenantApi.createOrganization(data);
    const tenants = await tenantApi.listMyTenants();
    return tenants;
  },
);

const tenantSlice = createSlice({
  name: 'tenants',
  initialState,
  reducers: {
    switchTenant(state, action: PayloadAction<string>) {
      const slug = action.payload;
      const tenant = state.myTenants.find((t) => t.slug === slug);
      if (tenant) {
        state.activeTenant = tenant;
        try {
          localStorage.setItem(ACTIVE_TENANT_KEY, slug);
        } catch {
          // ignore storage errors
        }
      }
    },
    clearTenants(state) {
      state.activeTenant = null;
      state.myTenants = [];
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
        if (state.activeTenant) {
          try {
            localStorage.setItem(ACTIVE_TENANT_KEY, state.activeTenant.slug);
          } catch {
            // ignore
          }
        }
      })
      .addCase(loadMyTenants.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to load tenants';
      })
      .addCase(createOrganization.fulfilled, (state, action) => {
        state.myTenants = action.payload;
      });
  },
});

export const { switchTenant, clearTenants } = tenantSlice.actions;
export default tenantSlice.reducer;
