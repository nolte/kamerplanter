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

  // F-12 (#2935): the admin pages hang under the platform admin's hub, not under
  // the personal settings page that used to carry it as a tab.
  it('resolves the platform admin hub under the dashboard', () => {
    expect(buildBreadcrumbs('/admin/platform')).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.platformAdmin' },
    ]);
  });

  it.each([
    ['/admin/oidc-providers', 'pages.admin.oidc.title'],
    ['/admin/plans', 'pages.plans.title'],
    ['/admin/tenant-imports', 'pages.tenantImports.title'],
  ])('resolves %s to the platform admin hub as its parent', (path, label) => {
    expect(buildBreadcrumbs(path)).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.platformAdmin', path: '/admin/platform' },
      { label },
    ]);
  });

  it.each([
    ['/admin/tenants/t-1', 'pages.auth.adminTenantsTitle'],
    ['/admin/users/u-1', 'pages.auth.adminUsersTitle'],
  ])('links the list crumb of %s to the hub, not to an unrouted list path', (path, label) => {
    // `/admin/tenants` and `/admin/users` are no routes of their own — the lists
    // are the hub's tables — so a crumb pointing at them would end on a 404.
    expect(buildBreadcrumbs(path)).toEqual([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.platformAdmin', path: '/admin/platform' },
      { label, path: '/admin/platform' },
      { label: 'nav.detail' },
    ]);
  });

  it('no longer routes any admin page through the settings page', () => {
    for (const path of ['/admin/platform', '/admin/tenants/t-1', '/admin/users/u-1', '/admin/plans']) {
      expect(buildBreadcrumbs(path).map((c) => c.path)).not.toContain('/settings');
    }
  });
});
