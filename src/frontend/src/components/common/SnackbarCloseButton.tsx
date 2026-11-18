import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import { useSnackbar, type SnackbarKey } from 'notistack';
import { useTranslation } from 'react-i18next';

interface SnackbarCloseButtonProps {
  snackbarKey: SnackbarKey;
}

/**
 * Close action of every snackbar (UI-NFR-004 R-004/R-007, #3013 N-10).
 *
 * A real `<button>` with an accessible name, so a toast can be dismissed by
 * keyboard (Tab + Enter/Space) instead of only waiting for its timeout. Wired as
 * the `SnackbarProvider`'s default `action` in `App.tsx`; a snackbar that brings
 * its own action (the undo offer) renders this next to it.
 */
export default function SnackbarCloseButton({ snackbarKey }: SnackbarCloseButtonProps) {
  const { t } = useTranslation();
  const { closeSnackbar } = useSnackbar();
  return (
    <IconButton
      size="small"
      color="inherit"
      aria-label={t('common.close')}
      onClick={() => closeSnackbar(snackbarKey)}
      sx={{ minHeight: 44, minWidth: 44 }}
      data-testid="snackbar-close"
    >
      <CloseIcon fontSize="small" />
    </IconButton>
  );
}
