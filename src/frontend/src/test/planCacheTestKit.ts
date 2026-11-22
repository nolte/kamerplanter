/**
 * Test kit for the plan cache (REQ-053 WP 9.2): a fresh, empty cache for every test, as after a page
 * load. Import `fake-indexeddb/auto` in the test file before this runs.
 */
import { planCacheDatabase } from '@/features/gardenPlanner/offline/db';
import { resetPlanCacheForTests } from '@/features/gardenPlanner/offline/planCache';

/** The open test connection (a retirement only flags the cache; tests reset it). */
export function testPlanCacheDatabase() {
  return planCacheDatabase(() => undefined);
}

export async function emptyPlanCache(): Promise<void> {
  resetPlanCacheForTests();
  const db = testPlanCacheDatabase();
  await Promise.all([
    db.plans.clear(),
    db.bedLists.clear(),
    db.siteLists.clear(),
    db.bedSummaries.clear(),
    db.bedSheets.clear(),
  ]);
}
