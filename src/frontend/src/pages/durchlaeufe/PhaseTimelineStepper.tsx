import { useEffect, useState } from 'react';
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
import EmptyState from '@/components/common/EmptyState';
import * as runApi from '@/api/endpoints/plantingRuns';
import type { SpeciesPhaseTimeline, PhaseTimelineEntry } from '@/api/types';
import {
  kamiPhaseGermination, kamiPhaseSeedling, kamiPhaseVegetative,
  kamiPhaseFlowering, kamiPhaseFlushing, kamiPhaseHarvest, kamiPhaseLeafPhase,
  kamiPhaseRipening, kamiPhaseJuvenile, kamiPhaseClimbing, kamiPhaseMature,
  kamiPhaseDormancy, kamiPhaseSenescence, kamiPhaseShortDayInduction,
} from '@/assets/brand/illustrations';

const PHASE_IMAGES: Record<string, string> = {
  germination: kamiPhaseGermination,
  seedling: kamiPhaseSeedling,
  vegetative: kamiPhaseVegetative,
  flowering: kamiPhaseFlowering,
  flushing: kamiPhaseFlushing,
  harvest: kamiPhaseHarvest,
  ripening: kamiPhaseRipening,
  fruiting: kamiPhaseRipening,
  juvenile: kamiPhaseJuvenile,
  climbing: kamiPhaseClimbing,
  mature: kamiPhaseMature,
  dormancy: kamiPhaseDormancy,
  senescence: kamiPhaseSenescence,
  leaf_phase: kamiPhaseLeafPhase,
  short_day_induction: kamiPhaseShortDayInduction,
};

interface Props {
  runKey: string;
}

function formatDate(iso: string | null): string {
  if (!iso) return '\u2014';
  return new Date(iso).toLocaleDateString();
}

function PhaseStepIcon({ status }: { status: PhaseTimelineEntry['status'] }) {
  if (status === 'completed') return <CheckCircleIcon color="success" />;
  if (status === 'current') return <RadioButtonCheckedIcon color="primary" />;
  return <RadioButtonUncheckedIcon color="disabled" />;
}

function PhaseDetail({ phase, t }: { phase: PhaseTimelineEntry; t: (key: string, opts?: Record<string, unknown>) => string }) {
  if (phase.status === 'completed') {
    return (
      <Typography variant="body2" color="text.secondary">
        {formatDate(phase.actual_entered_at)} &ndash; {formatDate(phase.actual_exited_at)}
        {phase.actual_duration_days != null && ` (${phase.actual_duration_days}d)`}
      </Typography>
    );
  }
  if (phase.status === 'current') {
    /* eslint-disable react-hooks/purity -- Date.now() during render is intentional for display-only elapsed time */
    const daysIn = phase.actual_entered_at
      ? Math.floor((Date.now() - new Date(phase.actual_entered_at).getTime()) / 86400000)
      : 0;
    /* eslint-enable react-hooks/purity */
    return (
      <Box>
        <Typography variant="body2" color="primary">
          {t('pages.plantingRuns.daysOfTypical', { current: daysIn, typical: phase.typical_duration_days })}
        </Typography>
        {phase.projected_end && (
          <Typography variant="body2" color="text.secondary">
            {t('pages.plantingRuns.projectedEnd')}: {formatDate(phase.projected_end)}
          </Typography>
        )}
      </Box>
    );
  }
  // projected
  return (
    <Typography variant="body2" color="text.secondary">
      {phase.projected_start && `${t('pages.plantingRuns.projectedStart')}: ${formatDate(phase.projected_start)}`}
      {phase.projected_start && phase.projected_end && ' \u2013 '}
      {phase.projected_end && `${t('pages.plantingRuns.projectedEnd')}: ${formatDate(phase.projected_end)}`}
      {!phase.projected_start && !phase.projected_end && `~${phase.typical_duration_days}d`}
    </Typography>
  );
}

export default function PhaseTimelineStepper({ runKey }: Props) {
  const { t } = useTranslation();
  const [timelines, setTimelines] = useState<SpeciesPhaseTimeline[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- set loading before async fetch
    setLoading(true);
    runApi
      .getPhaseTimeline(runKey)
      .then(setTimelines)
      .catch(() => setTimelines([]))
      .finally(() => setLoading(false));
  }, [runKey]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (timelines.length === 0) {
    return <EmptyState message={t('pages.plantingRuns.noPlantsYet')} />;
  }

  return (
    <Box data-testid="phase-timeline-stepper">
      {timelines.map((tl) => {
        const activeStep = tl.phases.findIndex((p) => p.status === 'current');
        return (
          <Box key={tl.species_key} sx={{ mb: 3 }}>
            {timelines.length > 1 && (
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                {tl.species_name ?? tl.species_key} ({tl.plant_count})
              </Typography>
            )}
            <Stepper
              orientation="vertical"
              activeStep={activeStep >= 0 ? activeStep : tl.phases.length}
              nonLinear
            >
              {tl.phases.map((phase) => (
                <Step key={phase.phase_key} completed={phase.status === 'completed'}>
                  <StepLabel
                    slots={{ stepIcon: () => <PhaseStepIcon status={phase.status} /> }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {PHASE_IMAGES[phase.phase_name.toLowerCase()] && (
                        <Box
                          component="img"
                          src={PHASE_IMAGES[phase.phase_name.toLowerCase()]}
                          alt=""
                          sx={{ width: 32, height: 32, objectFit: 'contain' }}
                        />
                      )}
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
                    <PhaseDetail phase={phase} t={t} />
                  </StepContent>
                </Step>
              ))}
            </Stepper>
          </Box>
        );
      })}
    </Box>
  );
}
