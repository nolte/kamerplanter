import { useEffect } from 'react';
import {
  useForm,
  type Control,
  type FieldPath,
  type FieldValues,
  type UseFormProps,
  type UseFormReturn,
} from 'react-hook-form';

/** Validates the fields the user changed since their last blur check. */
type ValidateEnteredFields = () => void;

/**
 * The blur check of every live dialog form, keyed by its `control` — the one
 * handle {@link FormDialog} already receives. A `WeakMap`, so an unmounted form
 * leaves nothing behind.
 */
const enteredFieldValidators = new WeakMap<object, ValidateEnteredFields>();

/**
 * Validates the fields of the dialog form behind `control` that the user has
 * entered something in since their last check. `FormDialog` calls it whenever
 * focus leaves an element inside the dialog. A no-op for a form not created by
 * {@link useDialogForm}.
 */
export function validateEnteredFields<TFieldValues extends FieldValues, TTransformedValues>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- the form's context type is irrelevant here
  control: Control<TFieldValues, any, TTransformedValues>,
): void {
  enteredFieldValidators.get(control)?.();
}

/**
 * `useForm` with the dialog form defaults of UI-NFR-008 R-001 (#3019).
 *
 * Validation rule (operator decision 2026-11-19):
 * - Leaving a field validates it only when the user has entered something in
 *   it (typing and clearing it again counts). An untouched empty required
 *   field stays quiet until submit, so an autofocused name field does not grow
 *   a "required" line — and shift the dialog under the pointer — the moment
 *   the user clicks elsewhere.
 * - Submit validates every field (`mode: 'onSubmit'`).
 * - After a submit attempt every field re-validates on change
 *   (`reValidateMode: 'onChange'`), so fixing a field clears its error at once.
 *
 * Mechanism: the hook records which fields received user input (react-hook-form
 * emits `type: 'change'` only for input, not for `setValue`/`reset`). When focus
 * leaves an element inside the surrounding `FormDialog`, the dialog calls
 * {@link validateEnteredFields}, which `trigger`s exactly those fields and
 * forgets them. That covers every field of every dialog — shared `Form*Field`
 * components and hand-written `Controller`s alike — without touching them.
 *
 * A caller may still override `mode`/`reValidateMode`. Returns react-hook-form's
 * own object unchanged — no wrapper object, so its `formState` proxy stays the
 * live one.
 */
export function useDialogForm<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- mirrors useForm's own default
  TContext = any,
  TTransformedValues = TFieldValues,
>(
  props: UseFormProps<TFieldValues, TContext, TTransformedValues> = {},
): UseFormReturn<TFieldValues, TContext, TTransformedValues> {
  const form = useForm<TFieldValues, TContext, TTransformedValues>({
    mode: 'onSubmit',
    reValidateMode: 'onChange',
    ...props,
  });
  const { control, subscribe, trigger } = form;

  useEffect(() => {
    const entered = new Set<FieldPath<TFieldValues>>();
    const unsubscribe = subscribe({
      formState: { values: true },
      callback: ({ name, type }) => {
        if (name && type === 'change') entered.add(name as FieldPath<TFieldValues>);
      },
    });
    enteredFieldValidators.set(control, () => {
      if (entered.size === 0) return;
      const names = [...entered];
      entered.clear();
      void trigger(names);
    });
    return () => {
      unsubscribe();
      enteredFieldValidators.delete(control);
    };
  }, [control, subscribe, trigger]);

  return form;
}
