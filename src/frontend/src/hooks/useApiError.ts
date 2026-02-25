import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { isApiError, getFieldErrors, parseApiError } from '@/api/errors';
import { useNotification } from './useNotification';

export function useApiError() {
  const { t } = useTranslation();
  const notification = useNotification();

  const handleError = useCallback(
    (error: unknown, setFieldError?: (name: string, message: string) => void) => {
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
          case 'VALIDATION_ERROR':
            notification.error(t('errors.validation'));
            break;
          case 'INTERNAL_ERROR':
            notification.error(t('errors.server'));
            break;
          default:
            notification.error(parseApiError(error));
        }
      } else if (error instanceof Error && error.message === 'Network Error') {
        notification.error(t('errors.network'));
      } else {
        notification.error(t('errors.unknown'));
      }
    },
    [t, notification],
  );

  return { handleError };
}
