/**
 * "Transplant to …" (REQ-053 GP-FR-069): moving a plant into another bed is not a drag but the existing
 * `transplant` task (REQ-006). The grower names the target bed; the task carries it in its text and
 * hangs off the plant.
 */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { listBeds } from '../bed/bedApi';
import type { BedListItem } from '../bed/types';
import { createTransplantTask } from './plantingApi';

interface TransplantDialogProps {
  siteKey: string;
  bedKey: string;
  plantKey: string;
  plantLabel: string;
  onClose: () => void;
  onCreated: (targetName: string) => void;
}

export default function TransplantDialog({
  siteKey,
  bedKey,
  plantKey,
  plantLabel,
  onClose,
  onCreated,
}: TransplantDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const [beds, setBeds] = useState<BedListItem[] | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [target, setTarget] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listBeds(siteKey)
      .then((items) => {
        if (!cancelled) setBeds(items.filter((item) => item.key !== bedKey && item.bed_status !== 'retired'));
      })
      .catch(() => {
        if (!cancelled) setLoadFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [siteKey, bedKey]);

  const submit = async () => {
    const chosen = beds?.find((bed) => bed.key === target);
    if (!chosen) return;
    setSaving(true);
    try {
      await createTransplantTask({
        plantKey,
        name: t('pages.bed.planting.transplant.taskName', { plant: plantLabel, bed: chosen.name }),
        instruction: t('pages.bed.planting.transplant.taskInstruction', { plant: plantLabel, bed: chosen.name }),
      });
      onCreated(chosen.name);
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
      maxWidth="xs"
      fullWidth
      aria-labelledby="transplant-dialog-title"
      data-testid="transplant-dialog"
    >
      <DialogTitle id="transplant-dialog-title">{t('pages.bed.planting.transplant.title', { plant: plantLabel })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.bed.planting.transplant.help')}
        </Typography>
        {loadFailed ? <Alert severity="error">{t('pages.bed.planting.transplant.failed')}</Alert> : null}
        {beds !== null && beds.length === 0 ? (
          <Alert severity="info">{t('pages.bed.planting.transplant.noBeds')}</Alert>
        ) : null}
        {beds !== null && beds.length > 0 ? (
          <TextField
            select
            autoFocus
            label={t('pages.bed.planting.transplant.target')}
            value={target}
            onChange={(event) => setTarget(event.target.value)}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            slotProps={{ htmlInput: { 'data-testid': 'transplant-target' } }}
          >
            {beds.map((bed) => (
              <MenuItem key={bed.key} value={bed.key}>
                {bed.name}
              </MenuItem>
            ))}
          </TextField>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving || target === ''}
          sx={{ minHeight: 48 }}
          data-testid="transplant-submit"
        >
          {t('pages.bed.planting.transplant.create')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
