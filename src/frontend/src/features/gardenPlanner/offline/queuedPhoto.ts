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

/**
 * The file name a buffered photo is stored and sent under: generic, never the original (an original name such as
 * `IMG_20261108_Garten_Mueller.jpg` can carry a date, a place or a person).
 */
export const QUEUED_PHOTO_NAME = 'photo.jpg';

/** Downscale `file` for the buffer; the bytes go into IndexedDB. */
export async function photoForQueue(file: File): Promise<StoredPhoto> {
  const { file: scaled, previewUrl } = await normalizeImage(file, {
    maxEdge: QUEUED_PHOTO_MAX_EDGE,
    quality: QUEUED_PHOTO_JPEG_QUALITY,
  });
  URL.revokeObjectURL(previewUrl);
  return { bytes: await scaled.arrayBuffer(), type: scaled.type || 'image/jpeg', name: QUEUED_PHOTO_NAME };
}

/**
 * The bytes an online attempt already sent (its answer got lost): kept unchanged so the resend is a replay. The
 * upload dialog's canvas encode has already dropped EXIF; the server strips again.
 */
export async function photoAsSent(file: File): Promise<StoredPhoto> {
  return { bytes: await file.arrayBuffer(), type: file.type || 'image/jpeg', name: QUEUED_PHOTO_NAME };
}

/** The dialog's file under the generic name — what field mode sends online, so a buffered copy matches it. */
export function withGenericName(file: File): File {
  return new File([file], QUEUED_PHOTO_NAME, { type: file.type || 'image/jpeg' });
}

/** The `File` a sync uploads, rebuilt from the stored bytes. */
export function photoFile(photo: StoredPhoto): File {
  return new File([photo.bytes], photo.name, { type: photo.type });
}
