import { useCallback, useMemo, useRef, useState, type FocusEvent } from 'react';
import Dialog, { type DialogProps } from '@mui/material/Dialog';
import { useTranslation } from 'react-i18next';
import { useFormState, type Control, type FieldValues } from 'react-hook-form';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { validateEnteredFields } from '@/hooks/useDialogForm';
import { FormDialogContext, type FormDialogContextValue } from './formDialogContext';

export interface FormDialogProps<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues>
  extends Omit<DialogProps, 'onClose'> {
  /** The dialog form's `control`; its `isDirty` decides whether closing asks first. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- the form's context type is irrelevant here
  control: Control<TFieldValues, any, TTransformedValues>;
  /**
   * Closes the dialog. Called directly when the form is clean, after the
   * discard confirmation when it is dirty. Leave it `undefined` to make the
   * dialog undismissable (e.g. while a request is in flight).
   */
  onClose?: () => void;
  /** Unsaved input the form state does not see (local `useState` sections); OR-ed with `isDirty`. */
  dirty?: boolean;
}

/**
 * The dialog every create/edit form renders in (UI-NFR-008, #3019).
 *
 * A thin `Dialog` that owns the close path: backdrop click, Escape and the
 * cancel button of a `FormActions` inside it close straight away while the form
 * is clean, and ask "discard changes?" first when it is dirty. A successful
 * submit closes through the caller (`onCreated`/`onSaved`) and is not guarded.
 *
 * It also runs the blur check of `useDialogForm`: whenever focus leaves an
 * element inside the dialog, the fields the user entered something in since
 * their last check are validated — an untouched empty field stays quiet until
 * submit (UI-NFR-008 R-001, operator decision 2026-11-19).
 *
 * Pair it with `useDialogForm` and `useFormFieldViolations` (422 → field
 * errors) — the three together are the dialog form contract.
 */
export default function FormDialog<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues>({
  control,
  onClose,
  dirty = false,
  children,
  onBlur,
  ...dialogProps
}: FormDialogProps<TFieldValues, TTransformedValues>) {
  const { t } = useTranslation();
  const { isDirty } = useFormState({ control });
  const guarded = isDirty || dirty;
  const [confirmOpen, setConfirmOpen] = useState(false);
  const pendingClose = useRef<(() => void) | null>(null);

  const requestClose = useCallback(
    (close: () => void) => {
      if (!guarded) {
        close();
        return;
      }
      pendingClose.current = close;
      setConfirmOpen(true);
    },
    [guarded],
  );

  const handleDialogClose = useCallback(() => {
    if (onClose) requestClose(onClose);
  }, [onClose, requestClose]);

  const handleDiscard = useCallback(() => {
    setConfirmOpen(false);
    const close = pendingClose.current;
    pendingClose.current = null;
    close?.();
  }, []);

  const handleKeep = useCallback(() => {
    pendingClose.current = null;
    setConfirmOpen(false);
  }, []);

  // React's `onBlur` bubbles (focusout), also out of portals such as a Select menu.
  const handleBlur = useCallback(
    (event: FocusEvent<HTMLDivElement>) => {
      onBlur?.(event);
      validateEnteredFields(control);
    },
    [control, onBlur],
  );

  const contextValue = useMemo<FormDialogContextValue>(() => ({ requestClose }), [requestClose]);

  return (
    <FormDialogContext.Provider value={contextValue}>
      <Dialog {...dialogProps} onBlur={handleBlur} onClose={onClose ? handleDialogClose : undefined}>
        {children}
      </Dialog>
      <ConfirmDialog
        open={confirmOpen}
        title={t('common.discardChangesTitle')}
        message={t('common.discardChangesMessage')}
        confirmLabel={t('common.discardChangesConfirm')}
        destructive
        onConfirm={handleDiscard}
        onCancel={handleKeep}
      />
    </FormDialogContext.Provider>
  );
}
