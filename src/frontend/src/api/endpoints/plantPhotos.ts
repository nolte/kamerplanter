import { tenantClient } from '../client';

/**
 * REQ-034 §7 — plant-instance photo gallery API layer.
 *
 * All endpoints are tenant-scoped and run through {@link tenantClient}, which
 * prepends `/t/{slug}` automatically. The frontend never sees a bucket, region
 * or storage backend — only the opaque `attachment_id` and the stable,
 * tenant-scoped URIs the backend returns (REQ-034 AC-03/AC-04, NFR-013 §2.4).
 */

const base = (plantInstanceKey: string) =>
  `/plant-instances/${plantInstanceKey}/photos`;

/** Thumbnail renditions: small=128px, medium=512px, large=1280px (NFR-013 §8.2). */
export interface PlantPhotoThumbnailUris {
  small: string;
  medium: string;
  large: string;
}

/** A single gallery photo (REQ-034 §7). */
export interface PlantPhoto {
  attachment_id: string;
  /** Stable download URI for the original object. */
  uri: string;
  /** Thumbnail URIs; `null` while renditions are still generating. */
  thumbnail_uris: PlantPhotoThumbnailUris | null;
  is_cover: boolean;
  mime_type: string;
  byte_size: number;
  /**
   * User-editable caption (max 500 chars), or `null` (REQ-034 §2.1 v1.2).
   */
  caption: string | null;
  /**
   * User-editable capture date (`YYYY-MM-DD`), or `null`. When `null`, the UI
   * falls back to {@link created_at} for display (`taken_on ?? created_at`).
   */
  taken_on: string | null;
  created_at: string | null;
}

/**
 * PATCH body for a gallery photo's editable metadata (REQ-034 §2.1 v1.2).
 *
 * True PATCH: only the keys present on the object are sent and changed server
 * side. Send an explicit `null` to clear a field; omit a key to leave it
 * untouched.
 */
export interface PlantPhotoMetadataUpdate {
  caption?: string | null;
  taken_on?: string | null;
}

/** The gallery listing: ordered photos (newest first) plus the resolved cover. */
export interface PlantPhotoList {
  plant_instance_key: string;
  /** Resolved cover attachment id (explicit cover or first photo), or `null`. */
  cover_photo_ref: string | null;
  photos: PlantPhoto[];
}

/** GET — list a plant instance's gallery photos, newest first. */
export async function listPlantPhotos(
  plantInstanceKey: string,
): Promise<PlantPhotoList> {
  const { data } = await tenantClient.get<PlantPhotoList>(base(plantInstanceKey));
  return data;
}

/**
 * POST — upload a gallery photo (multipart `file`) and link it to the instance.
 *
 * The per-instance quota is enforced server-side *before* any bytes are written;
 * an exceeded quota surfaces as a 409 (`PHOTO_QUOTA_EXCEEDED`) for the caller.
 */
export async function uploadPlantPhoto(
  plantInstanceKey: string,
  file: File,
): Promise<PlantPhoto> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await tenantClient.post<PlantPhoto>(
    base(plantInstanceKey),
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data;
}

/** PUT — mark a gallery photo as the instance cover; returns the updated list. */
export async function setCoverPhoto(
  plantInstanceKey: string,
  attachmentId: string,
): Promise<PlantPhotoList> {
  const { data } = await tenantClient.put<PlantPhotoList>(
    `${base(plantInstanceKey)}/${attachmentId}/cover`,
  );
  return data;
}

/**
 * PATCH — update a gallery photo's caption / capture date (REQ-034 §2.1 v1.2).
 *
 * Only the keys present in `update` are sent (true PATCH); the server leaves
 * omitted fields untouched and clears a field on an explicit `null`. Returns
 * the updated photo (with the recomputed `is_cover` flag).
 */
export async function updatePhotoMetadata(
  plantInstanceKey: string,
  attachmentId: string,
  update: PlantPhotoMetadataUpdate,
): Promise<PlantPhoto> {
  const { data } = await tenantClient.patch<PlantPhoto>(
    `${base(plantInstanceKey)}/${attachmentId}`,
    update,
  );
  return data;
}

/** DELETE — hard-delete a gallery photo and unlink it (204 No Content). */
export async function deletePlantPhoto(
  plantInstanceKey: string,
  attachmentId: string,
): Promise<void> {
  await tenantClient.delete(`${base(plantInstanceKey)}/${attachmentId}`);
}
