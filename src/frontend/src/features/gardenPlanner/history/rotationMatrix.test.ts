import { describe, expect, it } from 'vitest';
import type { RotationMatrix, RotationMatrixBed, RotationPlanting } from './historyTypes';
import { FAMILY_PATTERNS, familyMarks, hasMoreBeds, mergeMatrixPage } from './rotationMatrix';

function planting(familyKey: string, familyName: string | null): RotationPlanting {
  return {
    season: null,
    family_key: familyKey,
    family_name: familyName,
    species_key: null,
    nutrient_demand: 'heavy_feeder',
    plan_role: 'main_crop',
    source: 'plant',
    care_event_key: null,
  };
}

function bedWith(key: string, ...families: [string, string | null][]): RotationMatrixBed {
  return {
    location_key: key,
    name: key,
    rotation_applicable: true,
    not_applicable_reason: null,
    rotation_reset_at: null,
    cells: [{ year: 2025, plantings: families.map(([k, n]) => planting(k, n)) }],
  };
}

function matrix(beds: RotationMatrixBed[], overrides: Partial<RotationMatrix> = {}): RotationMatrix {
  return { site_key: 's', years: 5, columns: [2025], total: beds.length, truncated: false, offset: 0, limit: 50, beds, ...overrides };
}

describe('familyMarks - a family is never carried by colour alone', () => {
  it('gives distinct families distinct codes, colours and (up to the pattern count) distinct patterns', () => {
    const families: [string, string][] = Array.from({ length: FAMILY_PATTERNS.length }, (_, index) => [
      `fam_${index}`,
      ['Solanaceae', 'Brassicaceae', 'Fabaceae', 'Cucurbitaceae', 'Apiaceae', 'Asteraceae', 'Poaceae', 'Lamiaceae'][index],
    ]);
    const marks = [...familyMarks([bedWith('b', ...families)]).values()];

    expect(new Set(marks.map((mark) => mark.pattern)).size).toBe(FAMILY_PATTERNS.length);
    expect(new Set(marks.map((mark) => mark.code)).size).toBe(marks.length);
    expect(new Set(marks.map((mark) => mark.color)).size).toBe(marks.length);
  });

  it('keeps the codes unique when names share a prefix or are equal', () => {
    const marks = [
      ...familyMarks([bedWith('b', ['a', 'Solanaceae'], ['b', 'Solanum'], ['c', 'Solanaceae'], ['d', null])]).values(),
    ];
    expect(new Set(marks.map((mark) => mark.code)).size).toBe(4);
    // a family without a name is shown by its key, never by an empty string
    expect(marks.find((mark) => mark.familyKey === 'd')?.name).toBe('d');
  });

  it('assigns the same marks whatever the order of the beds', () => {
    const one = bedWith('1', ['fab', 'Fabaceae']);
    const two = bedWith('2', ['sol', 'Solanaceae']);
    expect(familyMarks([one, two])).toEqual(familyMarks([two, one]));
  });

  it('keeps the marks of the families already shown when a further page brings an earlier-sorting family', () => {
    const first = familyMarks([bedWith('1', ['sol', 'Solanaceae'], ['fab', 'Fabaceae'])]);
    const order = [...first.keys()];
    const later = familyMarks([bedWith('1', ['sol', 'Solanaceae'], ['fab', 'Fabaceae']), bedWith('2', ['ama', 'Amaranthaceae'])], order);

    for (const key of order) expect(later.get(key)).toEqual(first.get(key));
    expect(later.get('ama')?.pattern).not.toBe(first.get('sol')?.pattern);
    expect([...later.keys()]).toEqual([...order, 'ama']);
  });

  it('marks nothing for a matrix without families', () => {
    expect(familyMarks([bedWith('b')]).size).toBe(0);
  });
});

describe('mergeMatrixPage', () => {
  it('appends the next page, keeps the columns and the look-back, and takes the new totals', () => {
    const first = matrix([bedWith('a')], { total: 3, years: 6, columns: [2020, 2021] });
    const next = matrix([bedWith('b'), bedWith('c')], { total: 3, years: 6, columns: [2020, 2021], offset: 1 });

    const merged = mergeMatrixPage(first, next);

    expect(merged.beds.map((bed) => bed.location_key)).toEqual(['a', 'b', 'c']);
    expect(merged.columns).toEqual([2020, 2021]);
    expect(hasMoreBeds(merged)).toBe(false);
    expect(hasMoreBeds(first)).toBe(true);
  });

  it('does not repeat a bed it already holds', () => {
    const merged = mergeMatrixPage(matrix([bedWith('a')]), matrix([bedWith('a'), bedWith('b')]));
    expect(merged.beds.map((bed) => bed.location_key)).toEqual(['a', 'b']);
  });

  it('starts from the first page', () => {
    const first = matrix([bedWith('a')]);
    expect(mergeMatrixPage(null, first)).toBe(first);
  });
});
