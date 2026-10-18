import { describe, expect, it } from 'vitest';
import { allowedBedTransitions } from './bedStatus';

describe('allowedBedTransitions (V-10, GP-API-018)', () => {
  it('lets a lead retire a planned or active bed and reactivate a retired one', () => {
    expect(allowedBedTransitions('planned', true)).toEqual(['active', 'retired']);
    expect(allowedBedTransitions('active', true)).toEqual(['retired']);
    expect(allowedBedTransitions('retired', true)).toEqual(['active']);
  });

  it('lets a grower only bring a planned bed into use', () => {
    expect(allowedBedTransitions('planned', false)).toEqual(['active']);
    expect(allowedBedTransitions('active', false)).toEqual([]);
    expect(allowedBedTransitions('retired', false)).toEqual([]);
  });
});
