import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import type { CareProfile } from '@/api/types';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import CareProfileForm from './CareProfileForm';

interface CareProfileEditDialogProps {
  open: boolean;
  onClose: () => void;
  /**
   * The profile to edit, or `null` while it loads. The host passes only a
   * profile that belongs to the plant it opened the dialog for (#3065): the
   * form seeds its fields from this object, so handing it another plant's
   * profile first and the right one later would show the wrong values and then
   * throw away whatever the user typed in between.
   */
  profile: CareProfile | null;
  /** Localised error key of a failed profile read; shown instead of the form. */
  error?: string | null;
  onRetry?: () => void;
  onUpdated: (profile: CareProfile) => void;
}

/**
 * Modal wrapper around {@link CareProfileForm}. Kept for the list-context callers
 * (care dashboard, task queue) where editing a profile from a row still reads
 * best as a dialog. The plant-instance Care tab renders {@link CareProfileForm}
 * inline instead (#577).
 */
export default function CareProfileEditDialog({
  open,
  onClose,
  profile,
  error = null,
  onRetry,
  onUpdated,
}: CareProfileEditDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();

  let body;
  if (profile) {
    body = (
      <CareProfileForm
        profile={profile}
        onUpdated={onUpdated}
        onDone={onClose}
        onCancel={onClose}
      />
    );
  } else if (error) {
    body = <ErrorDisplay error={error} onRetry={onRetry} />;
  } else {
    body = <LoadingSkeleton variant="form" />;
  }

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="care-profile-edit-dialog"
      aria-labelledby="care-profile-edit-dialog-title"
    >
      <DialogTitle id="care-profile-edit-dialog-title">
        {t('pages.pflege.editProfile')}
      </DialogTitle>
      <DialogContent>{body}</DialogContent>
      {/* The form brings its own actions; without it the dialog still needs a way out. */}
      {!profile && (
        <DialogActions>
          <Button onClick={onClose} data-testid="care-profile-edit-dialog-close">
            {t('common.cancel')}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
}
