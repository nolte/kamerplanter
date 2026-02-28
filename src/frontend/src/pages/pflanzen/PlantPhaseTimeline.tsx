import { useEffect, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import * as phasesApi from '@/api/endpoints/phases';
import type { PlantInstance, GrowthPhase, PhaseHistoryEntry, PhaseTimelineEntry } from '@/api/types';

interface Props {
  plant: PlantInstance;
  history: PhaseHistoryEntry[];
}

function formatDate(iso: string | null): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString();
}

function StepIcon({ status }: { status: PhaseTimelineEntry['status'] }) {
  if (status === 'completed') return <CheckCircleIcon color="success" />;
  if (status === 'current') return <RadioButtonCheckedIcon color="primary" />;
  return <RadioButtonUncheckedIcon color="disabled" />;
}

function buildTimeline(
  growthPhases: GrowthPhase[],
  history: PhaseHistoryEntry[],
  plant: PlantInstance,
): PhaseTimelineEntry[] {
  const sorted = [...growthPhases].sort((a, b) => a.sequence_order - b.sequence_order);
  const historyByPhase: Record<string, PhaseHistoryEntry> = {};
  for (const h of history) {
    historyByPhase[h.phase_name] = h;
  }

  const entries: PhaseTimelineEntry[] = [];
  let lastEnd: string | null = null;

  for (const gp of sorted) {
    const h = historyByPhase[gp.name];
    if (h && h.exited_at) {
      // Completed
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        sequence_order: gp.sequence_order,
        typical_duration_days: gp.typical_duration_days,
        status: 'completed',
        actual_entered_at: h.entered_at,
        actual_exited_at: h.exited_at,
        actual_duration_days: h.actual_duration_days,
        projected_start: null,
        projected_end: null,
      });
      lastEnd = h.exited_at;
    } else if (gp.name === plant.current_phase) {
      // Current
      const entered = h?.entered_at ?? plant.current_phase_started_at;
      const projEnd = entered
        ? new Date(new Date(entered).getTime() + gp.typical_duration_days * 86400000).toISOString()
        : null;
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        sequence_order: gp.sequence_order,
        typical_duration_days: gp.typical_duration_days,
        status: 'current',
        actual_entered_at: entered,
        actual_exited_at: null,
        actual_duration_days: null,
        projected_start: null,
        projected_end: projEnd,
      });
      lastEnd = projEnd;
    } else {
      // Projected
      const projStart: string | null = lastEnd;
      const projEnd: string | null = projStart
        ? new Date(new Date(projStart).getTime() + gp.typical_duration_days * 86400000).toISOString()
        : null;
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        sequence_order: gp.sequence_order,
        typical_duration_days: gp.typical_duration_days,
        status: 'projected',
        actual_entered_at: null,
        actual_exited_at: null,
        actual_duration_days: null,
        projected_start: projStart,
        projected_end: projEnd,
      });
      if (projEnd) lastEnd = projEnd;
    }
  }
  return entries;
}

export default function PlantPhaseTimeline({ plant, history }: Props) {
  const { t } = useTranslation();
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!plant.species_key) {
      setLoading(false);
      return;
    }
    setLoading(true);
    phasesApi
      .getLifecycleConfig(plant.species_key)
      .then((lc) => phasesApi.listGrowthPhases(lc.key))
      .then(setGrowthPhases)
      .catch(() => setGrowthPhases([]))
      .finally(() => setLoading(false));
  }, [plant.species_key]);

  const timeline = useMemo(
    () => (growthPhases.length > 0 ? buildTimeline(growthPhases, history, plant) : []),
    [growthPhases, history, plant],
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (timeline.length === 0) return null;

  const activeStep = timeline.findIndex((p) => p.status === 'current');

  return (
    <Box data-testid="plant-phase-timeline">
      <Stepper
        orientation="vertical"
        activeStep={activeStep >= 0 ? activeStep : timeline.length}
        nonLinear
      >
        {timeline.map((phase) => (
          <Step key={phase.phase_key} completed={phase.status === 'completed'}>
            <StepLabel StepIconComponent={() => <StepIcon status={phase.status} />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body1">
                  {phase.display_name || phase.phase_name}
                </Typography>
                <Chip
                  size="small"
                  label={t(`pages.plantingRuns.phase${phase.status.charAt(0).toUpperCase() + phase.status.slice(1)}`)}
                  color={
                    phase.status === 'completed'
                      ? 'success'
                      : phase.status === 'current'
                        ? 'primary'
                        : 'default'
                  }
                  variant="outlined"
                />
              </Box>
            </StepLabel>
            <StepContent>
              {phase.status === 'completed' && (
                <Typography variant="body2" color="text.secondary">
                  {formatDate(phase.actual_entered_at)} &ndash; {formatDate(phase.actual_exited_at)}
                  {phase.actual_duration_days != null && ` (${phase.actual_duration_days}d)`}
                </Typography>
              )}
              {phase.status === 'current' && (() => {
                const daysIn = phase.actual_entered_at
                  ? Math.floor((Date.now() - new Date(phase.actual_entered_at).getTime()) / 86400000)
                  : 0;
                return (
                  <Box>
                    <Typography variant="body2" color="primary">
                      {t('pages.plantingRuns.daysOfTypical', {
                        current: daysIn,
                        typical: phase.typical_duration_days,
                      })}
                    </Typography>
                    {phase.projected_end && (
                      <Typography variant="body2" color="text.secondary">
                        {t('pages.plantingRuns.projectedEnd')}: {formatDate(phase.projected_end)}
                      </Typography>
                    )}
                  </Box>
                );
              })()}
              {phase.status === 'projected' && (
                <Typography variant="body2" color="text.secondary">
                  {phase.projected_start && `${t('pages.plantingRuns.projectedStart')}: ${formatDate(phase.projected_start)}`}
                  {phase.projected_start && phase.projected_end && ' \u2013 '}
                  {phase.projected_end && `${t('pages.plantingRuns.projectedEnd')}: ${formatDate(phase.projected_end)}`}
                  {!phase.projected_start && !phase.projected_end && `~${phase.typical_duration_days}d`}
                </Typography>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
}
