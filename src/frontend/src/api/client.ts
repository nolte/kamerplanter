import axios from 'axios';
import { ApiError } from './errors';
import type { ApiErrorResponse } from './types';
import { isLightMode } from '@/config/mode';

const LIGHT_MODE_SLUG = 'mein-garten';

/**
 * Active tenant slug, kept in sync by tenantSlice.
 * This avoids reading a stale value from localStorage before
 * loadMyTenants has validated the persisted slug.
 */
let _activeTenantSlug: string | null = null;

export function setActiveTenantSlug(slug: string | null) {
  _activeTenantSlug = slug;
}

export function getActiveTenantSlug(): string | null {
  return _activeTenantSlug;
}

/**
 * Shared response-interceptor rejection handler: converts a backend error
 * envelope ({ error_id, error_code, ... }) into a typed {@link ApiError} and
 * re-throws everything else unchanged. Used by both `client` and `tenantClient`
 * so the envelope-detection logic lives in exactly one place.
 */
function rethrowApiError(error: unknown): never {
  if (axios.isAxiosError(error) && error.response) {
    const data = error.response.data as ApiErrorResponse;
    if (data?.error_id && data?.error_code) {
      throw new ApiError(data, error.response.status);
    }
  }
  throw error;
}

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use((response) => response, rethrowApiError);

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
  const slug = isLightMode ? LIGHT_MODE_SLUG : _activeTenantSlug;
  if (slug && config.url && !config.url.startsWith('/t/')) {
    config.url = `/t/${slug}${config.url}`;
  }
  return config;
});

tenantClient.interceptors.response.use((response) => response, rethrowApiError);

export { tenantClient };
export default client;
