import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import * as authApi from '@/api/endpoints/auth';
import type { UserProfile } from '@/api/types';
import { parseApiError } from '@/api/errors';

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  // True once the one-time auth bootstrap (refresh + profile, or light-mode
  // profile fetch, or its timeout/error fallback) has completed. Route guards
  // gate their initial loading skeleton on this — NOT on `isLoading`, which also
  // toggles during in-flight login/register requests and would otherwise unmount
  // the login/register page mid-submit. Once true, it never returns to false.
  initialized: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  initialized: false,
};

export const loginLocal = createAsyncThunk(
  'auth/loginLocal',
  async (data: { email: string; password: string; remember_me?: boolean }) => {
    const response = await authApi.login(data);
    return response;
  },
);

export const registerLocal = createAsyncThunk(
  'auth/registerLocal',
  async (data: { email: string; password: string; display_name: string }) => {
    const profile = await authApi.register(data);
    return profile;
  },
);

export const fetchProfile = createAsyncThunk('auth/fetchProfile', async () => {
  const profile = await authApi.getProfile();
  return profile;
});

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  await authApi.logout();
});

export const refreshAccessToken = createAsyncThunk(
  'auth/refresh',
  async () => {
    const response = await authApi.refresh();
    return response;
  },
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
    setAccessToken(state, action: { payload: string }) {
      state.accessToken = action.payload;
      state.isAuthenticated = true;
    },
    clearAuth(state) {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
      // clearAuth is the timeout/error fallback of the auth bootstrap
      // (AuthProvider.initAuth) as well as the response-interceptor refresh
      // failure — in every case the bootstrap has concluded.
      state.initialized = true;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder.addCase(loginLocal.pending, (state) => {
      state.isLoading = true;
      state.error = null;
    });
    builder.addCase(loginLocal.fulfilled, (state, action) => {
      state.isLoading = false;
      state.accessToken = action.payload.access_token;
      state.isAuthenticated = true;
    });
    builder.addCase(loginLocal.rejected, (state, action) => {
      state.isLoading = false;
      state.error = parseApiError(action.error);
    });

    // Register
    builder.addCase(registerLocal.pending, (state) => {
      state.isLoading = true;
      state.error = null;
    });
    builder.addCase(registerLocal.fulfilled, (state) => {
      state.isLoading = false;
    });
    builder.addCase(registerLocal.rejected, (state, action) => {
      state.isLoading = false;
      state.error = parseApiError(action.error);
    });

    // Fetch profile
    builder.addCase(fetchProfile.pending, (state) => {
      state.isLoading = true;
    });
    builder.addCase(fetchProfile.fulfilled, (state, action) => {
      state.isLoading = false;
      state.user = action.payload;
      state.isAuthenticated = true;
      // Light-mode bootstrap (AuthProvider.initAuth) completes via fetchProfile.
      state.initialized = true;
    });
    builder.addCase(fetchProfile.rejected, (state) => {
      state.isLoading = false;
      state.user = null;
      state.isAuthenticated = false;
      state.accessToken = null;
      state.initialized = true;
    });

    // Logout
    builder.addCase(logoutUser.fulfilled, (state) => {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
    });

    // Refresh
    builder.addCase(refreshAccessToken.fulfilled, (state, action) => {
      state.accessToken = action.payload.access_token;
      state.isAuthenticated = true;
      // JWT-mode bootstrap (AuthProvider.initAuth) begins with a token refresh.
      state.initialized = true;
    });
    builder.addCase(refreshAccessToken.rejected, (state) => {
      state.isLoading = false;
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
      state.initialized = true;
    });
  },
});

export const { clearError, setAccessToken, clearAuth } = authSlice.actions;
export default authSlice.reducer;
