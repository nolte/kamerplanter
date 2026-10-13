import { useEffect } from 'react';
import { useAppDispatch } from '@/store/hooks';
import { resetShowAllFields } from '@/store/slices/uiSlice';

/**
 * Scopes the global "show all fields" override to the dialog that set it (#1900).
 *
 * The override is one Redux flag read by every expertise-gated form. A dialog
 * that exposes `ShowAllFieldsToggle` must hand it back however it closes -- a
 * successful create closes through the parent (`onCreated` -> `setOpen(false)`)
 * and never reaches the dialog's own cancel handler. Resetting on the `open`
 * transition (and on unmount, for parents that conditionally render the dialog)
 * covers every exit path.
 */
export function useResetShowAllFieldsOnClose(open: boolean): void {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!open) {
      dispatch(resetShowAllFields());
    }
  }, [open, dispatch]);

  useEffect(
    () => () => {
      dispatch(resetShowAllFields());
    },
    [dispatch],
  );
}
