import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import { visuallyHidden } from '@mui/utils';
import { useTranslation } from 'react-i18next';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  destructive?: boolean;
  loading?: boolean;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
  destructive = false,
  loading = false,
}: ConfirmDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      // While the confirmed action is in flight, ignore backdrop/Escape close
      // attempts so the dialog cannot be dismissed mid-request (UI-NFR-004 R-020
      // / UI-NFR-008 double-submit protection extends to the whole interaction).
      onClose={loading ? undefined : onCancel}
      maxWidth="sm"
      fullWidth
      role="alertdialog"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      data-testid="confirm-dialog"
    >
      <DialogTitle id="confirm-dialog-title">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id="confirm-dialog-description" sx={{ whiteSpace: 'pre-line' }}>
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} autoFocus disabled={loading} data-testid="confirm-dialog-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          onClick={onConfirm}
          color={destructive ? 'error' : 'primary'}
          variant="contained"
          // MUI's native `loading` prop disables the button, renders an
          // accessible CircularProgress (labelled by the button's own text via
          // aria-labelledby) and keeps the label in the DOM (UI-NFR-002,
          // UI-NFR-008 R-016/R-017 double-submit protection + loading state).
          // Default (centered) loading position overlays the spinner on the
          // label, avoiding the width jump a "start" position causes without a
          // reserved startIcon.
          loading={loading}
          aria-busy={loading}
          data-testid="confirm-dialog-confirm"
        >
          {confirmLabel ?? t(destructive ? 'common.delete' : 'common.confirm')}
        </Button>
      </DialogActions>
      {/* UI-NFR-002 R-011: politely announce the pending state for screen-reader
          users even if focus was moved away when the confirm button became
          disabled (native `disabled` blurs the element). */}
      <Box aria-live="polite" sx={visuallyHidden} data-testid="confirm-dialog-live-region">
        {loading ? t('common.processing') : ''}
      </Box>
    </Dialog>
  );
}
