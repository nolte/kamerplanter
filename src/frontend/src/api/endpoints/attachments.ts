import { getActiveTenantSlug } from '../client';

/** Renditions the backend generates for every image attachment (NFR-013 §8.2). */
export type AttachmentRenditionSize = 128 | 512 | 1280;

/**
 * Build the authenticated URI of a tenant attachment, or of one of its renditions, from a bare attachment id.
 *
 * Diary entries, tasks and beds store bare attachment ids (`photo_refs`, `cover_photo_ref`), not URIs - a stored
 * URI carries the tenant slug, which a tenant rename re-derives (NFR-013 §2.2 / AC-09). A gallery photo arrives
 * with `uri` / `thumbnail_uris` already built by the server; this is the one place the frontend builds the same
 * shape itself. It mirrors `_base_uri()` in `app/api/v1/attachments/tenant_router.py`
 * (`/api/v1/t/{slug}/attachments/{id}[/thumbnails/{px}]`), with slug and id each encoded as one path segment.
 * Pass the result to {@link AuthImage}, which strips the `/api/v1` prefix again and sends the Bearer header a bare
 * `<img src>` could not. The URI names the tenant and the photo - never log it.
 */
export function attachmentUri(attachmentId: string, size?: AttachmentRenditionSize): string {
  const slug = encodeURIComponent(getActiveTenantSlug() ?? '');
  const uri = `/api/v1/t/${slug}/attachments/${encodeURIComponent(attachmentId)}`;
  return size ? `${uri}/thumbnails/${size}` : uri;
}
