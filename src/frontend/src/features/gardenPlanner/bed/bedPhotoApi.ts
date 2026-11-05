import { getActiveTenantSlug, tenantClient } from '@/api/client';

/**
 * REST access to the photos of a bed (REQ-053 GP-FR-051) through the tenant-scoped client. A photo is a tenant
 * attachment of category `location` (EXIF/GPS stripped on upload); it is uploaded first through `POST /attachments`
 * and then linked to the bed with `POST /locations/{key}/photos`. The first photo linked becomes the cover.
 *
 * URIs are built and handed to `AuthImage` only - they are never logged (the URI names the tenant and the photo).
 */

const LOCATIONS = '/locations';

/** The attachment category of a bed photo. */
const BED_PHOTO_CATEGORY = 'location';

/** One photo of a bed, newest first in the gallery. */
export interface BedPhoto {
  attachment_id: string;
  uri: string;
  thumbnail_uris?: { small: string; medium: string; large: string } | null;
  mime_type?: string;
  byte_size?: number;
  caption?: string | null;
  taken_on?: string | null;
  created_at?: string | null;
  is_cover: boolean;
  /** The caller may remove it: an own upload from `grower`, any photo as `lead`. */
  can_remove: boolean;
}

/** `GET|POST /locations/{key}/photos` and the cover/remove routes answer with the whole gallery. */
export interface BedPhotoGallery {
  location_key: string;
  cover_photo_ref: string | null;
  photos: BedPhoto[];
  /** At most this many photos per bed (50). */
  max_photos: number;
}

/** Renditions the backend generates for every image (NFR-013 §8.2). */
type BedPhotoSize = 128 | 512 | 1280;

/**
 * The authenticated URI of a bed photo rendition, for a bare attachment id such as the bed's `cover_photo_ref`.
 * Mirrors the route the gallery answers with (`/api/v1/t/{slug}/attachments/{id}/thumbnails/{px}`).
 */
export function bedPhotoUri(attachmentId: string, size: BedPhotoSize): string {
  const slug = getActiveTenantSlug() ?? '';
  return `/api/v1/t/${slug}/attachments/${attachmentId}/thumbnails/${size}`;
}

/** The bed's photos, newest first, with the cover marked and `can_remove` for the caller. */
export async function listBedPhotos(key: string): Promise<BedPhotoGallery> {
  const { data } = await tenantClient.get<BedPhotoGallery>(`${LOCATIONS}/${key}/photos`);
  return data;
}

/**
 * Upload a photo and link it to the bed. Two requests: the upload (category `location`), then the link; a 422
 * `location.photo_limit_reached` at 50 photos comes from the link.
 */
export async function addBedPhoto(key: string, file: File): Promise<BedPhotoGallery> {
  const form = new FormData();
  form.append('file', file);
  form.append('category', BED_PHOTO_CATEGORY);
  const uploaded = await tenantClient.post<{ attachment_id: string }>('/attachments', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  const { data } = await tenantClient.post<BedPhotoGallery>(`${LOCATIONS}/${key}/photos`, {
    attachment_id: uploaded.data.attachment_id,
  });
  return data;
}

/** Choose the cover from the bed's photos, or clear it with `null`. */
export async function setBedCoverPhoto(key: string, attachmentId: string | null): Promise<BedPhotoGallery> {
  const { data } = await tenantClient.put<BedPhotoGallery>(`${LOCATIONS}/${key}/photos/cover`, {
    attachment_id: attachmentId,
  });
  return data;
}

/** Remove a photo from the bed; the server deletes the file unless something else still names it. */
export async function removeBedPhoto(key: string, attachmentId: string): Promise<BedPhotoGallery> {
  const { data } = await tenantClient.delete<BedPhotoGallery>(`${LOCATIONS}/${key}/photos/${attachmentId}`);
  return data;
}
