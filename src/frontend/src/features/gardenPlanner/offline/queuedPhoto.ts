/**
 * A photo for the offline buffer (REQ-053 WP 9.4, UI-NFR-012 R-043/R-044, G-W9 g): downscaled on the device to at
 * most 1920 px on the longer edge and re-encoded as JPEG 80, so the buffer stays small. The canvas re-encode drops
 * EXIF already; the server strips it again on upload, as for every photo.
 */
import { normalizeImage } from '@/utils/imageNormalization';
import type { StoredPhoto } from './queueTypes';

/** R-044. */
export const QUEUED_PHOTO_MAX_EDGE = 1920;
export const QUEUED_PHOTO_JPEG_QUALITY = 0.8;

/** Downscale `file` for the buffer; the bytes go into IndexedDB. */
export async function photoForQueue(file: File): Promise<StoredPhoto> {
  const { file: scaled, previewUrl } = await normalizeImage(file, {
    maxEdge: QUEUED_PHOTO_MAX_EDGE,
    quality: QUEUED_PHOTO_JPEG_QUALITY,
  });
  URL.revokeObjectURL(previewUrl);
  return { bytes: await scaled.arrayBuffer(), type: scaled.type || 'image/jpeg', name: scaled.name };
}

/** The `File` a sync uploads, rebuilt from the stored bytes. */
export function photoFile(photo: StoredPhoto): File {
  return new File([photo.bytes], photo.name, { type: photo.type });
}
