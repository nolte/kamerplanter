import { describe, expect, it } from 'vitest';
import {
  backfillErrors,
  backfillYears,
  buildBackfillBody,
  emptyBackfillForm,
  firstEmptyYear,
} from './backfillForm';
import { year } from './historyTestKit';

const NOW = new Date('2026-06-15T12:00:00Z');

describe('the years on offer', () => {
  it('run from last year back ten years, as the server accepts', () => {
    const years = backfillYears(NOW);
    expect(years[0]).toBe(2025);
    expect(years[years.length - 1]).toBe(2016);
    expect(years).toHaveLength(10);
  });

  it('start at the newest year nobody recorded', () => {
    expect(firstEmptyYear([], NOW)).toBe(2025);
    const solanum = { plantings: [{} as never] };
    expect(firstEmptyYear([{ year: 2025, ...solanum }, { year: 2024, ...solanum }, year(2023)], NOW)).toBe(2023);
    // every offered year recorded: fall back to the newest
    const all = backfillYears(NOW).map((value) => ({ year: value, ...solanum }));
    expect(firstEmptyYear(all, NOW)).toBe(2025);
  });
});

describe('backfillErrors', () => {
  it('asks for a family or a species unless the year was fallow', () => {
    expect(backfillErrors(emptyBackfillForm(2024), NOW)).toEqual({ family: 'family' });
    expect(backfillErrors({ ...emptyBackfillForm(2024), familyKey: 'fam' }, NOW)).toEqual({});
    expect(backfillErrors({ ...emptyBackfillForm(2024), speciesKey: 'sp' }, NOW)).toEqual({});
    expect(backfillErrors({ ...emptyBackfillForm(2024), planRole: 'fallow' }, NOW)).toEqual({});
  });

  it('refuses a year outside the window before the server does', () => {
    expect(backfillErrors({ ...emptyBackfillForm(2026), familyKey: 'fam' }, NOW)).toEqual({ year: 'year' });
    expect(backfillErrors({ ...emptyBackfillForm(2015), familyKey: 'fam' }, NOW)).toEqual({ year: 'year' });
  });
});

describe('buildBackfillBody', () => {
  it('sends the family and the role, and the season only when one was chosen', () => {
    expect(buildBackfillBody({ ...emptyBackfillForm(2024), familyKey: 'fam' }, null)).toEqual({
      year: 2024,
      plan_role: 'main_crop',
      family_key: 'fam',
    });
    expect(buildBackfillBody({ ...emptyBackfillForm(2024), familyKey: 'fam', season: 'autumn' }, null)).toMatchObject({
      season: 'autumn',
    });
  });

  it('lets a species stand for its family', () => {
    expect(buildBackfillBody({ ...emptyBackfillForm(2024), speciesKey: 'sp' }, 'fam_sol')).toEqual({
      year: 2024,
      plan_role: 'main_crop',
      species_key: 'sp',
      family_key: 'fam_sol',
    });
    // a species without a family sends the species alone; the server answers
    expect(buildBackfillBody({ ...emptyBackfillForm(2024), speciesKey: 'sp' }, null)).toEqual({
      year: 2024,
      plan_role: 'main_crop',
      species_key: 'sp',
    });
  });

  it('sends neither species nor family for a fallow year, even if the form still holds them', () => {
    expect(
      buildBackfillBody({ ...emptyBackfillForm(2024), planRole: 'fallow', speciesKey: 'sp', familyKey: 'fam' }, 'fam'),
    ).toEqual({ year: 2024, plan_role: 'fallow' });
  });
});
