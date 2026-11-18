import { useMemo } from 'react';
import { computeCurrentWeek, computeRunElapsedWeek } from '@/utils/weekCalculation';
import { utcCalendarDaysBetween } from '@/utils/calendarDay';
import type { ActiveChannel, NutrientPlanPhaseEntry, PhaseName, SpeciesPhaseTimeline } from '@/api/types';

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

  if (utcCalendarDaysBetween(epoch) === undefined) return planEntries;

  // 1. Actual phase start weeks from timeline (UTC calendar days, the server's clock)
  const actualStartWeek = new Map<string, number>();
  for (const phase of phases) {
    const enteredAt = phase.actual_entered_at ?? phase.projected_start;
    if (!enteredAt) continue;
    const days = utcCalendarDaysBetween(epoch, enteredAt);
    if (days === undefined) continue;
    actualStartWeek.set(phase.phase_name, Math.max(1, Math.floor(days / 7) + 1));
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
  /**
   * The run's nutrient-plan week by the server's rule (`computeRunElapsedWeek`) — the week whose dosages
   * the server applies and returns from `/active-channels`. Shown as "Week N".
   */
  currentWeek: number | undefined;
  /**
   * Today's week on the Gantt axis: weeks since `ganttEpoch`, the coordinate system of `adaptedEntries`.
   * Presentational only — it positions the marker over the shifted bars and never selects a dosage.
   */
  ganttWeek: number | undefined;
  adaptedEntries: NutrientPlanPhaseEntry[];
  currentDosages: {
    phaseName: PhaseName;
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

/** Shape the server's active channels into the dosage view; `null` when the server applies none. */
export function dosagesFromActiveChannels(
  activeChannels: ActiveChannel[] | null,
  phaseTimelines: SpeciesPhaseTimeline[],
  now: Date = new Date(),
): RunNutrientData['currentDosages'] {
  if (!activeChannels || activeChannels.length === 0) return null;
  const dosages: NonNullable<RunNutrientData['currentDosages']>['dosages'] = [];
  const channelGroups: ChannelGroup[] = activeChannels.map((channel) => {
    const seen = new Set<string>();
    const group: ChannelGroup = {
      channelId: channel.channel_id,
      channelLabel: channel.label,
      applicationMethod: channel.application_method,
      targetEcMs: channel.target_ec_ms,
      targetPh: channel.target_ph,
      dosages: [],
    };
    for (const dosage of channel.dosages) {
      // Avoid duplicate fertilizers per channel
      if (seen.has(dosage.fertilizer_key)) continue;
      seen.add(dosage.fertilizer_key);
      group.dosages.push({
        fertilizerKey: dosage.fertilizer_key,
        mlPerLiter: dosage.ml_per_liter,
        optional: dosage.optional,
        mixingOrder: dosage.mixing_priority,
      });
      dosages.push({
        fertilizerKey: dosage.fertilizer_key,
        mlPerLiter: dosage.ml_per_liter,
        optional: dosage.optional,
        channelLabel: channel.label,
      });
    }
    // The server already sorts by mixing priority; keep it stable if it ever does not.
    group.dosages.sort((a, b) => a.mixingOrder - b.mixingOrder);
    return group;
  });
  const floweringEnteredAt = phaseTimelines[0]?.phases.find((p) => p.phase_name === 'flowering')?.actual_entered_at;
  const floweringWeek = floweringEnteredAt ? (computeCurrentWeek(floweringEnteredAt, now) ?? null) : null;
  return {
    phaseName: activeChannels[0].phase_name,
    floweringWeek,
    dosages,
    channelGroups,
  };
}

/**
 * Derived nutrient data of a planting run.
 *
 * The week and the dosages come from the server's rule (#3016): `currentWeek` mirrors the server's
 * default week and `currentDosages` is the server's `/active-channels` answer, so the page never shows a
 * dosage the server would not apply. The Gantt adaptation (`ganttEpoch`, `adaptedEntries`, `ganttWeek`)
 * stays a client-side presentation of the plan against the actual phase dates.
 *
 * Returns a memoized object — callers must NOT destructure before useMemo boundary.
 */
export function useRunNutrientData(
  planEntries: NutrientPlanPhaseEntry[],
  phaseTimelines: SpeciesPhaseTimeline[],
  runStartedAt: string | null | undefined,
  activeChannels: ActiveChannel[] | null,
): RunNutrientData {
  const ganttEpoch = useMemo(
    () => findGanttEpoch(planEntries, phaseTimelines, runStartedAt ?? null),
    [planEntries, phaseTimelines, runStartedAt],
  );

  const currentWeek = useMemo(() => computeRunElapsedWeek(runStartedAt), [runStartedAt]);

  const ganttWeek = useMemo(() => (ganttEpoch ? computeCurrentWeek(ganttEpoch) : undefined), [ganttEpoch]);

  const adaptedEntries = useMemo(
    () =>
      ganttEpoch && planEntries.length > 0
        ? adaptEntriesToRun(planEntries, phaseTimelines, ganttEpoch)
        : planEntries,
    [planEntries, phaseTimelines, ganttEpoch],
  );

  const currentDosages = useMemo(
    () => dosagesFromActiveChannels(activeChannels, phaseTimelines),
    [activeChannels, phaseTimelines],
  );

  return useMemo(
    () => ({ ganttEpoch, currentWeek, ganttWeek, adaptedEntries, currentDosages }),
    [ganttEpoch, currentWeek, ganttWeek, adaptedEntries, currentDosages],
  );
}
