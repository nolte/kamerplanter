import { describe, it, expect } from 'vitest';
import { SETTINGS_GROUPS } from '@/config/settingsGroups';

/**
 * F-11 (#2935) acceptance-5 — every in-app link into the settings points at a
 * section's new place.
 *
 * The tab bar addressed its tabs as `/settings#<tab>`; since F-11 a section is
 * `/settings/<group>#<section>`, and the old form is not mapped (operator
 * decision Q5): a link left on it silently lands on the first group. So the old
 * form must not occur in production code at all, and a literal `/settings/<x>`
 * must name a real group. Links are built with `settingsSectionPath()` from
 * `@/config/settingsGroups`, which cannot name a section that does not exist.
 */

const PRODUCTION_SOURCES = import.meta.glob(
  ['/src/**/*.ts', '/src/**/*.tsx', '!/src/test/**', '!/src/**/*.test.ts', '!/src/**/*.test.tsx'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

const GROUP_KEYS = new Set<string>(SETTINGS_GROUPS.map((g) => g.key));

/** Code without its comments, so an explanation of the old form is not a finding. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');
}

function findings(file: string, source: string): string[] {
  const code = stripComments(source);
  const out: string[] = [];
  // `/settings#…` (also `/settings/#…`), quoted or in a template literal.
  for (const m of code.matchAll(/['"`]\/settings\/?#[^'"`]*/g)) out.push(`${file}: old tab link ${m[0].slice(1)}`);
  // `/settings/<x>` whose first segment is not a group. Template interpolation is left to the type system.
  for (const m of code.matchAll(/['"`]\/settings\/([a-z][a-z0-9-]*)/g)) {
    if (!GROUP_KEYS.has(m[1])) out.push(`${file}: unknown settings group /settings/${m[1]}`);
  }
  return out;
}

describe('settings links (F-11 acceptance-5)', () => {
  it('scans the production sources', () => {
    expect(Object.keys(PRODUCTION_SOURCES).length).toBeGreaterThan(300);
  });

  it('leaves no link on the former /settings#<tab> form and names only real groups', () => {
    expect(Object.entries(PRODUCTION_SOURCES).flatMap(([file, source]) => findings(file, source))).toEqual([]);
  });

  it('detects both defects — fixtures', () => {
    expect(findings('a.tsx', "navigate('/settings#dashboard')")).toHaveLength(1);
    expect(findings('a.tsx', 'to="/settings#ha"')).toHaveLength(1);
    expect(findings('a.tsx', "to={'/settings/platform'}")).toHaveLength(1);
    expect(findings('a.tsx', "to='/settings/display#dashboard'")).toEqual([]);
    expect(findings('a.tsx', "navigate('/settings')")).toEqual([]);
    expect(findings('a.tsx', '// the old `/settings#ha` link')).toEqual([]);
  });
});
