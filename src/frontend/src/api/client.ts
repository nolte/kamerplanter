import axios from 'axios';
import { ApiError } from './errors';
import type { ApiErrorResponse } from './types';
import { isLightMode } from '@/config/mode';

const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';
const LIGHT_MODE_SLUG = 'mein-garten';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const data = error.response.data as ApiErrorResponse;
      if (data?.error_id && data?.error_code) {
        throw new ApiError(data, error.response.status);
      }
    }
    throw error;
  },
);

/**
 * Axios client for tenant-scoped API endpoints.
 * Automatically prepends /t/{tenant_slug} to all request URLs
 * using the active tenant slug from localStorage.
 */
const tenantClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

tenantClient.interceptors.request.use((config) => {
  let slug: string | null = null;
  if (isLightMode) {
    slug = LIGHT_MODE_SLUG;
  } else {
    try {
      slug = window.localStorage.getItem(ACTIVE_TENANT_KEY);
    } catch {
      // localStorage unavailable (e.g. SSR)
    }
  }
  if (slug && config.url && !config.url.startsWith('/t/')) {
    config.url = `/t/${slug}${config.url}`;
  }
  return config;
});

tenantClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const data = error.response.data as ApiErrorResponse;
      if (data?.error_id && data?.error_code) {
        throw new ApiError(data, error.response.status);
      }
    }
    throw error;
  },
);

export { tenantClient };
export default client;
