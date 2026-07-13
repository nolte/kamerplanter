import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import type { CareProfile } from '@/api/types';
import CareProfileForm from './CareProfileForm';

interface CareProfileEditDialogProps {
  open: boolean;
  onClose: () => void;
  profile: CareProfile;
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
  onUpdated,
}: CareProfileEditDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();

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
      <DialogContent>
        <CareProfileForm
          profile={profile}
          onUpdated={onUpdated}
          onDone={onClose}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
