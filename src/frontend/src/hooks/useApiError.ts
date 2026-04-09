import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { isApiError, getFieldErrors, parseApiError } from '@/api/errors';
import { useNotification } from './useNotification';

export function useApiError() {
  const { t } = useTranslation();
  const notification = useNotification();

  const handleError = useCallback(
    (error: unknown, setFieldError?: (name: string, message: string) => void) => {
      // 1. Structured API errors (backend returned our error envelope)
      if (isApiError(error)) {
        // Map field errors to form
        if (setFieldError) {
          const fieldErrors = getFieldErrors(error);
          for (const [field, message] of Object.entries(fieldErrors)) {
            setFieldError(field, message);
          }
          if (Object.keys(fieldErrors).length > 0) {
            notification.error(t('errors.validation'));
            return;
          }
        }

        // Map error codes to i18n messages
        switch (error.errorCode) {
          case 'ENTITY_NOT_FOUND':
            notification.error(t('errors.notFound'));
            break;
          case 'DUPLICATE_ENTRY':
            notification.error(t('errors.duplicate'));
            break;
          case 'VALIDATION_ERROR': {
            const vDetail = sanitizeDetail(error.message);
            notification.error(
              vDetail
                ? t('errors.validationWithDetail', { detail: vDetail })
                : t('errors.validation'),
            );
          }
            break;
          case 'INTERNAL_ERROR':
            notification.error(t('errors.server'));
            break;
          default:
            // Use status code for unmapped error codes
            switch (error.statusCode) {
              case 403:
                notification.error(t('errors.forbidden'));
                break;
              case 409:
                notification.error(t('errors.conflict'));
                break;
              case 413:
                notification.error(t('errors.tooLarge'));
                break;
              default:
                notification.error(parseApiError(error));
            }
        }
        return;
      }

      // 2. Axios errors without structured body (e.g. 500 without JSON, CORS, timeout)
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_CANCELED') {
          notification.error(t('errors.networkTimeout'));
          return;
        }
        if (error.response) {
          // Server responded but not with our error envelope
          const status = error.response.status;
          if (status === 403) {
            notification.error(t('errors.forbidden'));
          } else if (status === 404) {
            notification.error(t('errors.notFound'));
          } else if (status === 409) {
            notification.error(t('errors.conflict'));
          } else if (status === 413) {
            notification.error(t('errors.tooLarge'));
          } else if (status === 422) {
            const rawDetail = extractDetail(error.response.data);
            const cleanDetail = sanitizeDetail(rawDetail);
            notification.error(
              cleanDetail
                ? t('errors.validationWithDetail', { detail: cleanDetail })
                : t('errors.validation'),
            );
          } else if (status >= 500) {
            notification.error(t('errors.server'));
          } else {
            notification.error(t('errors.unknown'));
          }
          return;
        }
        // No response at all — true network error
        notification.error(t('errors.network'));
        return;
      }

      // 3. Plain Error with "Network Error" message (legacy axios pattern)
      if (error instanceof Error && error.message === 'Network Error') {
        notification.error(t('errors.network'));
        return;
      }

      notification.error(t('errors.unknown'));
    },
    [t, notification],
  );

  return { handleError };
}

/** Extract a human-readable detail string from an unstructured error response body. */
function extractDetail(data: unknown): string | null {
  if (typeof data === 'string' && data.length > 0 && data.length < 200) {
    return data;
  }
  if (typeof data === 'object' && data !== null) {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === 'string') return obj.detail;
    if (typeof obj.message === 'string') return obj.message;
  }
  return null;
}

/** Known English backend error patterns that should not be shown as raw detail text. */
const ENGLISH_DETAIL_PATTERN = /^(The .+ is invalid\.|.+ not found\.|An internal error occurred)/i;

/** Return the detail only if it is not a raw English backend message. */
function sanitizeDetail(detail: string | undefined | null): string | null {
  if (!detail) return null;
  if (ENGLISH_DETAIL_PATTERN.test(detail)) return null;
  return detail;
}
