import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import * as phasesApi from '@/api/endpoints/phases';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { GrowthPhase, PlantInstance } from '@/api/types';

interface Props {
  plantKey: string;
  lifecycleKey: string | null;
  open: boolean;
  onClose: () => void;
  onTransitioned: (plant: PlantInstance) => void;
}

export default function PhaseTransitionDialog({
  plantKey,
  lifecycleKey,
  open,
  onClose,
  onTransitioned,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [phases, setPhases] = useState<GrowthPhase[]>([]);
  const [targetPhaseKey, setTargetPhaseKey] = useState('');
  const [reason, setReason] = useState('manual');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && lifecycleKey) {
      phasesApi.listGrowthPhases(lifecycleKey).then(setPhases).catch(() => {});
    }
  }, [open, lifecycleKey]);

  const handleTransition = async () => {
    if (!targetPhaseKey) return;
    try {
      setSaving(true);
      const plant = await phasesApi.transitionPhase(plantKey, {
        target_phase_key: targetPhaseKey,
        reason,
      });
      notification.success(t('pages.phases.transition'));
      onTransitioned(plant);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="phase-transition-dialog">
      <DialogTitle>{t('pages.phases.transition')}</DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t('common.unsavedChanges')}
        </Alert>
        <TextField
          select
          fullWidth
          label={t('pages.phases.targetPhase')}
          value={targetPhaseKey}
          onChange={(e) => setTargetPhaseKey(e.target.value)}
          sx={{ mb: 2, mt: 1 }}
          data-testid="target-phase-select"
        >
          {phases.map((p) => (
            <MenuItem key={p.key} value={p.key}>
              {p.display_name || p.name} ({p.typical_duration_days}d)
            </MenuItem>
          ))}
        </TextField>
        <TextField
          fullWidth
          label={t('pages.phases.reason')}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          data-testid="transition-reason"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} data-testid="transition-cancel">{t('common.cancel')}</Button>
        <Button
          variant="contained"
          onClick={handleTransition}
          disabled={!targetPhaseKey || saving}
          data-testid="transition-confirm"
        >
          {t('common.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
