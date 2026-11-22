import { describe, expect, it } from 'vitest';
import * as barrel from './index';

describe('renderer barrel (what the editor may import)', () => {
  it('exposes no renderer implementation', () => {
    // GP-NFR-009: the route picks SvgPlanRenderer; the editor only ever sees the interface.
    expect(Object.keys(barrel).sort()).toEqual(['BOUNDARY_KEY', 'useRendererLabels']);
  });
});
