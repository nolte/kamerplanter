import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRunNutrientData } from '@/hooks/useRunNutrientData';
import type {
  ActiveChannel,
  DeliveryChannel,
  NutrientPlanPhaseEntry,
  PhaseName,
  PhaseTimelineEntry,
  SpeciesPhaseTimeline,
} from '@/api/types';

/**
 * #3016 — the run page shows the week and the dosages the server applies.
 *
 * The client used to derive the week itself — phase-relative, in local time — and pick dosages from the
 * plan entries for that week. The server (`GET /planting-runs/{key}/active-channels`) counts whole UTC
 * days since `started_at` and applies the entry of *that* week. Fixture: a run started 2026-10-06, in
 * flowering since 2026-11-03, observed at 00:30 CET on 2026-11-17 (= 2026-11-16 23:30 UTC):
 *
 * - server: (2026-11-16 - 2026-10-06).days = 41 -> 41 // 7 + 1 = week 6
 * - old client: flowering entered 14 local days ago -> 3rd week in phase -> 5 + 3 - 1 = week 7
 */

const PLAN_CHANNEL: DeliveryChannel = {
  channel_id: 'plan-only',
  label: 'Plan channel (client-side copy)',
  application_method: 'fertigation',
  enabled: true,
  notes: null,
  schedule: null,
  target_ec_ms: 9,
  target_ph: 9,
  fertilizer_dosages: [{ fertilizer_key: 'plan-fert', ml_per_liter: 99, optional: false, mixing_order: 1 }],
  method_params: null,
} as unknown as DeliveryChannel;

function entry(phase: PhaseName, sequence: number, weekStart: number, weekEnd: number): NutrientPlanPhaseEntry {
  return {
    key: `e-${phase}`,
    plan_key: 'plan-1',
    phase_name: phase,
    sequence_order: sequence,
    week_start: weekStart,
    week_end: weekEnd,
    is_recurring: false,
    npk_ratio: [1, 1, 1],
    calcium_ppm: null,
    magnesium_ppm: null,
    target_ec_ms: null,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0,
    notes: null,
    delivery_channels: [PLAN_CHANNEL],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
  };
}

function phase(name: string, sequence: number, enteredAt: string, exitedAt: string | null): PhaseTimelineEntry {
  return {
    phase_key: `p-${name}`,
    phase_name: name,
    display_name: name,
    sequence_order: sequence,
    typical_duration_days: 28,
    status: exitedAt ? 'completed' : 'current',
    actual_entered_at: enteredAt,
    actual_exited_at: exitedAt,
    actual_duration_days: null,
    projected_start: null,
    projected_end: null,
  };
}

const PLAN_ENTRIES = [entry('vegetative', 1, 1, 4), entry('flowering', 2, 5, 12)];
const TIMELINES: SpeciesPhaseTimeline[] = [
  {
    species_key: 'sp-1',
    species_name: 'Tomato',
    lifecycle_key: 'lc-1',
    cycle_type: null,
    plant_count: 3,
    phases: [
      phase('vegetative', 1, '2026-10-06T10:00:00Z', '2026-11-03T10:00:00Z'),
      phase('flowering', 2, '2026-11-03T10:00:00Z', null),
    ],
  },
];
const RUN_STARTED_AT = '2026-10-06T10:00:00Z';

/** What the server answered for week 6: its entry, its channels, sorted by mixing priority. */
const SERVER_CHANNELS: ActiveChannel[] = [
  {
    channel_id: 'drip',
    label: 'Drip',
    application_method: 'fertigation',
    target_ec_ms: 1.6,
    target_ph: 6,
    plan_key: 'plan-1',
    plan_name: 'Plan',
    entry_key: 'e-flowering',
    phase_name: 'flowering',
    week_start: 5,
    week_end: 12,
    dosages: [
      { fertilizer_key: 'calmag', product_name: 'CalMag', ml_per_liter: 0.5, optional: false, mixing_priority: 20 },
      { fertilizer_key: 'bloom', product_name: 'Bloom', ml_per_liter: 2, optional: true, mixing_priority: 40 },
    ],
  },
];

describe('useRunNutrientData (#3016)', () => {
  const zone = process.env.TZ;

  beforeEach(() => {
    process.env.TZ = 'Europe/Berlin';
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-11-16T23:30:00Z')); // 2026-11-17 00:30 CET
  });

  afterEach(() => {
    vi.useRealTimers();
    if (zone === undefined) delete process.env.TZ;
    else process.env.TZ = zone;
  });

  it('shows the week the server applies (UTC days since started_at), not a local phase-relative week', () => {
    const { result } = renderHook(() =>
      useRunNutrientData(PLAN_ENTRIES, TIMELINES, RUN_STARTED_AT, SERVER_CHANNELS),
    );
    expect(result.current.currentWeek).toBe(6);
  });

  it('shows the dosages the server returned, in its mixing order', () => {
    const { result } = renderHook(() =>
      useRunNutrientData(PLAN_ENTRIES, TIMELINES, RUN_STARTED_AT, SERVER_CHANNELS),
    );
    const dosages = result.current.currentDosages;
    expect(dosages?.phaseName).toBe('flowering');
    expect(dosages?.channelGroups).toEqual([
      {
        channelId: 'drip',
        channelLabel: 'Drip',
        applicationMethod: 'fertigation',
        targetEcMs: 1.6,
        targetPh: 6,
        dosages: [
          { fertilizerKey: 'calmag', mlPerLiter: 0.5, optional: false, mixingOrder: 20 },
          { fertilizerKey: 'bloom', mlPerLiter: 2, optional: true, mixingOrder: 40 },
        ],
      },
    ]);
    // 2026-11-03 -> 2026-11-16 (UTC) = 13 days -> 2nd flowering week
    expect(dosages?.floweringWeek).toBe(2);
  });

  it('shows no dosage when the server applies none, whatever the plan entries contain', () => {
    const { result } = renderHook(() => useRunNutrientData(PLAN_ENTRIES, TIMELINES, RUN_STARTED_AT, []));
    expect(result.current.currentDosages).toBeNull();
  });

  it('keeps the Gantt marker on the Gantt axis (weeks since the first plan phase)', () => {
    const { result } = renderHook(() =>
      useRunNutrientData(PLAN_ENTRIES, TIMELINES, RUN_STARTED_AT, SERVER_CHANNELS),
    );
    expect(result.current.ganttEpoch).toBe('2026-10-06T10:00:00Z');
    expect(result.current.ganttWeek).toBe(6);
  });
});
