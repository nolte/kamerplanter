import { useMemo } from 'react';
import { MS_PER_WEEK, computeCurrentWeek } from '@/utils/weekCalculation';
import type { NutrientPlanPhaseEntry, SpeciesPhaseTimeline } from '@/api/types';

// ── Gantt adaptation helpers ──────────────────────────────────────────

/**
 * Find the epoch for week-1: the actual_entered_at of the first timeline phase
 * that also exists in the nutrient plan entries.  Falls back to run.started_at.
 */
export function findGanttEpoch(
  planEntries: NutrientPlanPhaseEntry[],
  timelines: SpeciesPhaseTimeline[],
  runStartedAt: string | null,
): string | null {
  if (timelines.length > 0 && planEntries.length > 0) {
    const planPhaseNames = new Set<string>(planEntries.map((e) => e.phase_name));
    const phases = timelines[0].phases;
    for (const phase of phases) {
      if (planPhaseNames.has(phase.phase_name) && phase.actual_entered_at) {
        return phase.actual_entered_at;
      }
    }
  }
  return runStartedAt;
}

/**
 * Adapt nutrient plan phase entries to actual run durations.
 *
 * Uses a shift-based approach: for each plan phase, compute the offset between
 * the plan's phase start week and the actual phase start week. Apply that shift
 * to every entry, preserving relative positions within the phase (e.g. flushing
 * products stay at the end of flowering, not the beginning).
 *
 * Phases that don't exist in the timeline (e.g. "flushing") inherit the
 * cumulative shift from the previous matched phase.
 */
export function adaptEntriesToRun(
  planEntries: NutrientPlanPhaseEntry[],
  timelines: SpeciesPhaseTimeline[],
  epoch: string,
): NutrientPlanPhaseEntry[] {
  if (timelines.length === 0) return planEntries;
  const phases = timelines[0].phases;
  if (phases.length === 0) return planEntries;

  const epochDate = new Date(epoch);
  epochDate.setHours(0, 0, 0, 0);
  if (isNaN(epochDate.getTime())) return planEntries;

  // 1. Actual phase start weeks from timeline
  const actualStartWeek = new Map<string, number>();
  for (const phase of phases) {
    const enteredAt = phase.actual_entered_at ?? phase.projected_start;
    if (!enteredAt) continue;
    const d = new Date(enteredAt);
    d.setHours(0, 0, 0, 0);
    actualStartWeek.set(phase.phase_name, Math.max(1, Math.floor((d.getTime() - epochDate.getTime()) / MS_PER_WEEK) + 1));
  }

  // 2. Plan phase start weeks from entries (min week_start per phase)
  const planStartWeek = new Map<string, number>();
  for (const entry of planEntries) {
    const cur = planStartWeek.get(entry.phase_name);
    if (cur === undefined || entry.week_start < cur) {
      planStartWeek.set(entry.phase_name, entry.week_start);
    }
  }

  // 3. Compute shift per plan phase, sorted by plan start week.
  //    Unmatched phases (e.g. "flushing" not in timeline) inherit the last shift.
  const sortedPhases = [...planStartWeek.entries()].sort((a, b) => a[1] - b[1]);
  const shiftMap = new Map<string, number>();
  let cumulativeShift = 0;
  for (const [phaseName, planStart] of sortedPhases) {
    const actualStart = actualStartWeek.get(phaseName);
    if (actualStart !== undefined) {
      cumulativeShift = actualStart - planStart;
    }
    shiftMap.set(phaseName, cumulativeShift);
  }

  // 4. Apply shift — preserves relative position within each phase
  return planEntries.map((entry) => {
    const shift = shiftMap.get(entry.phase_name) ?? 0;
    if (shift === 0) return entry;
    return { ...entry, week_start: entry.week_start + shift, week_end: entry.week_end + shift };
  });
}

export interface ChannelDosage {
  fertilizerKey: string;
  mlPerLiter: number;
  optional: boolean;
  mixingOrder: number;
}

export interface ChannelGroup {
  channelId: string;
  channelLabel: string;
  applicationMethod: string;
  targetEcMs: number | null;
  targetPh: number | null;
  dosages: ChannelDosage[];
}

export interface RunNutrientData {
  ganttEpoch: string | null;
  currentWeek: number | undefined;
  adaptedEntries: NutrientPlanPhaseEntry[];
  currentDosages: {
    phaseName: string;
    floweringWeek: number | null;
    /** @deprecated flat list — use channelGroups instead */
    dosages: Array<{
      fertilizerKey: string;
      mlPerLiter: number;
      optional: boolean;
      channelLabel: string;
    }>;
    channelGroups: ChannelGroup[];
  } | null;
}

/**
 * Custom hook that computes derived Gantt / dosage data from raw plan entries,
 * phase timelines and the run's started_at timestamp.
 *
 * Returns a memoized object — callers must NOT destructure before useMemo boundary.
 */
