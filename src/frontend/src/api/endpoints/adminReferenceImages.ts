import client from '../client';
import type {
  CurationImageList,
  SetImageActiveRequest,
  SetImageActiveResponse,
} from '../types';

const BASE = '/admin/reference-images';

/**
 * List ALL reference images for a species (including deselected ones) for the
 * admin curation view. Platform-admin only — returns 403 otherwise.
 */
export async function getReferenceImageCuration(speciesKey: string): Promise<CurationImageList> {
  const { data } = await client.get<CurationImageList>(`${BASE}/${speciesKey}/images`);
  return data;
}

/**
 * Deselect (``is_active: false``) or re-include (``true``) one reference image.
 * Deselected images are kept for the audit trail but filtered out of recognition.
 */
export async function setReferenceImageActive(
  speciesKey: string,
  imageId: number,
  payload: SetImageActiveRequest,
): Promise<SetImageActiveResponse> {
  const { data } = await client.patch<SetImageActiveResponse>(
    `${BASE}/${speciesKey}/images/${imageId}`,
    payload,
  );
  return data;
}
