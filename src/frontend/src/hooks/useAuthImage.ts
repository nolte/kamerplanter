import { useEffect, useMemo, useRef, useState } from 'react';
import client from '@/api/client';

/** Lifecycle state of an authenticated image fetch. */
export type AuthImageStatus = 'loading' | 'loaded' | 'error';

interface UseAuthImageResult {
  /** Object-URL for the fetched blob while `status === 'loaded'`, otherwise `null`. */
  objectUrl: string | null;
  status: AuthImageStatus;
}

/**
 * Strips the shared `/api/v1` prefix from a backend-issued attachment URI so the
 * remaining path (`/t/{slug}/attachments/...`) can be requested through the plain
 * {@link client} (whose `baseURL` is already `/api/v1`).
 *
 * The plain client is deliberately chosen over `tenantClient`: it carries the
 * Bearer-token request interceptor and the 401 auto-refresh response interceptor
 * (both installed in `AuthProvider`), but — unlike `tenantClient` — it does NOT
 * prepend `/t/{slug}`. Because the backend URI already contains the tenant
 * segment, routing it through `tenantClient` would double the prefix
 * (`/api/v1/t/{slug}/t/{slug}/...`). Routing the de-prefixed path through the
 * plain client yields exactly `/api/v1` + `/t/{slug}/...` again, with auth set.
 *
 * URIs that are already relative to `/api/v1` (i.e. start with `/t/`) are passed
 * through unchanged; anything else is returned as-is so absolute/external URLs
 * still work.
 */
function toClientRelativeUrl(uri: string): string {
  const API_PREFIX = '/api/v1';
  if (uri.startsWith(`${API_PREFIX}/`)) {
    return uri.slice(API_PREFIX.length);
  }
  return uri;
}

/**
 * Loads a permission-gated attachment URI as an authenticated blob and exposes it
 * as an Object-URL suitable for an `<img src>`.
 *
 * Native `<img>` elements cannot carry the axios Bearer header, so directly
 * pointing them at a `require_attachment_permission(READ)`-gated endpoint yields a
 * 401/403 and a broken image. This hook fetches the bytes through the
 * authenticated axios client instead (`responseType: 'blob'`, mirroring
 * `api/endpoints/print.ts`) and hands back a stable Object-URL.
 *
 * The Object-URL is revoked whenever the source URI changes and on unmount, so no
 * blob references leak. A `null` / empty `uri` short-circuits to the `loading`
 * status without issuing a request (callers render their own placeholder).
 *
 * @param uri - Full backend attachment URI (e.g. `/api/v1/t/{slug}/attachments/{id}/thumbnails/512`).
 */
export function useAuthImage(uri: string | null | undefined): UseAuthImageResult {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthImageStatus>('loading');
  // Track the active Object-URL across renders so the cleanup always revokes the
  // exact URL it created, even if `setObjectUrl` has not yet flushed.
  const activeUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!uri) {
      setStatus('loading');
      setObjectUrl(null);
      return;
    }

    let cancelled = false;
    setStatus('loading');

    const requestUrl = toClientRelativeUrl(uri);
    client
      .get<Blob>(requestUrl, { responseType: 'blob' })
      .then((response) => {
        if (cancelled) return;
        const url = URL.createObjectURL(response.data);
        activeUrlRef.current = url;
        setObjectUrl(url);
        setStatus('loaded');
      })
      .catch(() => {
        if (cancelled) return;
        setObjectUrl(null);
        setStatus('error');
      });

    return () => {
      cancelled = true;
      if (activeUrlRef.current) {
        URL.revokeObjectURL(activeUrlRef.current);
        activeUrlRef.current = null;
      }
    };
  }, [uri]);

  // Primitive `status` is exempt from the useMemo obligation, but the returned
  // object is a reference type and must be stabilised (FRONTEND.md hook rules).
  return useMemo(() => ({ objectUrl, status }), [objectUrl, status]);
}
