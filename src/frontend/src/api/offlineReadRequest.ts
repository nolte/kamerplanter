/**
 * REQ-053 §32.6 Pkt. 13, SEC-001 (#2759): the three allowlisted reads (`GET …/sites`, `…/sites/{key}/plan`,
 * `…/locations/{key}/summary`) answer `Cache-Control: private, no-cache`. A plain request would let the browser's
 * HTTP disk cache store them, and no logout can empty that cache from script - the next user of a shared device
 * could read them with `fetch(url, { cache: 'force-cache' })`. This interceptor sends them through the fetch adapter
 * with the request cache mode `no-store` (`OFFLINE_READ_FETCH_OPTIONS`), whether or not a service worker controls
 * the page; XHR has no cache mode.
 */
import type { InternalAxiosRequestConfig } from 'axios';
import { isAllowlistedApiPath, OFFLINE_READ_FETCH_OPTIONS } from '@/pwa/cachePolicy';

/** The request path the server sees: base URL plus URL, without the query. */
function requestPath(config: InternalAxiosRequestConfig): string {
  const url = config.url ?? '';
  const full = /^[a-z]+:\/\//i.test(url) ? new URL(url).pathname : `${config.baseURL ?? ''}${url}`;
  return full.split('?')[0];
}

export function bypassHttpCacheForOfflineReads(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  if (!isAllowlistedApiPath(config.method ?? 'get', requestPath(config))) return config;
  config.adapter = 'fetch';
  config.fetchOptions = { ...config.fetchOptions, ...OFFLINE_READ_FETCH_OPTIONS };
  // The fetch adapter builds a `Request`, which needs an absolute URL (XHR resolves against the document itself).
  if (typeof window !== 'undefined' && config.baseURL?.startsWith('/')) {
    config.baseURL = new URL(config.baseURL, window.location.origin).href;
  }
  return config;
}
