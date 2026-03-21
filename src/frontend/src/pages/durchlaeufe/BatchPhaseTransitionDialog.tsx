import { useState, useEffect, useMemo } from 'react';
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
import CircularProgress from '@mui/material/CircularProgress';
import * as phasesApi from '@/api/endpoints/phases';
import * as runApi from '@/api/endpoints/plantingRuns';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { PlantingRunEntry, PlantInRun, GrowthPhase, BatchTransitionResponse } from '@/api/types';

interface Props {
  open: boolean;
  runKey: string;
  entries: PlantingRunEntry[];
  plants: PlantInRun[];
  onClose: () => void;
  onTransitioned: (result: BatchTransitionResponse) => void;
}

export default function BatchPhaseTransitionDialog({
  open,
  runKey,
  entries,
  plants,
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
  const [saving, setSaving] = useState(false);
  const [loadingPhases, setLoadingPhases] = useState(false);

  const speciesKeys = useMemo(
    () => [...new Set(entries.map((e) => e.species_key))],
    [entries],
  );

  // Determine dominant current phase
  const dominantPhase = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of plants) {
      if (!p.detached_at) {
        counts[p.current_phase] = (counts[p.current_phase] ?? 0) + 1;
      }
    }
    let max = 0;
    let dominant = '';
    for (const [phase, count] of Object.entries(counts)) {
      if (count > max) {
        max = count;
        dominant = phase;
      }
    }
    return dominant;
  }, [plants]);

  useEffect(() => {
    if (!open || speciesKeys.length === 0) return;
    setLoadingPhases(true);
    // Load lifecycle for the first species (most common case: monoculture)
    phasesApi
      .getLifecycleConfig(speciesKeys[0])
      .then((lc) => phasesApi.listGrowthPhases(lc.key))
      .then((allPhases) => {
        // Sort by sequence_order and filter to only phases after the current dominant
        const sorted = allPhases.sort((a, b) => a.sequence_order - b.sequence_order);
        const currentIdx = sorted.findIndex((p) => p.name === dominantPhase);
        const available = currentIdx >= 0 ? sorted.slice(currentIdx + 1) : sorted;
        setPhases(available);
      })
      .catch(() => setPhases([]))
      .finally(() => setLoadingPhases(false));
  }, [open, speciesKeys, dominantPhase]);

  const selectedPhase = phases.find((p) => p.key === targetPhaseKey);

  const eligibleCount = plants.filter(
    (p) => !p.detached_at && !p.removed_on,
  ).length;

  const handleTransition = async () => {
    if (!targetPhaseKey || !selectedPhase) return;
    try {
      setSaving(true);
      const result = await runApi.batchTransition(runKey, {
        target_phase_key: targetPhaseKey,
        target_phase_name: selectedPhase.name,
      });
      notification.success(
        t('pages.plantingRuns.batchTransitionSuccess', {
          count: result.transitioned_count,
          skipped: result.skipped_count,
          failed: result.failed_count,
        }),
      );
      onTransitioned(result);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="batch-phase-transition-dialog">
      <DialogTitle>{t('pages.plantingRuns.batchTransition')}</DialogTitle>
      <DialogContent>
        {loadingPhases ? (
          <CircularProgress sx={{ display: 'block', mx: 'auto', my: 2 }} />
        ) : (
          <>
            {speciesKeys.length > 1 && (
              <Alert severity="info" sx={{ mb: 2, mt: 1 }}>
                {t('pages.plantingRuns.mixedCultureWarning')}
              </Alert>
            )}
            <TextField
              select
              fullWidth
              label={t('pages.phases.targetPhase')}
              value={targetPhaseKey}
              onChange={(e) => setTargetPhaseKey(e.target.value)}
              sx={{ mb: 2, mt: 1 }}
              data-testid="batch-target-phase-select"
            >
              {phases.map((p) => (
                <MenuItem key={p.key} value={p.key}>
                  {p.display_name || p.name} ({p.typical_duration_days}d)
                </MenuItem>
              ))}
            </TextField>
            {selectedPhase && (
              <Alert severity="warning">
                {t('pages.plantingRuns.batchTransitionConfirm', {
                  count: eligibleCount,
                  phase: selectedPhase.display_name || selectedPhase.name,
                })}
              </Alert>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button
          variant="contained"
          onClick={handleTransition}
          disabled={!targetPhaseKey || saving}
          data-testid="batch-transition-confirm"
        >
          {saving ? <CircularProgress size={20} /> : t('common.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
