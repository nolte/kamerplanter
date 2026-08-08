import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { FieldPath, FieldValues, UseFormSetError } from 'react-hook-form';
import type { FieldViolation } from '@/api/errors';
import type { FieldViolationHandler } from './useApiError';

export interface FieldViolationConfig {
  /**
   * Stable violation `code` → i18n key. A code absent from this map is left to
   * the generic validation toast; the backend's English `reason` is never
   * rendered onto the German form (#1015). Reference codes come from the backend
   * domain validators (e.g. `WINTER_PATH_VIOLATION`, `DUPLICATE_ENTRY`).
   */
  messageKeys: Record<string, string>;
  /**
   * Server field name → form field name, for the rare field the form edits under
   * a different name (e.g. `slot_keys` → `slot_keys_input`). Identity mapping
   * when a field is absent.
   */
  fieldMap?: Record<string, string>;
}

/**
 * Build the translate-or-skip handler that {@link useApiError.handleError} hands
 * each field-scoped 422 violation.
 *
 * Generalises the guard PR #1014 wrote inline in `WateringLogCreateDialog`:
 * render a field error only when the violation's stable `code` has a translation,
 * otherwise leave the field untouched so the generic validation toast remains the
 * floor. The handler returns `true` when it set an error, which tells
 * `handleError` a field message is already on screen.
 *
 * `config.messageKeys` / `config.fieldMap` MUST be referentially stable
 * (module-level constants) so the returned handler stays stable across renders —
 * the `useCallback`/`useMemo` obligation of FRONTEND.md §6.1.
 */
export function useFieldViolations<TFieldValues extends FieldValues = FieldValues>(
  setError: UseFormSetError<TFieldValues>,
  config: FieldViolationConfig,
): FieldViolationHandler {
  const { t } = useTranslation();
  const { messageKeys, fieldMap } = config;
  return useCallback(
    (violation: FieldViolation): boolean => {
      const messageKey = messageKeys[violation.code];
      if (!messageKey) return false;
      // The server names the field with a plain string; react-hook-form types it
      // as `FieldPath<TFieldValues>`. A field the form does not own simply has no
      // error surface and renders nothing, so the cast cannot mislead the user.
      const field = (fieldMap?.[violation.field] ??
        violation.field) as FieldPath<TFieldValues>;
      setError(field, { type: violation.code, message: t(messageKey) });
      return true;
    },
    [setError, t, messageKeys, fieldMap],
  );
}
