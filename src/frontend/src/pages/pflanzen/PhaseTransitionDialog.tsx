import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import * as phasesApi from '@/api/endpoints/phases';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { growthPhaseFromEntry } from '@/utils/phaseSequenceMapper';
import type { GrowthPhase, PlantInstance } from '@/api/types';

interface Props {
  plantKey: string;
  speciesKey?: string | null;
  lifecycleKey: string | null;
  open: boolean;
  onClose: () => void;
  onTransitioned: (plant: PlantInstance) => void;
}

export default function PhaseTransitionDialog({
  plantKey,
  speciesKey,
  lifecycleKey,
  open,
  onClose,
  onTransitioned,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [phases, setPhases] = useState<GrowthPhase[]>([]);
  const [targetPhaseKey, setTargetPhaseKey] = useState('');
  const [reason, setReason] = useState('manual');
  const [force, setForce] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTargetPhaseKey('');
    setReason('manual');
    setForce(false);

    // Try PhaseSequence first, fall back to legacy GrowthPhases
    if (speciesKey) {
      phaseSequenceApi
        .getSpeciesPhaseSequence(speciesKey)
        .catch(() => null)
        .then((sequence) => {
          if (sequence && sequence.entries.length > 0) {
            setPhases(sequence.entries.map(growthPhaseFromEntry));
            return;
          }
          // Fallback to legacy
          if (lifecycleKey) {
            phasesApi.listGrowthPhases(lifecycleKey).then(setPhases).catch(() => {});
          }
        });
    } else if (lifecycleKey) {
      phasesApi.listGrowthPhases(lifecycleKey).then(setPhases).catch(() => {});
    }
  }, [open, speciesKey, lifecycleKey]);

  const handleTransition = async () => {
    if (!targetPhaseKey) return;
    try {
      setSaving(true);
      const plant = await phasesApi.transitionPhase(plantKey, {
        target_phase_key: targetPhaseKey,
        reason: force ? (reason || 'correction') : reason,
        force,
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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="phase-transition-dialog">
      <DialogTitle>{t('pages.phases.transition')}</DialogTitle>
      <DialogContent>
        <TextField
          select
          fullWidth
          label={t('pages.phases.targetPhase')}
          value={targetPhaseKey}
          onChange={(e) => setTargetPhaseKey(e.target.value)}
          sx={{ mb: 2, mt: 1 }}
          data-testid="target-phase-select"
          helperText={t('pages.phases.targetPhaseHelper')}
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
          sx={{ mb: 2 }}
          helperText={t('pages.phases.reasonHelper')}
          data-testid="transition-reason"
        />
        <FormControlLabel
          control={
            <Switch
              checked={force}
              onChange={(e) => {
                setForce(e.target.checked);
                if (e.target.checked) setReason('correction');
                else setReason('manual');
              }}
              data-testid="force-transition-switch"
            />
          }
          label={t('pages.phases.forceCorrection')}
          sx={{ mb: 1, mt: 1 }}
        />
        {force && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {t('pages.phases.forceCorrectionHint')}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} data-testid="transition-cancel">{t('common.cancel')}</Button>
        <Button
          variant="contained"
          onClick={handleTransition}
          disabled={!targetPhaseKey || saving}
          color={force ? 'warning' : 'primary'}
          data-testid="transition-confirm"
        >
          {force ? t('pages.phases.forceTransition') : t('common.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
