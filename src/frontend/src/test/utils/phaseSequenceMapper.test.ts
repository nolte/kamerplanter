import { describe, it, expect } from 'vitest';
import { growthPhaseFromEntry } from '@/utils/phaseSequenceMapper';
import type { PhaseSequenceEntry } from '@/api/types';

const baseEntry = (over: Partial<PhaseSequenceEntry> = {}): PhaseSequenceEntry =>
  ({
    key: 'entry-1',
    sequence_order: 2,
    is_terminal: false,
    allows_harvest: true,
    override_duration_days: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    phase_definition: {
      name: 'vegetative',
      display_name: 'Vegetativ',
      description: 'Wachstumsphase',
      typical_duration_days: 30,
      stress_tolerance: 'high',
      watering_interval_days: 3,
    },
    ...over,
  }) as unknown as PhaseSequenceEntry;

describe('growthPhaseFromEntry', () => {
  it('maps a fully-populated entry onto the GrowthPhase shape', () => {
    const gp = growthPhaseFromEntry(baseEntry());
    expect(gp).toMatchObject({
      key: 'entry-1',
      name: 'vegetative',
      display_name: 'Vegetativ',
      description: 'Wachstumsphase',
      typical_duration_days: 30,
      sequence_order: 2,
      is_terminal: false,
      allows_harvest: true,
      stress_tolerance: 'high',
      watering_interval_days: 3,
    });
    expect(gp.lifecycle_key).toBe('');
  });

  it('prefers override_duration_days over the definition default', () => {
    const gp = growthPhaseFromEntry(baseEntry({ override_duration_days: 12 }));
    expect(gp.typical_duration_days).toBe(12);
  });

  it('falls back to empty/default fields when phase_definition is missing', () => {
    const gp = growthPhaseFromEntry(baseEntry({ phase_definition: undefined }));
    expect(gp.name).toBe('');
    expect(gp.display_name).toBe('');
    expect(gp.description).toBe('');
    expect(gp.typical_duration_days).toBe(1); // final fallback
    expect(gp.stress_tolerance).toBe('medium');
    expect(gp.watering_interval_days).toBeNull();
  });

  it('uses the definition duration when no override is set', () => {
    const gp = growthPhaseFromEntry(baseEntry({ override_duration_days: null }));
    expect(gp.typical_duration_days).toBe(30);
  });
});
