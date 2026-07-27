import Box from '@mui/material/Box';
import type { BoxProps } from '@mui/material/Box';
import type { ReactNode } from 'react';

/**
 * Props accepted by {@link Form}.
 *
 * `component` and `noValidate` are deliberately removed from the surface: the
 * former is what makes this a form at all, the latter is the invariant the
 * component exists to enforce (see the component docs).
 */
export interface FormProps extends Omit<BoxProps<'form'>, 'component' | 'noValidate'> {
  children: ReactNode;
}

/**
 * The form element every React-Hook-Form form in this app renders.
 *
 * Its whole job is that `noValidate` is not a decision a call site gets to
 * make. Without it the browser runs its own constraint validation on submit,
 * and a single empty `required` field aborts the submission *before* the
 * `submit` event fires. The consequences are not cosmetic:
 *
 * 1. `handleSubmit` never runs, so **zod never runs** — every cross-field and
 *    business rule in the schema is silently skipped.
 * 2. No `helperText` renders, so the field-level messages we wrote and
 *    translated never appear.
 * 3. The user gets a transient native bubble instead, in the *browser's* UI
 *    locale rather than the app's — a German app can show an English bubble.
 *
 * Our field components (`FormTextField`, `FormNumberField`, …) forward
 * `required` straight to the MUI input, where it lands on the DOM node as the
 * native attribute — so any form built from them is exposed by default.
 *
 * `noValidate` is applied *after* the prop spread, so it cannot be overridden
 * from the outside. That is intentional: issue #825 exists because the correct
 * behaviour was opt-in, and 55 of 84 form-bearing files had not opted in.
 *
 * ## Testing note — jsdom cannot see this
 *
 * jsdom does not implement native constraint validation, so a behavioural test
 * ("submit an empty required field, expect the zod message") passes with *and*
 * without `noValidate`. A test written that way looks like it guards this and
 * does not — see #822, which threw such a test away rather than ship a check
 * that cannot fail. The defences that do work are the ESLint rule in
 * `eslint.config.js` (which rejects a raw form element) and E2E coverage in a
 * real browser.
 *
 * @example
 * ```tsx
 * <Form onSubmit={handleSubmit(onSubmit)}>
 *   <FormTextField name="common_name" control={control} label={…} required />
 *   <FormActions onCancel={onClose} loading={saving} />
 * </Form>
 * ```
 */
export default function Form({ children, ...rest }: FormProps) {
  return (
    <Box component="form" {...rest} noValidate>
      {children}
    </Box>
  );
}