export function useRunNutrientData(
  planEntries: NutrientPlanPhaseEntry[],
  phaseTimelines: SpeciesPhaseTimeline[],
  runStartedAt: string | null | undefined,
): RunNutrientData {
  const ganttEpoch = useMemo(
    () => findGanttEpoch(planEntries, phaseTimelines, runStartedAt ?? null),
    [planEntries, phaseTimelines, runStartedAt],
  );

  // Phase-relative currentWeek: anchored to the plan's week structure via
  // the active phase's actual_entered_at, matching PlantInstanceDetailPage logic.
  // Falls back to epoch-based calculation when no phase match is found.
  const currentWeek = useMemo(() => {
    if (phaseTimelines.length > 0 && planEntries.length > 0) {
      const phases = phaseTimelines[0].phases;
      // Find the currently active phase (entered but not exited)
      const activePhase = phases.find((p) => p.actual_entered_at && !p.actual_exited_at);
      if (activePhase) {
        const phaseStart = new Date(activePhase.actual_entered_at!);
        phaseStart.setHours(0, 0, 0, 0);
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        const diffMs = now.getTime() - phaseStart.getTime();
        if (diffMs >= 0) {
          const weeksInPhase = Math.floor(diffMs / MS_PER_WEEK) + 1;
          const sorted = [...planEntries].sort((a, b) => a.sequence_order - b.sequence_order);
          const phaseEntry = sorted.find((e) => e.phase_name === activePhase.phase_name);
          if (phaseEntry) {
            return phaseEntry.week_start + weeksInPhase - 1;
          }
        }
      }
    }
    // Fallback: weeks since epoch
    return ganttEpoch ? computeCurrentWeek(ganttEpoch) : undefined;
  }, [ganttEpoch, phaseTimelines, planEntries]);

  const adaptedEntries = useMemo(
    () =>
      ganttEpoch && planEntries.length > 0
        ? adaptEntriesToRun(planEntries, phaseTimelines, ganttEpoch)
        : planEntries,
    [planEntries, phaseTimelines, ganttEpoch],
  );

  const currentDosages = useMemo(() => {
    if (!currentWeek || adaptedEntries.length === 0) return null;
    const activeEntries = adaptedEntries.filter(
      (e) => currentWeek >= e.week_start && currentWeek <= e.week_end,
    );
    if (activeEntries.length === 0) return null;
    const dosageMap = new Map<string, { fertilizerKey: string; mlPerLiter: number; optional: boolean; channelLabel: string }>();
    const channelMap = new Map<string, ChannelGroup>();
    for (const entry of activeEntries) {
      for (const channel of entry.delivery_channels) {
        if (!channel.enabled) continue;
        if (!channelMap.has(channel.channel_id)) {
          channelMap.set(channel.channel_id, {
            channelId: channel.channel_id,
            channelLabel: channel.label,
            applicationMethod: channel.application_method,
            targetEcMs: channel.target_ec_ms,
            targetPh: channel.target_ph,
            dosages: [],
          });
        }
        const group = channelMap.get(channel.channel_id)!;
        for (const dosage of channel.fertilizer_dosages) {
          const mapKey = `${dosage.fertilizer_key}__${channel.channel_id}`;
          dosageMap.set(mapKey, {
            fertilizerKey: dosage.fertilizer_key,
            mlPerLiter: dosage.ml_per_liter,
            optional: dosage.optional,
            channelLabel: channel.label,
          });
          // Avoid duplicate fertilizers per channel
          if (!group.dosages.some((d) => d.fertilizerKey === dosage.fertilizer_key)) {
            group.dosages.push({
              fertilizerKey: dosage.fertilizer_key,
              mlPerLiter: dosage.ml_per_liter,
              optional: dosage.optional,
              mixingOrder: dosage.mixing_order,
            });
          }
        }
      }
    }
    // Sort dosages within each channel by mixing order
    for (const group of channelMap.values()) {
      group.dosages.sort((a, b) => a.mixingOrder - b.mixingOrder);
    }
    let floweringWeek: number | null = null;
    if (phaseTimelines.length > 0 && ganttEpoch) {
      const epochDate = new Date(ganttEpoch);
      epochDate.setHours(0, 0, 0, 0);
      const floweringPhase = phaseTimelines[0].phases.find((p) => p.phase_name === 'flowering');
      const enteredAt = floweringPhase?.actual_entered_at;
      if (enteredAt) {
        const floweringDate = new Date(enteredAt);
        floweringDate.setHours(0, 0, 0, 0);
        const floweringStartWeek = Math.max(1, Math.floor((floweringDate.getTime() - epochDate.getTime()) / MS_PER_WEEK) + 1);
        if (currentWeek >= floweringStartWeek) {
          floweringWeek = currentWeek - floweringStartWeek + 1;
        }
      }
    }
    return {
      phaseName: activeEntries[0].phase_name,
      floweringWeek,
      dosages: [...dosageMap.values()],
      channelGroups: [...channelMap.values()],
    };
  }, [currentWeek, adaptedEntries, phaseTimelines, ganttEpoch]);

  return useMemo(
    () => ({ ganttEpoch, currentWeek, adaptedEntries, currentDosages }),
    [ganttEpoch, currentWeek, adaptedEntries, currentDosages],
  );
}
