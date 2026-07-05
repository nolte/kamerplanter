import { describe, it, expect } from 'vitest';
import type { RouteObject } from 'react-router-dom';
import { router } from '@/routes/AppRoutes';

/**
 * Regression guard for #12 (REQ-025): the `PrivacySettingsPage` scaffold must be
 * reachable via a `<Route>`. It was authored but never wired into the router.
 */
function collectPaths(routes: RouteObject[]): string[] {
  const paths: string[] = [];
  for (const route of routes) {
    if (route.path) {
      paths.push(route.path);
    }
    if (route.children) {
      paths.push(...collectPaths(route.children));
    }
  }
  return paths;
}

describe('AppRoutes', () => {
  it('registers the privacy settings route (REQ-025, #12)', () => {
    const paths = collectPaths(router.routes);
    expect(paths).toContain('privacy');
    // Sanity: the sibling account-settings route is present too.
    expect(paths).toContain('settings');
  });
});
