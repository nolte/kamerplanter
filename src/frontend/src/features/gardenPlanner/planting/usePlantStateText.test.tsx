import { renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { formatDay, MAX_INFO_LINES, usePlantStateText } from './usePlantStateText';
import type { PlantStateWire } from './plantStateApi';
import { visualOf, type PlantStateView } from './usePlantStates';

/** The plant info is one glance: at most eight lines, the reasons to act never the ones that give way (GP-FR-190). */
const NOW = '2026-06-10T12:00:00Z';

function view(overrides: Partial<PlantStateWire> = {}): PlantStateView {
  const wire: PlantStateWire = {
    plant_key: 'pl_1',
    slot_id: 'A1',
    instance_id: 'TOM-1',
    species_key: 'sp',
    species_name: 'Tomato',
    scientific_name: 'Solanum lycopersicum',
    planted_on: '2026-04-01',
    lifecycle: 'active',
    phase: { key: 'ph', name: 'Flowering', elapsed_d: 21, typical_d: 60, fraction: 0.35, next_phase_eta: '2026-07-19' },
    last_care: { watering: '2026-06-05T07:00:00Z', feeding: '2026-06-01T07:00:00Z' },
    next_task: { name: 'Prune', category: 'pruning', due: '2026-06-08' },
    attention: [],
    finding_label: 'Aphids',
    harvest: { ready: true, ready_from: '2026-05-20', harvested_total_g: 150.5 },
    inputs: {
      open_tasks: [{ category: 'pruning', due: '2026-06-08' }],
      open_findings: 1,
      frost_risk: true,
      harvest_batches: 1,
      phase: { key: 'ph', started_on: '2026-05-20', typical_days: 60, allows_harvest: true, is_terminal: false },
    },
    ...overrides,
  };
  return { ...wire, visual: visualOf(wire, NOW) };
}

describe('usePlantStateText', () => {
  it('labels a marker like "Tomato, Flowering, Finding: Aphids" (GP-UX-062)', () => {
    const { result } = renderHook(() => usePlantStateText());
    const text = result.current.ariaLabel(view());
    expect(text.startsWith('Tomato, Flowering, ')).toBe(true);
    expect(text).toContain('Finding: Aphids');
    expect(text).toContain('1 task overdue');
  });

  it('names the lifecycle of a plant that is not simply growing', () => {
    const { result } = renderHook(() => usePlantStateText());
    const harvesting = view({ inputs: { ...view().inputs, open_tasks: [], open_findings: 0, frost_risk: false } });
    expect(result.current.ariaLabel(harvesting)).toContain('Harvesting');
  });

  it('falls back from the species name to the scientific name to the instance id', () => {
    const { result } = renderHook(() => usePlantStateText());
    expect(result.current.name(view({ species_name: null }))).toBe('Solanum lycopersicum');
    expect(result.current.name(view({ species_name: null, scientific_name: null }))).toBe('TOM-1');
  });

  it('keeps the info at eight lines and drops the least useful first, never a reason to act', () => {
    const { result } = renderHook(() => usePlantStateText());
    const lines = result.current.lines(view());
    expect(lines.length).toBeLessThanOrEqual(MAX_INFO_LINES);
    const keys = lines.map((line) => line.key);
    expect(keys).toContain('attention-problem');
    expect(keys).toContain('attention-frost');
    expect(keys).toContain('attention-overdue');
    expect(keys).toContain('task');
    // the first to give way
    expect(keys).not.toContain('harvested');
    expect(keys).not.toContain('eta');
  });

  it('leaves out what is not there', () => {
    const { result } = renderHook(() => usePlantStateText());
    const sparse = view({
      slot_id: null,
      last_care: {},
      next_task: null,
      phase: null,
      harvest: { ready: false },
      inputs: { open_tasks: [], open_findings: 0, frost_risk: false, harvest_batches: 0, phase: null },
    });
    expect(result.current.lines(sparse).map((line) => line.key)).toEqual(['age']);
  });

  it('hands the renderer the top reason as the one badge and the initial of the species', () => {
    const { result } = renderHook(() => usePlantStateText());
    const marker = result.current.marker(view());
    expect(marker.badge).toBe('problem');
    expect(marker.initial).toBe('T');
    expect(marker.progress).toBeCloseTo(0.35, 2);
  });
});

describe('formatDay', () => {
  const zone = process.env.TZ;
  afterEach(() => {
    if (zone === undefined) delete process.env.TZ;
    else process.env.TZ = zone;
  });

  it.each(['America/Los_Angeles', 'UTC', 'Pacific/Auckland'])(
    'shows a date without a time as that very day in %s (a calendar day is not an instant)',
    (timeZone) => {
      process.env.TZ = timeZone;
      expect(formatDay('2026-06-15', 'en')).toBe('Jun 15, 2026');
    },
  );

  it('keeps the viewer\'s zone for an instant', () => {
    process.env.TZ = 'America/Los_Angeles';
    expect(formatDay('2026-06-15T03:00:00Z', 'en')).toBe('Jun 14, 2026');
  });

  it('answers nothing for a missing or unreadable value', () => {
    expect(formatDay(null, 'en')).toBeNull();
    expect(formatDay('', 'en')).toBeNull();
    expect(formatDay('2026-13-45', 'en')).toBeNull();
  });
});
