import { createAsyncThunk, createSlice, miniSerializeError } from '@reduxjs/toolkit';
import { isRateLimited } from '@/api/client';
import * as authApi from '@/api/endpoints/auth';
import type { UserProfile } from '@/api/types';
import { isApiError, parseApiError } from '@/api/errors';
import { releasePushSubscription } from '@/lib/pushSubscription';
import { forgetPendingInvitation } from '@/utils/pendingInvitation';

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

/** The backend's `error_code` for a correct password on an unverified address (#2037). */
export const EMAIL_NOT_VERIFIED = 'EMAIL_NOT_VERIFIED';

export const loginLocal = createAsyncThunk(
  'auth/loginLocal',
  async (data: { email: string; password: string; remember_me?: boolean }) => {
    const response = await authApi.login(data);
    return response;
  },
  {
    // RTK's default serialisation keeps name/message/stack/`code` of the thrown
    // error, and an `ApiError` carries the backend's code as `errorCode` — so it
    // was dropped, and the login page could not tell "unverified" from any other
    // refusal. Carried as `code`, which `SerializedError` already has (#2037).
    serializeError: (error) => ({
      ...miniSerializeError(error),
      ...(isApiError(error) ? { code: error.errorCode } : {}),
    }),
  },
);

/** The backend's `error_code` for a registration the instance's registration mode refuses (#2132). */
export const REGISTRATION_NOT_ALLOWED = 'REGISTRATION_NOT_ALLOWED';

export const registerLocal = createAsyncThunk(
  'auth/registerLocal',
  async (data: { email: string; password: string; display_name: string; invitation_token?: string }) => {
    const profile = await authApi.register(data);
    return profile;
  },
  {
    // The backend's code travels as `code` (as for `loginLocal`, #2037), so the
    // register page can answer a refused registration in the user's language.
    serializeError: (error) => ({
      ...miniSerializeError(error),
      ...(isApiError(error) ? { code: error.errorCode } : {}),
    }),
  },
);

export const fetchProfile = createAsyncThunk('auth/fetchProfile', async () => {
  const profile = await authApi.getProfile();
  return profile;
});

/**
 * Sign out of this session (#2117).
 *
 * The device's push subscription is dropped first, on the server and in the
 * browser, because removing the server copy needs the access token this request
 * is about to end. The rest of the clean-up (every data slice, the active tenant)
 * belongs to the session end itself and runs on this thunk's `fulfilled` **and**
 * `rejected`: a logout request that fails (offline) still ends the session in
 * the tab — the user asked to leave, and the refresh cookie dies at its expiry.
 */
export const logoutUser = createAsyncThunk('auth/logout', async () => {
  // #2162 review S-2 — an invitation remembered across a sign-in belongs to the account that is
  // leaving; the next account signing in in this tab must not be taken to it.
  forgetPendingInvitation();
  await releasePushSubscription({ notifyServer: true });
  await authApi.logout();
});

/**
 * What a rate-limited refresh rejects *with* (#1131).
 *
 * A constant, not a literal at three call sites, because the three cannot be
 * allowed to drift: the thunk sets it, the reducer keeps the session on it, and
 * the 401 interceptor decides on it whether to sign the user out. `unwrap()`
 * throws the **payload** of a `rejectWithValue` rejection rather than the
 * original error, so the interceptor never sees an `AxiosError` here — the
 * first version of this fix checked for one and was therefore inert.
 */
export const RATE_LIMITED_REJECTION = 'rate-limited';

export const refreshAccessToken = createAsyncThunk(
  'auth/refresh',
  async (_: void, { rejectWithValue }) => {
    try {
      return await authApi.refresh();
    } catch (error) {
      // Carry *why* it failed, because the reducer's answer differs (#1131): a
      // 429 is a limit that expires within the minute and leaves the refresh
      // token valid, while a 401 means the credential is gone. Without this the
      // rejection is opaque and every failure looks like a dead session.
      if (isRateLimited(error)) return rejectWithValue(RATE_LIMITED_REJECTION);
      throw error;
    }
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

    // Logout — a failed request still signs the tab out (#2117, see `logoutUser`).
    const signedOut = (state: AuthState) => {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.initialized = true;
    };
    builder.addCase(logoutUser.fulfilled, signedOut);
    builder.addCase(logoutUser.rejected, signedOut);

    // Refresh
    builder.addCase(refreshAccessToken.fulfilled, (state, action) => {
      state.accessToken = action.payload.access_token;
      state.isAuthenticated = true;
      // JWT-mode bootstrap (AuthProvider.initAuth) begins with a token refresh.
      state.initialized = true;
    });
    builder.addCase(refreshAccessToken.rejected, (state, action) => {
      state.isLoading = false;
      state.initialized = true;
      // A rate limit is not a signed-out user (#1131). `/auth/refresh` has a
      // per-IP budget and `AuthProvider` calls it on every bootstrap and on
      // every 401 retry, so behind a shared address a burst of tabs can reach
      // it — dropping the session there would sign someone out over a limit
      // that expires within the minute, while their refresh token is still
      // valid. Every other rejection does mean the credential is gone.
      if (action.payload === RATE_LIMITED_REJECTION) return;
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
    });
  },
});

export const { clearError, setAccessToken, clearAuth } = authSlice.actions;
export default authSlice.reducer;
