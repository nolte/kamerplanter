/**
 * The auth bootstrap loads profile, tenants and preferences once per app start (#3022).
 *
 * Before the fix the "after login" effect fired as soon as the bootstrap's own
 * refresh made the session authenticated, so every start sent `/auth/me`, the
 * tenant list and the preferences twice.
 */
import { render, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import AuthProvider from '@/auth/AuthProvider';
import * as authApi from '@/api/endpoints/auth';
import * as tenantApi from '@/api/endpoints/tenants';
import * as preferencesApi from '@/api/endpoints/userPreferences';
import { createTestStore } from '@/test/helpers';

vi.mock('@/config/mode', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/config/mode')>()),
  isLightMode: false,
}));
vi.mock('@/api/endpoints/auth');
vi.mock('@/api/endpoints/tenants');
vi.mock('@/api/endpoints/userPreferences');

beforeEach(() => {
  vi.mocked(authApi.refresh).mockResolvedValue({ access_token: 'token-1' } as never);
  vi.mocked(authApi.getProfile).mockResolvedValue({ key: 'u1' } as never);
  vi.mocked(tenantApi.listMyTenants).mockResolvedValue([]);
  vi.mocked(preferencesApi.getPreferences).mockResolvedValue({} as never);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('AuthProvider bootstrap', () => {
  it('loads the profile, the tenants and the preferences once per app start', async () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <AuthProvider>
          <span />
        </AuthProvider>
      </Provider>,
    );

    await waitFor(() => expect(store.getState().auth.initialized).toBe(true));
    await waitFor(() => expect(preferencesApi.getPreferences).toHaveBeenCalled());

    expect(authApi.refresh).toHaveBeenCalledTimes(1);
    expect(authApi.getProfile).toHaveBeenCalledTimes(1);
    expect(tenantApi.listMyTenants).toHaveBeenCalledTimes(1);
    expect(preferencesApi.getPreferences).toHaveBeenCalledTimes(1);
  });
});
