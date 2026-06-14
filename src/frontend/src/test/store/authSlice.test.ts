import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearError,
  setAccessToken,
  clearAuth,
  loginLocal,
  registerLocal,
  fetchProfile,
  logoutUser,
  refreshAccessToken,
} from '@/store/slices/authSlice';

function createStore() {
  return configureStore({ reducer: { auth: reducer } });
}

describe('authSlice', () => {
  it('has the unauthenticated initial state with loading enabled', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('clearError removes a stored error message', () => {
    const initial = reducer(undefined, { type: 'unknown' });
    const withError = { ...initial, error: 'Boom' };
    const state = reducer(withError, clearError());
    expect(state.error).toBeNull();
  });

  it('setAccessToken stores the token and marks the session authenticated', () => {
    const state = reducer(undefined, setAccessToken('jwt-abc'));
    expect(state.accessToken).toBe('jwt-abc');
    expect(state.isAuthenticated).toBe(true);
  });

  it('clearAuth wipes user, token and authenticated flag', () => {
    const authed = {
      user: { key: 'u1' } as never,
      accessToken: 'jwt-abc',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    };
    const state = reducer(authed, clearAuth());
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('loginLocal.pending sets loading and clears prior error', () => {
    const withError = { ...reducer(undefined, { type: 'unknown' }), error: 'old' };
    const state = reducer(withError, { type: loginLocal.pending.type });
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('loginLocal.fulfilled stores the access token and authenticates', () => {
    const state = reducer(undefined, {
      type: loginLocal.fulfilled.type,
      payload: { access_token: 'jwt-xyz' },
    });
    expect(state.accessToken).toBe('jwt-xyz');
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it('loginLocal.rejected stores the parsed error and stops loading', () => {
    const state = reducer(undefined, {
      type: loginLocal.rejected.type,
      error: { message: 'Invalid credentials' },
    });
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Invalid credentials');
  });

  it('registerLocal.pending sets loading and clears prior error', () => {
    const withError = { ...reducer(undefined, { type: 'unknown' }), error: 'old' };
    const state = reducer(withError, { type: registerLocal.pending.type });
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('registerLocal.fulfilled stops loading without authenticating', () => {
    const state = reducer(
      { ...reducer(undefined, { type: 'unknown' }), isLoading: true },
      { type: registerLocal.fulfilled.type, payload: { key: 'u1' } },
    );
    expect(state.isLoading).toBe(false);
    expect(state.isAuthenticated).toBe(false);
  });

  it('registerLocal.rejected stores the parsed error', () => {
    const state = reducer(undefined, {
      type: registerLocal.rejected.type,
      error: { message: 'Email already used' },
    });
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Email already used');
  });

  it('fetchProfile.fulfilled stores the user and authenticates', () => {
    const user = { key: 'u1', email: 'a@b.de' };
    const state = reducer(undefined, {
      type: fetchProfile.fulfilled.type,
      payload: user,
    });
    expect(state.user).toEqual(user);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it('fetchProfile.rejected clears the session', () => {
    const authed = {
      user: { key: 'u1' } as never,
      accessToken: 'jwt',
      isAuthenticated: true,
      isLoading: true,
      error: null,
    };
    const state = reducer(authed, { type: fetchProfile.rejected.type });
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('logoutUser.fulfilled clears the session', () => {
    const authed = {
      user: { key: 'u1' } as never,
      accessToken: 'jwt',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    };
    const state = reducer(authed, { type: logoutUser.fulfilled.type });
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('refreshAccessToken.fulfilled stores the rotated token and authenticates', () => {
    const state = reducer(undefined, {
      type: refreshAccessToken.fulfilled.type,
      payload: { access_token: 'jwt-rotated' },
    });
    expect(state.accessToken).toBe('jwt-rotated');
    expect(state.isAuthenticated).toBe(true);
  });

  it('refreshAccessToken.rejected clears the session', () => {
    const authed = {
      user: { key: 'u1' } as never,
      accessToken: 'jwt',
      isAuthenticated: true,
      isLoading: true,
      error: null,
    };
    const state = reducer(authed, { type: refreshAccessToken.rejected.type });
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });

  it('updates state through the store when dispatching plain action creators', () => {
    const store = createStore();
    store.dispatch(setAccessToken('jwt-store'));
    expect(store.getState().auth.accessToken).toBe('jwt-store');
    store.dispatch(clearAuth());
    expect(store.getState().auth.isAuthenticated).toBe(false);
  });

  it('authenticates via the loginLocal thunk against the mocked API', async () => {
    const store = createStore();
    await store.dispatch(loginLocal({ email: 'demo@kamerplanter.local', password: 'pw' }));
    const state = store.getState().auth;
    expect(state.accessToken).toBe('jwt-msw');
    expect(state.isAuthenticated).toBe(true);
  });

  it('registers a new account via the registerLocal thunk', async () => {
    const store = createStore();
    await store.dispatch(
      registerLocal({ email: 'new@kamerplanter.local', password: 'pw', display_name: 'New' }),
    );
    const state = store.getState().auth;
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('loads the profile via the fetchProfile thunk', async () => {
    const store = createStore();
    await store.dispatch(fetchProfile());
    const state = store.getState().auth;
    expect(state.user?.email).toBe('demo@kamerplanter.local');
    expect(state.isAuthenticated).toBe(true);
  });

  it('rotates the token via the refreshAccessToken thunk', async () => {
    const store = createStore();
    await store.dispatch(refreshAccessToken());
    expect(store.getState().auth.accessToken).toBe('jwt-refreshed');
  });

  it('clears the session via the logoutUser thunk', async () => {
    const store = createStore();
    store.dispatch(setAccessToken('jwt-store'));
    await store.dispatch(logoutUser());
    expect(store.getState().auth.isAuthenticated).toBe(false);
  });
});
