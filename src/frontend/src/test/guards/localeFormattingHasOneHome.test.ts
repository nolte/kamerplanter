import { describe, expect, it } from 'vitest';
import { blankComments } from './jsxScan';

/**
 * #3025 M14 (audit A-13, A-16, A-21, B-10) — dates, numbers, sorting and per-language names
 * follow the UI language, and they do so in ONE place each.
 *
 * Each rule below names the pattern, the home it routes to, and why the pattern is wrong:
 *
 *  - `toLocaleDateString()` / `toLocaleString()` / `toLocaleTimeString()` -> `utils/formatting.ts`
 *    (`formatDate`, `formatDateTime`, `formatDateWith`, `formatTime`, `formatMonthName`,
 *    `formatNumber`). Without a locale they follow the BROWSER, not the app: "4/4/2026" in the
 *    German UI. With one passed by hand the rule is written once per call site.
 *  - a hard-coded BCP-47 tag (`'de-DE'`, `'en-GB'`) -> `activeLocale()`. Two of them disagreed
 *    (`en-GB` in the season panel, `en-US` everywhere else).
 *  - `a.localeCompare(b)` -> `compareText` (human text, active language) or `compareCodes`
 *    (`utils/compareCodes.ts`: keys, ids, enum values — the same order in every language).
 *  - `new Intl.*(undefined)` / `new Intl.*()` -> the browser's locale again; `new Intl.*('de')`
 *    -> one fixed language whatever the UI shows.
 *  - `dayjs(x).format('DD.MM.')` -> a German pattern in every language (and English weekday
 *    names: dayjs carries no locale here) -> `formatDateWith`.
 *  - `.replace('{{count}}', …)` -> i18next interpolation, which also picks the plural form.
 *  - `value.toFixed(n)` shown to the user -> `formatFixed(value, n)`: `toFixed` always writes
 *    a decimal POINT ("0.2 L" in German). Rounding a number (`Number(x.toFixed(2))`) is not
 *    display and is not reported.
 *  - a language test choosing between `x_de` and `x_en`/`x` -> `localizedText`
 *    (`utils/localizedText.ts`): UI language -> other language -> fallback.
 *
 * Shrink-only ratchet: `new Intl.*(language)` outside `utils/formatting.ts`. Those calls do
 * pass the UI language — they are correct, just not routed through the helpers — and they
 * sit almost all in the garden planner (`features/gardenPlanner/**`, own number/date formats
 * with `useGrouping`, `dateStyle`, `timeZone`). Migrating them is its own change; until then
 * the count may only go down.
 *
 * Blind spots: a formatter reached through a variable (`const f = x.toLocaleString; f()`),
 * `Intl` used via a re-export, `toFixed` whose result is turned into a number some other way
 * than `Number(…)`, and a language flag computed in one statement and used in another
 * (`const german = …; german ? a.name_de : a.name`) when the flag has another name than the
 * ones listed in `LANGUAGE_TEST`.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return (
    !/\.(test|spec)\.tsx?$/.test(path) &&
    !path.endsWith('.d.ts') &&
    !path.startsWith('/src/test/') &&
    !path.includes('/__mocks__/')
  );
}

const HOME = '/src/utils/formatting.ts';

const LANGUAGE_TEST =
  String.raw`(?:===\s*['"](?:de|en)['"]\)?|startsWith\(\s*['"](?:de|en)['"]\s*\)\)?|\b(?:isDE|isGerman|isEnglish|german|english)\b)`;

interface Rule {
  name: string;
  pattern: RegExp;
  /** File -> reason the pattern is right there. */
  allow: Record<string, string>;
}

