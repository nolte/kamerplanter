import type { TFunction } from 'i18next';
import { isApiError } from '@/api/errors';

/** The error code the link answers with when the bed already holds `max_photos` photos. */
const PHOTO_LIMIT_REACHED = 'location.photo_limit_reached';

/** The largest number of photos a bed holds (`max_photos` of the gallery, `MAX_PHOTOS_PER_LOCATION`). */
export const BED_PHOTO_LIMIT = 50;

/**
 * The message for a failed bed-photo upload or link, or `null` for the upload dialog's generic ones (file too
 * large, connection). Named here: the photo limit of the bed, the storage quota of the garden and a missing
 * write right - each worded for a bed, not for a plant.
 */
export function bedPhotoUploadError(t: TFunction, error: unknown): string | null {
  if (!isApiError(error)) return null;
  if (error.errorCode === PHOTO_LIMIT_REACHED) return t('pages.bed.photos.limitReached', { max: BED_PHOTO_LIMIT });
  if (error.errorCode === 'PHOTO_QUOTA_EXCEEDED' || error.statusCode === 409) return t('pages.bed.photos.quotaExceeded');
  if (error.statusCode === 403) return t('pages.bed.photos.uploadForbidden');
  return null;
}
