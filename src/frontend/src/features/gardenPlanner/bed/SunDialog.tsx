/**
 * Change the sun and shade class of one bed from the bed view (REQ-053 GP-FR-157, GP-API-010): the
 * tiles of the plan editor in a dialog, stored with `PATCH /locations/{key}`. The editor stores the
 * same field through the plan batch; here a bed that is not on the plan can be classified too.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import type { SunExposure } from '../model/types';
import { patchSunExposure } from './bedApi';
import SunTileSelector from './SunTileSelector';

interface SunDialogProps {
  bedKey: string;
  bedName: string;
  current: SunExposure;
  onClose: () => void;
  /** The class was stored; the page reloads its summary. */
  onChanged: () => void;
}

export default function SunDialog({ bedKey, bedName, current, onClose, onChanged }: SunDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const [chosen, setChosen] = useState<SunExposure>(current);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (chosen === current) {
      onClose();
      return;
    }
    setSaving(true);
    try {
      await patchSunExposure(bedKey, chosen);
      notification.success(t('pages.gardenPlan.sun.dialog.saved'));
      onChanged();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      aria-labelledby="bed-sun-title"
      data-testid="bed-sun-dialog"
    >
      <DialogTitle id="bed-sun-title">{t('pages.gardenPlan.sun.dialog.title', { bed: bedName })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.gardenPlan.sun.hint')}
        </Typography>
        <SunTileSelector value={chosen} onChange={setChosen} disabled={saving} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('pages.gardenPlan.sun.dialog.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          loading={saving}
          data-testid="bed-sun-submit"
        >
          {t('pages.gardenPlan.sun.dialog.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
