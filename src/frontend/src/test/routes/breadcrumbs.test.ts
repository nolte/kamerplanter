import { describe, it, expect } from 'vitest';
import { buildBreadcrumbs } from '@/routes/breadcrumbs';

describe('buildBreadcrumbs', () => {
  it('returns an empty chain for an unknown path', () => {
    expect(buildBreadcrumbs('/does/not/exist')).toEqual([]);
  });

  it('returns a single current crumb for a top-level route without a parent', () => {
    expect(buildBreadcrumbs('/dashboard')).toEqual([{ label: 'nav.dashboard' }]);
  });

  it('prepends the parent chain for a nested list route', () => {
    expect(buildBreadcrumbs('/stammdaten/species')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.species' },
    ]);
  });

  it('walks a multi-level parent chain', () => {
    // /standorte/substrates/batches -> parent /standorte/substrates -> parent /dashboard
    expect(buildBreadcrumbs('/standorte/substrates/batches')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.substrates', path: '/standorte/substrates' },
      { label: 'nav.substrates' },
    ]);
  });

  it('renders a detail page: list link + non-clickable current detail crumb', () => {
    // /pflanzen/plant-instances/:key -> basePath match, detail page
    expect(buildBreadcrumbs('/pflanzen/plant-instances/abc123')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.plantInstances', path: '/pflanzen/plant-instances' },
      { label: 'nav.detail' },
    ]);
  });

  it('uses listPath override for the list link of virtual detail routes', () => {
    // /standorte/locations/:key -> basePath /standorte/locations has listPath /standorte/sites
    const crumbs = buildBreadcrumbs('/standorte/locations/loc-1');
    expect(crumbs).toContainEqual({ label: 'nav.sites', path: '/standorte/sites' });
    expect(crumbs[crumbs.length - 1]).toEqual({ label: 'nav.detail' });
  });

  it('resolves via the two-level-up (deepBase) fallback when basePath does not match', () => {
    // /duengung/plans/:key/edit -> basePath /duengung/plans/:key (no match) ->
    // deepBase /duengung/plans (match). basePath is unmapped, so this is not
    // flagged as a detail page: the matched label is the current (non-link) crumb.
    expect(buildBreadcrumbs('/duengung/plans/plan-1/edit')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.nutrientPlans' },
    ]);
  });

  it('returns an empty chain when even the deepBase does not match', () => {
    // 5-segment path: neither basePath nor deepBase resolve to a mapped route.
    expect(buildBreadcrumbs('/stammdaten/species/sp-1/cultivars/cv-1')).toEqual([]);
  });

  it('resolves a nested admin route to its /settings parent', () => {
    expect(buildBreadcrumbs('/admin/tenants')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.settings', path: '/settings' },
      { label: 'pages.auth.adminTenantsTitle' },
    ]);
  });
});
