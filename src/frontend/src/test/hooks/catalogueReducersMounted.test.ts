/**
 * Every catalogue `useCatalogue` can read has a reducer mounted (#1568 review, S4).
 *
 * **Why this is worth a file.** A missing reducer does not fail where it is
 * missing. The selector reads `state.<name>.items` off `undefined`, and the page
 * dies with a render error naming neither the slice nor the hook. That happened
 * while this hook was being built: `nutrientPlans` was absent from the test store
 * and surfaced as nine failing `SpeciesDetailPage` cases whose messages said only
 * "Cannot read properties of undefined (reading 'plans')".
 *
 * Both stores are asserted, because they are maintained separately and it was the
 * test store that drifted.
 */
import { describe, it, expect } from 'vitest';
import { CATALOGUE_NAMES } from '@/hooks/useCatalogue';
import { store } from '@/store/store';
import { createTestStore } from '../helpers';

describe('catalogue reducers', () => {
  it.each(CATALOGUE_NAMES)('the application store mounts %s', (name) => {
    expect(store.getState()).toHaveProperty(name);
  });

  it.each(CATALOGUE_NAMES)('the test store mounts %s', (name) => {
    expect(createTestStore().getState()).toHaveProperty(name);
  });
});
