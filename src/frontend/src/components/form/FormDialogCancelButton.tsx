import Button, { type ButtonProps } from '@mui/material/Button';
import { useTranslation } from 'react-i18next';
import { useFormDialogClose } from './formDialogContext';

interface FormDialogCancelButtonProps extends Omit<ButtonProps, 'onClick'> {
  onCancel: () => void;
}

/**
 * The cancel button of a `FormDialog` that lays out its own `DialogActions`
 * instead of using `FormActions` (#3019). Goes through the dialog's dirty
 * guard like `FormActions` does; outside a `FormDialog` it calls `onCancel`.
 */
export default function FormDialogCancelButton({ onCancel, children, ...props }: FormDialogCancelButtonProps) {
  const { t } = useTranslation();
  const formDialog = useFormDialogClose();
  return (
    <Button data-testid="form-cancel-button" {...props} onClick={() => (formDialog ? formDialog.requestClose(onCancel) : onCancel())}>
      {children ?? t('common.cancel')}
    </Button>
  );
}
