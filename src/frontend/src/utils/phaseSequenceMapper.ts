import type { GrowthPhase, PhaseSequenceEntry, StressTolerance } from '@/api/types';

/**
 * Map a PhaseSequenceEntry (with embedded PhaseDefinition) to a GrowthPhase-compatible object.
 * Used across timeline, transition dialogs, and batch transition components to
 * bridge the PhaseSequence model to the legacy GrowthPhase interface.
 */
export function growthPhaseFromEntry(entry: PhaseSequenceEntry): GrowthPhase {
  return {
    key: entry.key,
    name: entry.phase_definition?.name ?? '',
    display_name: entry.phase_definition?.display_name ?? '',
    description: entry.phase_definition?.description ?? '',
    lifecycle_key: '',
    typical_duration_days:
      entry.override_duration_days ?? entry.phase_definition?.typical_duration_days ?? 1,
    sequence_order: entry.sequence_order,
    is_terminal: entry.is_terminal,
    allows_harvest: entry.allows_harvest,
    stress_tolerance: (entry.phase_definition?.stress_tolerance ?? 'medium') as StressTolerance,
    watering_interval_days: entry.phase_definition?.watering_interval_days ?? null,
    created_at: entry.created_at,
    updated_at: entry.updated_at,
  };
}
