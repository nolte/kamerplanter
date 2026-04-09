import { useEffect, useState, useMemo } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import * as phasesApi from '@/api/endpoints/phases';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type {
  PlantInstance,
  GrowthPhase,
  LifecycleConfig,
  PhaseHistoryEntry,
  PhaseTimelineEntry,
} from '@/api/types';
import { growthPhaseFromEntry } from '@/utils/phaseSequenceMapper';
import PhaseKamiTimeline from '@/pages/durchlaeufe/PhaseKamiTimeline';

interface Props {
  plant: PlantInstance;
  history: PhaseHistoryEntry[];
  speciesName?: string | null;
  onLifecycleLoaded?: (lc: LifecycleConfig) => void;
}

function buildTimeline(
  growthPhases: GrowthPhase[],
  history: PhaseHistoryEntry[],
  _plant: PlantInstance,
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

    if (h?.entered_at && h.exited_at) {
      // Phase has been entered and exited -> completed
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        description: undefined,
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
    } else if (h?.entered_at && !h.exited_at) {
      // Phase has been entered but not exited -> current (active)
      const projEnd = new Date(
        new Date(h.entered_at).getTime() + gp.typical_duration_days * 86400000,
      ).toISOString();
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        description: undefined,
        sequence_order: gp.sequence_order,
        typical_duration_days: gp.typical_duration_days,
        status: 'current',
        actual_entered_at: h.entered_at,
        actual_exited_at: null,
        actual_duration_days: null,
        projected_start: null,
        projected_end: projEnd,
      });
      lastEnd = projEnd;
    } else {
      // No history entry -> projected (not started)
      const projStart: string | null = lastEnd;
      const projEnd: string | null = projStart
        ? new Date(new Date(projStart).getTime() + gp.typical_duration_days * 86400000).toISOString()
        : null;
      entries.push({
        phase_key: gp.key,
        phase_name: gp.name,
        display_name: gp.display_name || gp.name,
        description: undefined,
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

export default function PlantPhaseTimeline({ plant, history, speciesName, onLifecycleLoaded }: Props) {
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!plant.species_key) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset loading when no species
      setLoading(false);
      return;
    }
    setLoading(true);

    // Try PhaseSequence first, fall back to LifecycleConfig + GrowthPhases
    phaseSequenceApi
      .getSpeciesPhaseSequence(plant.species_key)
      .catch(() => null)
      .then((sequence) => {
        if (sequence && sequence.entries.length > 0) {
          // Map PhaseSequence to LifecycleConfig-compatible object for callback
          const lcCompat: LifecycleConfig = {
            key: sequence.key,
            species_key: sequence.species_key,
            cycle_type: sequence.cycle_type,
            typical_lifespan_years: sequence.typical_lifespan_years,
            dormancy_required: sequence.dormancy_required,
            vernalization_required: sequence.vernalization_required,
            vernalization_min_days: sequence.vernalization_min_days,
            photoperiod_type: sequence.photoperiod_type,
            critical_day_length_hours: sequence.critical_day_length_hours,
            phase_sequence_key: sequence.key,
            created_at: sequence.created_at,
            updated_at: sequence.updated_at,
          };
          onLifecycleLoaded?.(lcCompat);
          const mapped = sequence.entries.map(growthPhaseFromEntry);
          setGrowthPhases(mapped);
          setLoading(false);
          return;
        }

        // Fallback: legacy LifecycleConfig + GrowthPhases path
        phasesApi
          .getLifecycleConfig(plant.species_key)
          .then((lc) => {
            onLifecycleLoaded?.(lc);
            return phasesApi.listGrowthPhases(lc.key);
          })
          .then(setGrowthPhases)
          .catch(() => setGrowthPhases([]))
          .finally(() => setLoading(false));
      });
  }, [plant.species_key, onLifecycleLoaded]);

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

  return <PhaseKamiTimeline phases={timeline} speciesName={speciesName} />;
}
