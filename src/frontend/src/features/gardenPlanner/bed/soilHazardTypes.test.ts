/** Which locations the soil tab offers no soil hazard for, in the words the server refuses them with (#2888 F-20). */
import { describe, expect, it } from 'vitest';
import { soilHazardsUnavailable } from './soilHazardTypes';

describe('soilHazardsUnavailable', () => {
  it.each(['planter', 'tent', 'shelf', 'container'])('answers a %s as a vessel', (type) => {
    expect(soilHazardsUnavailable(type, 'manual')).toBe('container');
  });

  it.each(['hydro', 'nft', 'ebb_flow'])('answers %s irrigation as hydroponic', (irrigation) => {
    expect(soilHazardsUnavailable('raised_bed', irrigation)).toBe('hydroponic');
  });

  it('lets a bed with soil carry them', () => {
    expect(soilHazardsUnavailable('bed', 'drip')).toBeNull();
    expect(soilHazardsUnavailable('bed', undefined)).toBeNull();
  });
});
