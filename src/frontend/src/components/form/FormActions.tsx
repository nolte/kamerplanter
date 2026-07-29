import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
import { useStickyBarScrollPadding } from '@/hooks/useStickyBarScrollPadding';

interface FormActionsProps {
  onCancel: () => void;
  loading?: boolean;
  saveLabel?: string;
  disabled?: boolean;
}

export default function FormActions({
  onCancel,
  loading = false,
  saveLabel,
  disabled = false,
}: FormActionsProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // Below `sm` every dialog in this app renders `fullScreen`, and this row is
  // the last child of a scrolling `DialogContent` — on a long form (the task
  // create dialog, the plant instance dialog) the primary action then sits
  // ~900px below the fold, with nothing on screen indicating the form can be
  // submitted at all. Pinning the row to the bottom of its scroll container
  // keeps "Speichern"/"Abbrechen" reachable without restructuring ~40 dialogs
  // into `DialogActions`, and does the same for long in-page edit forms.
  const isPinned = useMediaQuery(theme.breakpoints.down('sm'));
  // Issue #768 — a pinned bar floats over the bottom band of its own scroll
  // container, so a field the browser scrolls to that edge (Tab, an anchor,
  // WebDriver's click preparation) ends up behind it. The hook reserves the
  // band on whichever ancestor scrolls, measured from this row's real height,
  // and stays inert on wider viewports where the row is not pinned.
  const stickyBarRef = useStickyBarScrollPadding(isPinned, Number.parseFloat(theme.spacing(1)));

  return (
    <Box
      ref={stickyBarRef}
      data-testid="form-actions"
      sx={{
        display: 'flex',
        gap: 2,
        mt: 3,
        ...(isPinned
          ? {
              position: 'sticky',
              bottom: 0,
              zIndex: 1,
              py: 1.5,
              bgcolor: 'background.paper',
              borderTop: '1px solid',
              borderColor: 'divider',
            }
          : {}),
      }}
    >
      <Button variant="outlined" onClick={onCancel} disabled={loading} data-testid="form-cancel-button">
        {t('common.cancel')}
      </Button>
      <Button
        type="submit"
        variant="contained"
        disabled={loading || disabled}
        startIcon={loading ? <CircularProgress size={16} /> : undefined}
        data-testid="form-submit-button"
      >
        {saveLabel ?? t('common.save')}
      </Button>
    </Box>
  );
}
