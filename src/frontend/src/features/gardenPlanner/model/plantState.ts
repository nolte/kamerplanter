/**
 * Visual state of one plant on the garden plan — TypeScript port of
 * `app/domain/calculators/plant_state_calculator.py` (REQ-053 GP-FR-192, GP-UX-059/060).
 *
 * The Python module is the reference and carries the full rationale (calendar days in UTC, the priority
 * `problem > frost > overdue > water > harvest`, missing sources dropping their reason); this port mirrors it
 * operation for operation. Both run against `spec/e2e-testcases/fixtures/garden-plan-vectors.json`
 * (operation `plant_state`, GP-ACC-050, §19.6). The server answer wins on any difference.
 *
 * Pure: no I/O, no React, no clock — `now` is an argument. Days are `YYYY-MM-DD` strings (UTC calendar days),
 * which compare correctly as text.
 */

export type Lifecycle = 'planned' | 'sown' | 'active' | 'harvesting' | 'failed' | 'historic';
export type AttentionCode = 'problem' | 'frost' | 'overdue' | 'water' | 'harvest';

export const LIFECYCLES: readonly Lifecycle[] = [
  'planned',
  'sown',
  'active',
  'harvesting',
  'failed',
  'historic',
];
/** Reasons that need attention, highest priority first (GP-UX-060). */
export const ATTENTION_PRIORITY: readonly AttentionCode[] = [
  'problem',
  'frost',
  'overdue',
  'water',
  'harvest',
];
/** `termination_type` values that count as a failure (§11.3 "ausgefallen"). */
const FAILED_TERMINATIONS: ReadonlySet<string> = new Set(['died', 'senesced']);
const WATERING_CATEGORY = 'watering';
const MS_PER_DAY = 86_400_000;

export interface PlantFacts {
  kind: 'plant' | 'planned' | 'sown';
  removed_on: string | null;
  termination_type: string | null;
}

export interface PhaseFacts {
  key: string;
  started_on: string;
  typical_days: number | null;
  allows_harvest: boolean;
  is_terminal: boolean;
}

export interface OpenTask {
  category: string;
  due: string | null;
}

export interface PhaseProgress {
  elapsed_d: number;
  typical_d: number | null;
  fraction: number | null;
  next_phase_eta: string | null;
}

export interface AttentionReason {
  reason: AttentionCode;
  count: number;
}

export interface PlantVisualState {
  lifecycle: Lifecycle;
  phase_key: string | null;
  phase_progress: PhaseProgress | null;
  attention: AttentionReason[];
  harvest_ready: boolean;
  harvest_ready_from: string | null;
}

export interface ComputeOptions {
  open_findings: number;
  frost_risk: boolean;
  harvest_batches: number;
  /** An ISO instant; its UTC calendar day is "today". */
  now: string;
}

let lastInstant = '';
let lastDay = '';

/**
 * The UTC calendar day (`YYYY-MM-DD`) of an ISO instant. A whole bed is computed at one `now`, so the last
 * answer is kept: 5 000 plants parse the instant once, not 5 000 times (GP-NFR-073).
 */
export function utcDay(instant: string): string {
  if (instant !== lastInstant) {
    lastDay = new Date(instant).toISOString().slice(0, 10);
    lastInstant = instant;
  }
  return lastDay;
}

function dayNumber(day: string): number {
  return Math.floor(Date.parse(`${day}T00:00:00Z`) / MS_PER_DAY);
}

function addDays(day: string, days: number): string {
  return new Date(Date.parse(`${day}T00:00:00Z`) + days * MS_PER_DAY).toISOString().slice(0, 10);
}

function lifecycleOf(plant: PlantFacts, harvestBatches: number): Lifecycle {
  if (plant.kind !== 'plant') return plant.kind;
  if (plant.termination_type !== null && FAILED_TERMINATIONS.has(plant.termination_type)) return 'failed';
  if (plant.removed_on !== null || plant.termination_type !== null) return 'historic';
  return harvestBatches > 0 ? 'harvesting' : 'active';
}

function progressOf(phase: PhaseFacts, today: string): PhaseProgress {
  const elapsed = Math.max(dayNumber(today) - dayNumber(phase.started_on), 0);
  const typical = phase.typical_days !== null && phase.typical_days > 0 ? phase.typical_days : null;
  return {
    elapsed_d: elapsed,
    typical_d: typical,
    fraction: typical === null ? null : Math.min(elapsed / typical, 1),
    next_phase_eta: typical === null || phase.is_terminal ? null : addDays(phase.started_on, typical),
  };
}

/** The visual state of `plant` at `options.now` (UTC calendar day). See the Python reference for the rules. */
export function computePlantState(
  plant: PlantFacts,
  phase: PhaseFacts | null,
  tasks: readonly OpenTask[],
  options: ComputeOptions,
): PlantVisualState {
  const today = utcDay(options.now);
  const lifecycle = lifecycleOf(plant, options.harvest_batches);
  const live = lifecycle === 'active' || lifecycle === 'harvesting';
  const hasPhase = phase !== null && plant.kind === 'plant';
  const harvestReady = live && phase !== null && phase.allows_harvest;

  const attention: AttentionReason[] = [];
  if (live) {
    const counts: Record<AttentionCode, number> = {
      problem: Math.max(options.open_findings, 0),
      frost: options.frost_risk ? 1 : 0,
      overdue: tasks.filter((task) => task.due !== null && task.due < today).length,
      water: tasks.filter((task) => task.category === WATERING_CATEGORY && task.due === today).length,
      harvest: harvestReady ? 1 : 0,
    };
    for (const reason of ATTENTION_PRIORITY) {
      if (counts[reason] > 0) attention.push({ reason, count: counts[reason] });
    }
  }
  return {
    lifecycle,
    phase_key: hasPhase ? phase.key : null,
    phase_progress: hasPhase ? progressOf(phase, today) : null,
    attention,
    harvest_ready: harvestReady,
    harvest_ready_from: harvestReady && phase !== null ? phase.started_on : null,
  };
}
