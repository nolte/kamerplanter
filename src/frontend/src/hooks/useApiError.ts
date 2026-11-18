import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { errorKey, errorKeyForCode, getFieldViolations, isApiError, type FieldViolation } from '@/api/errors';
import { useNotification } from './useNotification';

/**
 * Caller-supplied handler for one field-scoped 422 violation, carrying the full
 * `{ field, reason, code }` — the `code` above all (#1015).
 *
 * The hook forwards each violation here instead of writing the backend's
 * `reason` onto the form itself: `reason` is English (NFR-003) and belongs in a
 * German form no more than a stack trace does. A caller translates on the stable
 * `code` and renders its own message, returning `true`; for a `code` it cannot
 * translate it returns falsy and leaves the field alone, so the generic toast
 * below remains the floor rather than English text becoming the ceiling.
 *
 * {@link useFieldViolations} builds this handler from a `code → i18n key` map,
 * which is the path every caller should take rather than re-deriving the guard.
 */
export type FieldViolationHandler = (violation: FieldViolation) => boolean | void;

export function useApiError() {
  const { t } = useTranslation();
  const notification = useNotification();

  const handleError = useCallback(
    (error: unknown, applyFieldViolation?: FieldViolationHandler) => {
      // Forward each field-scoped violation to the caller (side effect only).
      // This must NOT swallow the error-code-specific message below: a coded
      // error such as DUPLICATE_ENTRY carries a `details[].field` too (e.g. the
      // conflicting `batch_id`), yet the user still needs its specific
      // "already exists" toast — not a generic "check your input" (issue #744).
      // `mappedFieldError` tracks only violations the caller actually rendered,
      // so an untranslatable code that the caller skipped still falls through to
      // the coded/generic toast rather than being silently absorbed (#1015).
      let mappedFieldError = false;
      if (isApiError(error) && applyFieldViolation) {
        for (const violation of getFieldViolations(error)) {
          if (applyFieldViolation(violation)) {
            mappedFieldError = true;
          }
        }
      }

      // FRONTEND.md §10.3 (#3013): the stable `error_code` decides the text, the
      // backend's English `message` never reaches the toast. A violation the form
      // already shows pairs with the generic "check your input" unless the code
      // itself has a more specific translation (DUPLICATE_ENTRY, a quota, ...).
      const specific = isApiError(error) ? errorKeyForCode(error.errorCode) : null;
      const key =
        mappedFieldError && (specific === null || specific === 'errors.validation')
          ? 'errors.validation'
          : errorKey(error, 'errors.unknown');
      notification.error(t(key));
    },
    [t, notification],
  );

  // FRONTEND.md §6.1: object return MUST be useMemo-stabilised.
  return useMemo(() => ({ handleError }), [handleError]);
}
