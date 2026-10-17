import { describe, expect, it } from 'vitest';
import { buildTree, neighbourKey } from './planTree';
import { testPlan } from './tools/toolTestKit';

const typeName = (type: string) => `type:${type}`;

describe('buildTree', () => {
  const rows = buildTree(testPlan(), typeName);

  it('walks garden -> area -> bed -> object in reading order', () => {
    expect(rows.map((row) => `${row.depth}:${row.key}`)).toEqual([
      '1:area',
      '2:b1',
      '2:b2',
      '2:t1',
      '1:lock',
      '1:solo',
    ]);
  });

  it('calls a location with locations below it an area and a leaf a bed', () => {
    expect(rows.find((row) => row.key === 'area')?.level).toBe('area');
    expect(rows.find((row) => row.key === 'b1')?.level).toBe('bed');
    expect(rows.find((row) => row.key === 't1')?.level).toBe('object');
  });

  it('keeps flags the list needs', () => {
    expect(rows.find((row) => row.key === 'lock')?.locked).toBe(true);
    expect(rows.find((row) => row.key === 't1')?.name).toBe('Tree');
  });
});

describe('neighbourKey', () => {
  const rows = buildTree(testPlan(), typeName);

  it('prefers the next row that stays', () => {
    expect(neighbourKey(rows, new Set(['b1']))).toBe('b2');
  });

  it('skips everything below a removed area', () => {
    expect(neighbourKey(rows, new Set(['area']))).toBe('lock');
  });

  it('falls back to the previous row at the end of the list', () => {
    expect(neighbourKey(rows, new Set(['solo']))).toBe('lock');
  });

  it('has no neighbour when everything goes or nothing does', () => {
    expect(
      neighbourKey(rows, new Set(rows.filter((row) => row.depth === 1).map((r) => r.key))),
    ).toBeNull();
    expect(neighbourKey(rows, new Set(['nope']))).toBeNull();
  });
});
