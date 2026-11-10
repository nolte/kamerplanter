/**
 * REQ-053 §11.3 "gesät" (W-015): a sown row or zone of the plant-states answer is drawn as `sown` - the port reads
 * the entry's `kind` instead of assuming a plant - and is keyed by its slot (it has no plant).
 */
import { describe, expect, it } from 'vitest';
import type { PlantStateEntryWire, PlantStateWire, SownStateWire } from './plantStateApi';
import { isPlantEntry, stateKeyOf } from './plantStateApi';
import { viewsOf, visualOf } from './usePlantStates';

const NOW = '2026-06-10T12:00:00Z';

const base = {
  slot_key: 'r1',
  slot_id: 'BED_R01',
  instance_id: 'BED_R01',
  species_key: 'sp_carrot',
  species_name: 'Carrot',
  planted_on: '2026-04-12',
  last_care: {},
  attention: [],
  harvest: { ready: false },
  inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0, phase: null },
};

const sown: SownStateWire = { ...base, kind: 'sown', plant_key: null, lifecycle: 'sown' };
const plant: PlantStateWire = {
  ...base,
  plant_key: 'p1',
  slot_key: 's1',
  instance_id: 'TOM-1',
  lifecycle: 'active',
};

describe('the sown entry of the plant states', () => {
  it('is computed as lifecycle sown', () => {
    expect(visualOf(sown, NOW).lifecycle).toBe('sown');
    expect(visualOf(plant, NOW).lifecycle).toBe('active');
  });

  it('is keyed by its slot, a plant by the plant', () => {
    const entries: PlantStateEntryWire[] = [sown, plant];
    expect(Object.keys(viewsOf(entries, NOW))).toEqual(['r1', 'p1']);
    expect(stateKeyOf(sown)).toBe('r1');
  });

  it('is not a plant for the plant lists', () => {
    expect([sown, plant].filter(isPlantEntry).map((entry) => entry.plant_key)).toEqual(['p1']);
  });
});
