import { lazy, Suspense, useContext, useId, type ComponentProps } from 'react';
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
import { KioskContext } from '@/kiosk/KioskProvider';
import { loadLongPressButton } from '@/kiosk/kioskChunks';
// Type only: the button itself stays in its lazy chunk.
import type HoldButton from '@/components/kiosk/LongPressButton';

/**
 * The plain confirm button, standing in for the hold button while its chunk loads and for good if
 * it cannot load (offline before the kiosk shell could preload it). A destructive dialog never
 * shows Cancel alone; and this dialog IS the two-step confirmation R-030 accepts on its own.
 */
function PlainConfirmButton({
  onConfirm,
  loading,
  disabled,
  children,
  'data-testid': testId,
}: ComponentProps<typeof HoldButton>) {
  return (
    <Button
      onClick={onConfirm}
      color="error"
      variant="contained"
      loading={loading}
      disabled={disabled}
      aria-busy={loading}
      data-testid={testId}
    >
      {children}
    </Button>
  );
}

// UI-NFR-019 R-030 — only a kiosk session holds a destructive confirmation; its own chunk.
const LongPressButton = lazy(() =>
  loadLongPressButton().catch(() => ({ default: PlainConfirmButton })),
);

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
  // Generated, not the fixed `confirm-dialog-title`: a confirmation can open on
  // top of another one (the discard prompt over a form dialog), and two
  // elements with the same id leave one dialog named after the other's title
  // (#3024). The `data-testid`s stay fixed — they are the E2E contract.
  const titleId = useId();
  const descriptionId = useId();
  // UI-NFR-019 R-030/R-031 — in kiosk mode a destructive confirmation is HELD (a phantom touch on a
  // wet screen taps, it does not hold for two seconds), and Cancel and Confirm sit ≥ 32 px apart.
  // Keyboard and assistive activation still confirm directly; see LongPressButton.
  const isKiosk = useContext(KioskContext)?.isKiosk ?? false;
  const holdToConfirm = destructive && isKiosk;

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
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      data-testid="confirm-dialog"
    >
      <DialogTitle id={titleId}>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id={descriptionId} sx={{ whiteSpace: 'pre-line' }}>
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions
        sx={holdToConfirm ? { gap: 4, alignItems: 'flex-start', '& > :not(style) ~ :not(style)': { ml: 0 } } : undefined}
      >
        <Button onClick={onCancel} autoFocus disabled={loading} data-testid="confirm-dialog-cancel">
          {t('common.cancel')}
        </Button>
        {holdToConfirm ? (
          <Suspense
            fallback={
              <PlainConfirmButton onConfirm={onConfirm} disabled data-testid="confirm-dialog-confirm">
                {confirmLabel ?? t('common.delete')}
              </PlainConfirmButton>
            }
          >
            <LongPressButton
              onConfirm={onConfirm}
              loading={loading}
              // The hold stops the moment the dialog starts closing (its exit transition).
              disabled={!open}
              data-testid="confirm-dialog-confirm"
            >
              {confirmLabel ?? t('common.delete')}
            </LongPressButton>
          </Suspense>
        ) : (
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
        )}
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
