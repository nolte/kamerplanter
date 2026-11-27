import { useState, useEffect, useCallback } from 'react';
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
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import RequiresConnectivity from '@/components/common/RequiresConnectivity';
import { useApiError } from '@/hooks/useApiError';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';
import OptionsLoadError from '@/components/common/OptionsLoadError';
import { captureHandledError } from '@/observability/errorTracking';
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
  const [targetPhaseKey, setTargetPhaseKey] = useState('');
  const [reason, setReason] = useState('manual');
  const [force, setForce] = useState(false);
  const [saving, setSaving] = useState(false);
  // UI-NFR-012 R-020a/R-020e: the server validates every transition (order, allowed edges, cycle restarts).
  const online = useOnlineStatus();

  useEffect(() => {
    if (!open) return;
    setTargetPhaseKey('');
    setReason('manual');
    setForce(false);
  }, [open]);

  // #3013 (A-02): the target phases are the only input of this dialog. A failed load used to
  // leave the select empty without a word, so a phase change was silently impossible; it now
  // renders an error with retry.
  const loadPhases = useCallback(async (): Promise<GrowthPhase[]> => {
    // Try the species' PhaseSequence first, fall back to the lifecycle's legacy GrowthPhases.
    if (speciesKey) {
      let sequenceError: unknown = null;
      try {
        const sequence = await phaseSequenceApi.getSpeciesPhaseSequence(speciesKey);
        if (sequence && sequence.entries.length > 0) return sequence.entries.map(growthPhaseFromEntry);
      } catch (err) {
        // Not fatal while the legacy phases can stand in; reported so it is not invisible.
        captureHandledError(err, { source: 'PhaseTransitionDialog.phaseSequence' });
        sequenceError = err;
      }
      if (!lifecycleKey && sequenceError !== null) throw sequenceError;
    }
    return lifecycleKey ? phasesApi.listGrowthPhases(lifecycleKey) : [];
  }, [speciesKey, lifecycleKey]);
  const phasesLoad = useAsyncOptions(loadPhases, { enabled: open });
  const phases = phasesLoad.options;

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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth aria-labelledby="phase-transition-dialog-title" data-testid="phase-transition-dialog">
      <DialogTitle id="phase-transition-dialog-title">{t('pages.phases.transition')}</DialogTitle>
      <DialogContent>
        {phasesLoad.error && (
          <OptionsLoadError
            onRetry={phasesLoad.reload}
            messageKey="pages.phases.targetPhasesLoadFailed"
            data-testid="target-phases-load-error"
          />
        )}
        {!phasesLoad.error && !phasesLoad.loading && open && phases.length === 0 && (
          <Alert severity="info" sx={{ mt: 1 }} data-testid="target-phases-empty">
            {t('pages.phases.noTargetPhases')}
          </Alert>
        )}
        <TextField
          select
          fullWidth
          disabled={phasesLoad.loading || phasesLoad.error}
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
        <RequiresConnectivity offline={!online}>
          <Button
            variant="contained"
            onClick={handleTransition}
            disabled={!targetPhaseKey || saving}
            color={force ? 'warning' : 'primary'}
            data-testid="transition-confirm"
          >
            {force ? t('pages.phases.forceTransition') : t('common.confirm')}
          </Button>
        </RequiresConnectivity>
      </DialogActions>
    </Dialog>
  );
}
