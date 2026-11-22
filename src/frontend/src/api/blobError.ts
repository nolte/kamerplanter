import axios from 'axios';
import { ApiError } from './errors';
import type { ApiErrorResponse } from './types';

/**
 * Read a blob-typed error body back as the API's error envelope.
 *
 * With `responseType: 'blob'` the error body arrives as a `Blob`, so the client's interceptor cannot
 * recognise the envelope and rethrows the raw Axios error; without this a download that is refused
 * (an expired archive, a CSV over the row limit) would show "Request failed with status code 4xx".
 */
export async function rethrowBlobError(error: unknown): Promise<never> {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    let parsed: Partial<ApiErrorResponse> | null;
    try {
      parsed = JSON.parse(await error.response.data.text()) as Partial<ApiErrorResponse>;
    } catch {
      parsed = null;
    }
    if (parsed?.error_id && parsed.error_code) {
      throw new ApiError(parsed as ApiErrorResponse, error.response.status);
    }
  }
  throw error;
}
