import { createContext, useContext } from 'react';

/**
 * What a {@link FormDialog} hands the controls rendered inside it (#3019).
 *
 * Kept in a module of its own so that `FormActions` — which page forms import
 * eagerly — can read the context without pulling the dialog and its confirm
 * prompt into the initial bundle.
 */
export interface FormDialogContextValue {
  /**
   * Run `close` now when the form is clean, or after the user confirmed that
   * the unsaved input may be discarded (UI-NFR-008).
   */
  requestClose: (close: () => void) => void;
}

export const FormDialogContext = createContext<FormDialogContextValue | null>(null);

/** The surrounding {@link FormDialog}'s close guard, or `null` outside one. */
export function useFormDialogClose(): FormDialogContextValue | null {
  return useContext(FormDialogContext);
}