const RULES: Rule[] = [
  {
    name: 'toLocale*String',
    pattern: /\.toLocale(?:Date|Time)?String\(/g,
    allow: { [HOME]: 'the home: formats with activeLocale()' },
  },
  {
    name: 'hard-coded BCP-47 locale',
    pattern: /['"`][a-z]{2}-[A-Z]{2}['"`]/g,
    allow: { [HOME]: 'the home: the UI-language -> BCP-47 table' },
  },
  {
    name: 'two-letter locale literal in Intl',
    pattern: /new\s+Intl\.\w+\(\s*['"`][a-z]{2}(?:-[A-Za-z]+)?['"`]/g,
    allow: {},
  },
  {
    name: 'dayjs display format',
    pattern: /\.format\(\s*['"`][^'"`]*\b(?:DD|MM|YYYY|HH|dd)\b/g,
    allow: {},
  },
  {
    name: 'localeCompare',
    pattern: /\.localeCompare\(/g,
    allow: {},
  },
  {
    name: 'Intl without a locale',
    pattern: /new\s+Intl\.\w+\(\s*(?:undefined\b|\))/g,
    allow: {},
  },
  {
    name: 'hand-made {{interpolation}}',
    pattern: /\.replace(?:All)?\(\s*['"`/]\{\{/g,
    allow: {},
  },
  {
    name: 'toFixed for display',
    pattern: /\.toFixed\(/g,
    allow: {
      '/src/features/gardenPlanner/editor/MeasureOverlay.tsx': 'SVG path data (`d` attribute): machine syntax, needs a decimal point',
      '/src/features/gardenPlanner/editor/EditorOverlay.tsx': 'SVG path data (`d` attribute): machine syntax, needs a decimal point',
      '/src/features/gardenPlanner/renderer/PlantMarker.tsx':
        'SVG coordinates and a `data-plan-progress` test hook: machine values, not text',
    },
  },
  {
    name: 'ad-hoc per-language field',
    pattern: new RegExp(`${LANGUAGE_TEST}\\s*(?:\\?(?!\\.)|&&)[^;]{0,160}?\\b\\w+_(?:de|en)\\b`, 'g'),
    allow: {
      '/src/features/gardenPlanner/bed/tentPhaseLabel.ts':
        "documented order with the app's own enum translation BETWEEN the two catalogue names (#2889)",
      '/src/pages/pflanzenschutz/PestDetailPage.tsx': 'a LIST of host plants per language, not one text',
    },
  },
];

/** `toFixed` inside `Number(…)` rounds a number; it does not produce display text. */
function isNumericRounding(source: string, index: number): boolean {
  let depth = 0;
  for (let i = index - 1; i >= 0; i -= 1) {
    const c = source[i];
    if (c === ')') depth += 1;
    else if (c === '(') {
      if (depth === 0) return /\bNumber\s*$/.test(source.slice(Math.max(0, i - 8), i));
      depth -= 1;
    } else if ((c === ';' || c === '{') && depth === 0) {
      return false;
    }
  }
  return false;
}

function findings(rule: Rule, rawSource: string): string[] {
  const source = blankComments(rawSource);
  return [...source.matchAll(rule.pattern)]
    .filter((match) => rule.name !== 'toFixed for display' || !isNumericRounding(source, match.index ?? 0))
    .map((match) => `${source.slice(0, match.index).split('\n').length}: ${match[0].replace(/\s+/g, ' ').slice(0, 60)}`);
}

/** `new Intl.*(` outside the home — measured 2026-11-26 after this change (all pass the UI language). */
const INTL_RATCHET = 51;
const INTL = /new\s+Intl\.\w+\(/g;

function intlSites(sources: Record<string, string>): number {
  return Object.entries(sources)
    .filter(([path]) => isProductionSource(path) && path !== HOME)
    .reduce((sum, [, source]) => sum + [...blankComments(source).matchAll(INTL)].length, 0);
}

describe('locale-aware formatting has one home (#3025 M14)', () => {
  const production = Object.entries(SOURCES).filter(([path]) => isProductionSource(path));

  it('scans the production tree (the glob is not empty)', () => {
    expect(production.length).toBeGreaterThan(500);
    expect(Object.keys(SOURCES)).toContain(HOME);
    expect(Object.keys(SOURCES)).toContain('/src/utils/localizedText.ts');
  });

  it.each(RULES.map((rule) => [rule.name, rule] as const))('no production source uses %s outside its allowlist', (_, rule) => {
    const offenders = production
      .filter(([path]) => !(path in rule.allow))
      .flatMap(([path, source]) => findings(rule, source).map((hit) => `${path}:${hit}`));
    expect(offenders).toEqual([]);
  });

  it.each(RULES.map((rule) => [rule.name, rule] as const))('keeps the %s allowlist real (no stale entries)', (_, rule) => {
    for (const path of Object.keys(rule.allow)) {
      expect(SOURCES[path], path).toBeDefined();
      expect(findings(rule, SOURCES[path]), `${path} no longer needs its ${rule.name} entry`).not.toEqual([]);
    }
  });

  it(`ratchets new Intl.*() outside the home: exactly ${INTL_RATCHET}, shrink-only`, () => {
    const count = intlSites(SOURCES);
    // Growing: route the new format through utils/formatting.ts instead. Shrinking: lower INTL_RATCHET.
    expect(count).toBe(INTL_RATCHET);
  });

  describe('detectors (seeded fixtures)', () => {
    const rule = (name: string) => RULES.find((r) => r.name === name) as Rule;

    it.each([
      ['toLocale*String', 'new Date(x).toLocaleDateString()'],
      ['toLocale*String', "d.toLocaleString(i18n.language, { month: 'long' })"],
      ['toLocale*String', 'v.toLocaleTimeString()'],
      ['hard-coded BCP-47 locale', "const locale = lang === 'de' ? 'de-DE' : 'en-GB';"],
      ['two-letter locale literal in Intl', "new Intl.NumberFormat('de', { maximumFractionDigits: 1 })"],
      ['two-letter locale literal in Intl', 'new Intl.DateTimeFormat("en")'],
      ['dayjs display format', "dayjs(ts).format('DD.MM. HH:mm')"],
      ['dayjs display format', "d.format('dd HH:mm')"],
      ['localeCompare', 'a.name.localeCompare(b.name)'],
      ['Intl without a locale', 'new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 })'],
      ['Intl without a locale', 'new Intl.Collator()'],
      ['hand-made {{interpolation}}', "t('x').replace('{{count}}', String(n))"],
      ['toFixed for display', '`${r.ec.toFixed(2)} mS/cm`'],
      ['toFixed for display', "{row.temp?.toFixed(1) ?? '–'}"],
      ['ad-hoc per-language field', "i18n.language === 'de' && t.name_de ? t.name_de : t.name"],
      ['ad-hoc per-language field', "(lang === 'en' ? s.name_en : s.name_de) || s.brand"],
      ['ad-hoc per-language field', "(language.startsWith('de') && task.name_de) || task.name"],
      ['ad-hoc per-language field', 'isEnglish ? a.message_en : a.message_de'],
    ])('%s reports %j', (name, code) => {
      expect(findings(rule(name), code)).not.toEqual([]);
    });

    it.each([
      ['toLocale*String', '// was new Date(x).toLocaleDateString() before #3025'],
      ['two-letter locale literal in Intl', 'new Intl.NumberFormat(language)'],
      ['dayjs display format', "dayjs().toISOString()"],
      ['dayjs display format', "logger.format('%s', value)"],
      ['localeCompare', 'compareText(a.name, b.name)'],
      ['Intl without a locale', 'new Intl.NumberFormat(language, { maximumFractionDigits: 2 })'],
      ['toFixed for display', 'const rounded = Number(value.toFixed(2));'],
      ['toFixed for display', 'return String(Number(value.toFixed(3)));'],
      ['toFixed for display', 'const raw = Number((value / perPlant).toFixed(DECIMALS));'],
      ['ad-hoc per-language field', 'localizedText(language, { de: t.name_de, en: t.name })'],
      ['ad-hoc per-language field', "const lang = i18n.language?.startsWith('en') ? 'en' : 'de';"],
    ])('%s leaves %j alone', (name, code) => {
      expect(findings(rule(name), code)).toEqual([]);
    });

    it('counts Intl constructions for the ratchet', () => {
      expect(intlSites({ '/src/a.ts': 'new Intl.NumberFormat(l); new Intl.DateTimeFormat(l, o);', [HOME]: 'new Intl.Collator(l)' })).toBe(2);
    });
  });
});
