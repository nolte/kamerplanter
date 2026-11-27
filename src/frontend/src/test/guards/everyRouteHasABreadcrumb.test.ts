import { isValidElement, type ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { Navigate, type RouteObject } from 'react-router-dom';
import { router } from '@/routes/AppRoutes';
import { buildBreadcrumbs } from '@/routes/breadcrumbs';
import MainLayout from '@/layouts/MainLayout';

/**
 * #3018 (audit 2026-11, N-16) — every routed page of the shell has a breadcrumb (UI-NFR-005 R-014).
 *
 * Ten routes had no entry in `breadcrumbMap`, so the breadcrumb vanished on them. The list of routes
 * is **not** written down here: it is read from the constructed router (`router.routes`), so a page
 * added to `AppRoutes.tsx` without a breadcrumb entry turns this test red the moment it is routed.
 *
 * A route without a breadcrumb is only accepted for one of the named reasons below. The reason is
 * derived from the route itself (its element, its place in the tree) — with one exception, the
 * declared {@link PAGE_SUPPLIED_BREADCRUMBS}, whose page sets its own crumbs.
 */

/** Why a route legitimately renders no breadcrumb. */
const EXCLUSION_REASONS = {
  redirect: 'redirect: the element is a <Navigate>, the page shown is the target route',
  outsideShell: 'outside MainLayout (sign-in, registration, callbacks): the page has no breadcrumb slot',
  kiosk: 'kiosk shell: UI-NFR-019 R-017 shows no breadcrumbs',
  notFound: 'the 404 page: an unknown URL has no place in the hierarchy',
  pageSupplied: 'the page dispatches its own crumbs (setBreadcrumbs) with the entity names',
} as const;

type ExclusionReason = keyof typeof EXCLUSION_REASONS;

/**
 * Routes whose static breadcrumb cannot resolve because the path nests two keys, and whose page sets
 * its crumbs itself. Each entry names the page module; the test reads that module and fails when it no
 * longer dispatches `setBreadcrumbs` — then the route needs a static entry.
 */
const PAGE_SUPPLIED_BREADCRUMBS: Record<string, string> = {
  'stammdaten/species/:speciesKey/cultivars/:cultivarKey': '/src/pages/stammdaten/CultivarDetailPage.tsx',
};

const PAGE_SOURCES = import.meta.glob('/src/pages/**/*.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

interface RoutedPath {
  /** The route's full pattern without the leading slash, e.g. `stammdaten/species/:key`. */
  pattern: string;
  element: ReactNode;
  insideShell: boolean;
  insideKiosk: boolean;
}

function joinPath(parent: string, child: string | undefined): string {
  if (!child) return parent;
  return parent ? `${parent}/${child}` : child;
}

function isElementOfType(node: ReactNode, type: unknown): boolean {
  return isValidElement(node) && node.type === type;
}

/** Every route of the tree that has a path (or is an index route), with its full pattern and ancestry. */
function collectRoutes(
  routes: RouteObject[],
  parentPath = '',
  insideShell = false,
  insideKiosk = false,
): RoutedPath[] {
  const out: RoutedPath[] = [];
  for (const route of routes) {
    const pattern = joinPath(parentPath, route.path);
    const shell = insideShell || isElementOfType(route.element, MainLayout);
    const kiosk = insideKiosk || route.path === 'kiosk';
    if (route.path !== undefined || route.index) {
      out.push({ pattern, element: route.element, insideShell: shell, insideKiosk: kiosk });
    }
    if (route.children) out.push(...collectRoutes(route.children, pattern, shell, kiosk));
  }
  return out;
}

/** The reason a route has no breadcrumb, or `null` when it must have one. */
function exclusionReason(route: RoutedPath): ExclusionReason | null {
  if (route.insideKiosk) return 'kiosk';
  if (!route.insideShell) return 'outsideShell';
  if (isElementOfType(route.element, Navigate)) return 'redirect';
  if (route.pattern === '*' || route.pattern.endsWith('/*')) return 'notFound';
  if (route.pattern in PAGE_SUPPLIED_BREADCRUMBS) return 'pageSupplied';
  return null;
}

/**
 * The concrete URLs a pattern stands for: each `:param` becomes a sample key; an optional segment
 * (`:group?`) yields the URL without it and with it.
 */
function concreteUrls(pattern: string): string[] {
  let urls = [''];
  for (const segment of pattern.split('/').filter(Boolean)) {
    const optional = segment.endsWith('?');
    const value = segment.startsWith(':') ? `sample-${segment.replace(/[:?]/g, '')}` : segment.replace(/\?$/, '');
    const extended = urls.map((url) => `${url}/${value}`);
    urls = optional ? [...urls, ...extended] : extended;
  }
  return urls.map((url) => url || '/');
}

const ROUTES = collectRoutes(router.routes);
const SHELL_PAGES = ROUTES.filter((route) => exclusionReason(route) === null);

describe('every routed page has a breadcrumb (#3018 N-16, UI-NFR-005 R-014)', () => {
  it('reads a real route table', () => {
    // A traversal that found nothing would make every check below vacuous.
    expect(SHELL_PAGES.length).toBeGreaterThan(70);
    expect(SHELL_PAGES.map((r) => r.pattern)).toContain('dashboard');
  });

  it.each(SHELL_PAGES.flatMap((route) => concreteUrls(route.pattern).map((url) => [route.pattern, url] as const)))(
    '%s (%s) resolves to a breadcrumb',
    (_pattern, url) => {
      expect(buildBreadcrumbs(url), `no breadcrumbMap entry resolves ${url}`).not.toEqual([]);
    },
  );

  it('excludes routes only for a named reason, and every reason still matches a route', () => {
    const used = new Set(ROUTES.map(exclusionReason).filter((r): r is ExclusionReason => r !== null));
    // A reason no route needs any more is stale and must go, so the list cannot only grow.
    expect([...used].sort()).toEqual(Object.keys(EXCLUSION_REASONS).sort());
  });

  it('classifies the known exceptions as such, not as pages', () => {
    const reasonOf = (pattern: string) => {
      const route = ROUTES.find((r) => r.pattern === pattern);
      if (!route) throw new Error(`route ${pattern} is not registered`);
      return exclusionReason(route);
    };
    expect(reasonOf('kiosk')).toBe('kiosk');
    expect(reasonOf('pflege')).toBe('redirect');
    expect(reasonOf('*')).toBe('notFound');
    expect(reasonOf('login')).toBe('outsideShell');
    expect(reasonOf('settings/:group?')).toBeNull();
  });

  it.each(Object.entries(PAGE_SUPPLIED_BREADCRUMBS))(
    '%s is routed and its page (%s) sets its own breadcrumbs',
    (pattern, pagePath) => {
      expect(ROUTES.some((route) => route.pattern === pattern)).toBe(true);
      const source = PAGE_SOURCES[pagePath];
      expect(source, `${pagePath} is not a page module`).toBeDefined();
      expect(source).toMatch(/dispatch\(\s*setBreadcrumbs\(\s*\[/);
    },
  );

  describe('concreteUrls', () => {
    it('fills parameters and expands an optional segment', () => {
      expect(concreteUrls('stammdaten/species/:key')).toEqual(['/stammdaten/species/sample-key']);
      expect(concreteUrls('settings/:group?')).toEqual(['/settings', '/settings/sample-group']);
      expect(concreteUrls('')).toEqual(['/']);
    });
  });
});
