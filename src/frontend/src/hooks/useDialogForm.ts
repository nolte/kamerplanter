import { useForm, type FieldValues, type UseFormProps, type UseFormReturn } from 'react-hook-form';

/**
 * `useForm` with the dialog form defaults of UI-NFR-008 R-001 (#3019).
 *
 * Validates a field when it loses focus (`mode: 'onBlur'`) instead of only on
 * submit, and re-validates on change once it has an error (the react-hook-form
 * default `reValidateMode`). A caller may still override `mode`.
 *
 * Returns react-hook-form's own object unchanged — no wrapper object, so its
 * `formState` proxy stays the live one.
 */
export function useDialogForm<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- mirrors useForm's own default
  TContext = any,
  TTransformedValues = TFieldValues,
>(
  props: UseFormProps<TFieldValues, TContext, TTransformedValues> = {},
): UseFormReturn<TFieldValues, TContext, TTransformedValues> {
  return useForm<TFieldValues, TContext, TTransformedValues>({ mode: 'onBlur', ...props });
}
