import { useEffect, useState, useMemo } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import * as phasesApi from '@/api/endpoints/phases';
import type { PlantInstance, GrowthPhase, PhaseHistoryEntry, PhaseTimelineEntry } from '@/api/types';
import PhaseKamiTimeline from '@/pages/durchlaeufe/PhaseKamiTimeline';

interface Props {
  plant: PlantInstance;
  history: PhaseHistoryEntry[];
  speciesName?: string | null;
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
      // Phase has been entered and exited → completed
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
      // Phase has been entered but not exited → current (active)
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
      // No history entry → projected (not started)
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

export default function PlantPhaseTimeline({ plant, history, speciesName }: Props) {
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

  return <PhaseKamiTimeline phases={timeline} speciesName={speciesName} />;
}
