import { useEffect, useCallback, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchProfile,
  refreshAccessToken,
  clearAuth,
  setAccessToken,
} from '@/store/slices/authSlice';
import { loadMyTenants } from '@/store/slices/tenantSlice';
import { fetchPreferences } from '@/store/slices/userPreferencesSlice';
import { isLightMode } from '@/config/mode';
import client from '@/api/client';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

interface QueueItem {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const dispatch = useAppDispatch();
  const accessToken = useAppSelector((s) => s.auth.accessToken);
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const tokenRef = useRef(accessToken);

  // Keep ref in sync with state
  useEffect(() => {
    tokenRef.current = accessToken;
  }, [accessToken]);

  // Request interceptor: attach Bearer token (skip in light mode)
  useEffect(() => {
    if (isLightMode) return;

    const requestInterceptor = client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (tokenRef.current && config.headers) {
          config.headers.Authorization = `Bearer ${tokenRef.current}`;
        }
        return config;
      },
    );

    return () => {
      client.interceptors.request.eject(requestInterceptor);
    };
  }, []);

  // Response interceptor: auto-refresh on 401 (skip in light mode)
  useEffect(() => {
    if (isLightMode) return;

    const responseInterceptor = client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;
        if (!originalRequest) throw error;

        // Don't retry auth endpoints
        const url = originalRequest.url || '';
        if (
          error.response?.status !== 401 ||
          url.includes('/auth/login') ||
          url.includes('/auth/refresh') ||
          url.includes('/auth/register')
        ) {
          throw error;
        }

        if (isRefreshing) {
          return new Promise<string>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return client(originalRequest);
          });
        }

        isRefreshing = true;

        try {
          const result = await dispatch(refreshAccessToken()).unwrap();
          const newToken = result.access_token;
          dispatch(setAccessToken(newToken));
          processQueue(null, newToken);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          dispatch(clearAuth());
          throw refreshError;
        } finally {
          isRefreshing = false;
        }
      },
    );

    return () => {
      client.interceptors.response.eject(responseInterceptor);
    };
  }, [dispatch]);

  // On mount: try to refresh and load profile + preferences
  const initAuth = useCallback(async () => {
    const AUTH_TIMEOUT_MS = 10_000;
    const timeout = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Auth init timeout')), AUTH_TIMEOUT_MS),
    );

    const doInit = async () => {
      if (isLightMode) {
        // Light mode: skip JWT refresh, just fetch profile directly
        try {
          await dispatch(fetchProfile()).unwrap();
          dispatch(loadMyTenants());
          dispatch(fetchPreferences());
        } catch {
          // System user should always exist in light mode
        }
        return;
      }

      try {
        const result = await dispatch(refreshAccessToken()).unwrap();
        dispatch(setAccessToken(result.access_token));
        await dispatch(fetchProfile());
        dispatch(loadMyTenants());
        dispatch(fetchPreferences());
      } catch {
        // Not authenticated — that's fine
      }
    };

    try {
      await Promise.race([doInit(), timeout]);
    } catch {
      // Timeout or error — clear auth state so UI exits loading
      dispatch(clearAuth());
    }
  }, [dispatch]);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // Fetch profile, tenants and preferences after login
  useEffect(() => {
    if (isAuthenticated && !isRefreshing) {
      dispatch(fetchProfile());
      dispatch(loadMyTenants());
      dispatch(fetchPreferences());
    }
  }, [isAuthenticated, dispatch]);

  return <>{children}</>;
}
