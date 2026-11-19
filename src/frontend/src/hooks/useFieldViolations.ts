import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Control, FieldPath, FieldValues, UseFormSetError } from 'react-hook-form';
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

/**
 * Pydantic `type` codes of the backend's 422 envelope (`details[].code`) → the
 * generic field message (#3019). The envelope carries no constraint values
 * (`min_length`, `gt`, ...), so the texts are the parameterless ones.
 */
const DEFAULT_VIOLATION_MESSAGE_KEYS: Readonly<Record<string, string>> = {
  missing: 'validation.required',
  enum: 'validation.invalidOption',
  literal_error: 'validation.invalidOption',
  url_parsing: 'validation.url',
  url_type: 'validation.url',
  url_scheme: 'validation.url',
  string_pattern_mismatch: 'validation.invalidFormat',
  date_parsing: 'validation.invalidFormat',
  date_from_datetime_parsing: 'validation.invalidFormat',
  datetime_parsing: 'validation.invalidFormat',
  datetime_from_date_parsing: 'validation.invalidFormat',
  time_parsing: 'validation.invalidFormat',
  uuid_parsing: 'validation.invalidFormat',
};

/** The message for a violation whose code has no translation of its own. */
const FALLBACK_VIOLATION_MESSAGE_KEY = 'validation.invalid';

/**
 * The 422 → form-field mapping every dialog form uses (UI-NFR-008 R-004, #3019).
 *
 * Unlike {@link useFieldViolations} it does not skip an unknown code: a
 * violation on a field **the form renders** always marks that field — with the
 * translation of its `code` (`config.messageKeys` first, then
 * {@link DEFAULT_VIOLATION_MESSAGE_KEYS}) or the generic "invalid input" text.
 * The backend's English `reason` is never shown. A violation on a field the
 * form does not render (a server-only field, a nested path the form edits
 * under another name without `fieldMap`) is left to the toast of
 * `useApiError().handleError`, so no violation disappears silently.
 *
 * The first mapped field receives focus. `config` MUST be referentially stable
 * (a module-level constant).
 */
export function useFormFieldViolations<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- the form's context type is irrelevant here
  control: Control<TFieldValues, any, TTransformedValues>,
  config?: Partial<FieldViolationConfig>,
): FieldViolationHandler {
  const { t } = useTranslation();
  const messageKeys = config?.messageKeys;
  const fieldMap = config?.fieldMap;
  return useCallback(
    (violation: FieldViolation): boolean => {
      const field = fieldMap?.[violation.field] ?? violation.field;
      // `_names.mount` holds every field a Controller/`register` has mounted —
      // the fields the user can actually see an error on.
      if (!control._names.mount.has(field)) return false;
      const messageKey =
        messageKeys?.[violation.code] ??
        DEFAULT_VIOLATION_MESSAGE_KEYS[violation.code] ??
        FALLBACK_VIOLATION_MESSAGE_KEY;
      const shouldFocus = !Object.keys(control._formState.errors).length;
      control.setError(
        field as FieldPath<TFieldValues>,
        { type: violation.code, message: t(messageKey) },
        { shouldFocus },
      );
      return true;
    },
    [control, t, messageKeys, fieldMap],
  );
}
