import { tenantClient } from '@/api/client';
import type { PlanUnderlay } from '../model/types';

/**
 * REST access to the background picture of a plan (REQ-053 GP-FR-033, GP-API-002 family) through the tenant client.
 * The picture is an attachment of category `garden_plan_underlay` (NFR-013: size limit, magic bytes, EXIF/GPS strip);
 * it is uploaded first and then named by the calibration that `PUT /plan/underlay` stores on the site.
 */

export const UNDERLAY_CATEGORY = 'garden_plan_underlay';

interface UploadedAttachment {
  attachment_id: string;
}

/** Upload the picture and return the attachment key the calibration names. */
export async function uploadUnderlayImage(file: File): Promise<string> {
  const form = new FormData();
  form.append('file', file);
  form.append('category', UNDERLAY_CATEGORY);
  const { data } = await tenantClient.post<UploadedAttachment>('/attachments', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data.attachment_id;
}

export async function putUnderlay(siteKey: string, body: PlanUnderlay): Promise<PlanUnderlay> {
  const { data } = await tenantClient.put<PlanUnderlay>(`/sites/${siteKey}/plan/underlay`, body);
  return data;
}

export async function deleteUnderlay(siteKey: string): Promise<void> {
  await tenantClient.delete(`/sites/${siteKey}/plan/underlay`);
}

/** The stored picture as a blob: a bare `<img>` cannot carry the bearer token, and `blob:` is in the CSP's `img-src`. */
export async function fetchUnderlayBlob(attachmentKey: string, signal?: AbortSignal): Promise<Blob> {
  const { data } = await tenantClient.get<Blob>(`/attachments/${attachmentKey}`, {
    responseType: 'blob',
    signal,
  });
  return data;
}
