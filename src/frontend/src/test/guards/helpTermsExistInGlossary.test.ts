import { describe, expect, it } from 'vitest';
import deGlossary from '@/i18n/locales/de/glossary.json';
import enGlossary from '@/i18n/locales/en/glossary.json';

/**
 * #3020 — every glossary key the code points at exists in BOTH languages (UI-NFR-011 §3.2/§6.3).
 *
 * `HelpTooltip` falls back to printing the raw key when a glossary entry is missing, so a typo in
 * `helpTerm="eec"` renders a help icon whose tooltip reads "eec" — nothing fails, nothing warns. This
 * guard reads every production source and checks each literal glossary key against the DE and EN
 * glossary files.
 *
 * Spellings covered (each exercised by a fixture below, in both directions):
 * - JSX props `helpTerm` / `glossaryTerm` as `="x"`, `='x'`, `{'x'}`, `{"x"}`, `{`x`}`;
 * - object properties `helpTerm: 'x'` (DataTable `Column.helpTerm`);
 * - `<HelpTooltip … term="x">`.
 *
 * A `helpTerm` whose value is not a string literal would be invisible to the check, so it is only
 * allowed as a pure pass-through (`helpTerm={helpTerm}`, `helpTerm={col.helpTerm}`) — anything else
 * is reported as an offender instead of being silently skipped.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return !/\.(test|spec)\.tsx?$/.test(path) && !path.endsWith('.d.ts') && !path.startsWith('/src/test/');
}

const LITERAL = String.raw`(?:"([^"\n]+)"|'([^'\n]+)'|\{\s*(?:"([^"\n]+)"|'([^'\n]+)'|\x60([^\x60$\n]+)\x60)\s*\})`;
const PROP_LITERAL = new RegExp(String.raw`\b(?:helpTerm|glossaryTerm)\s*=\s*` + LITERAL, 'g');
const OBJECT_LITERAL = new RegExp(String.raw`\bhelpTerm\s*:\s*(?:"([^"\n]+)"|'([^'\n]+)')`, 'g');
const HELP_TOOLTIP_TERM = new RegExp(String.raw`<HelpTooltip\b[^>]*?\bterm\s*=\s*` + LITERAL, 'g');
/** `helpTerm={…}` / `helpTerm: …` whose value is not a string literal. */
const PROP_EXPRESSION = /\bhelpTerm\s*=\s*\{\s*(?!["'\x60])([^}]*)\}/g;
const OBJECT_EXPRESSION = /\bhelpTerm\s*:\s*(?!["'\s])([^,}\n]+)/g;
const PASS_THROUGH = /^(?:helpTerm|[A-Za-z_$][\w$]*\.helpTerm)$/;

function firstGroup(match: RegExpMatchArray): string {
  return match.slice(1).find((g) => g !== undefined) ?? '';
}

/** Literal glossary keys referenced by `code`. */
function referencedTerms(code: string): string[] {
  const found: string[] = [];
  for (const pattern of [PROP_LITERAL, OBJECT_LITERAL, HELP_TOOLTIP_TERM]) {
    for (const match of code.matchAll(pattern)) found.push(firstGroup(match));
  }
  return found;
}

/** `helpTerm` values the literal check cannot see (and that are not a plain pass-through). */
function opaqueHelpTerms(code: string): string[] {
  const found: string[] = [];
  for (const pattern of [PROP_EXPRESSION, OBJECT_EXPRESSION]) {
    for (const match of code.matchAll(pattern)) {
      const expression = match[1].trim();
      if (!PASS_THROUGH.test(expression)) found.push(expression);
    }
  }
  return found;
}

type Glossary = Record<string, { short?: string; long?: string }>;
const DE = deGlossary.glossary as Glossary;
const EN = enGlossary.glossary as Glossary;

/** UI-NFR-011 §3.3 — the 38 mandatory terms, mapped onto their glossary keys. */
const MANDATORY_TERMS = [
  // Klima
  'vpd', 'rh', 'dif', 'hysterese',
  // Licht
  'ppfd', 'dli', 'photoperiod', 'lux_vs_ppfd',
  // Nährstoffe (Starkzehrer/Mittelzehrer/Schwachzehrer = zehrerklassen)
  'ec', 'npk', 'calmag', 'flushing', 'runoff', 'mixing_priority', 'zehrerklassen',
  // Substrat
  'cec', 'ph', 'drainage', 'air_porosity', 'substrat', 'staunaesse',
  // Wachstum
  'gdd', 'vernalization', 'dormancy', 'seneszenz', 'allelopathie', 'mischkultur', 'fruchtfolge',
  // Pflanzenschutz
  'ipm', 'karenzzeit', 'nuetzlinge',
  // Taxonomie
  'binomialnomenklatur', 'cultivar_varietaet', 'hardiness_zones',
  // Allgemein (the fourth, "pH-Wert", is `ph` above)
  'standort_slot', 'pflanzdurchlauf', 'umtopfen',
] as const;

function hasEntry(glossary: Glossary, term: string): boolean {
  const entry = glossary[term];
  return Boolean(entry?.short?.trim() && entry.long?.trim());
}

describe('glossary keys referenced in code (#3020)', () => {
  const production = Object.entries(SOURCES).filter(([path]) => isProductionSource(path));
  const references = production.flatMap(([path, code]) =>
    referencedTerms(code).map((term) => ({ path, term })),
  );

  it('the scan sees the call sites it is meant to check', () => {
    // A detector that silently matched nothing would pass every assertion below.
    expect(references.length).toBeGreaterThan(50);
    const files = new Set(references.map((r) => r.path));
    expect(files).toContain('/src/pages/standorte/WateringEventCreateDialog.tsx');
    expect(files).toContain('/src/pages/standorte/SubstrateListPage.tsx');
  });

  it('every literal helpTerm / glossaryTerm / HelpTooltip term exists in DE and EN', () => {
    const missing = references
      .filter(({ term }) => !hasEntry(DE, term) || !hasEntry(EN, term))
      .map(({ path, term }) => `${path}: ${term}`);
    expect(missing).toEqual([]);
  });

  it('no helpTerm value hides from the check behind an expression', () => {
    const offenders = production.flatMap(([path, code]) =>
      opaqueHelpTerms(code).map((expression) => `${path}: ${expression}`),
    );
    expect(offenders).toEqual([]);
  });

  it('DE and EN glossaries carry the same keys, each with short and long', () => {
    expect(Object.keys(EN).sort()).toEqual(Object.keys(DE).sort());
    const incomplete = Object.keys(DE).filter((term) => !hasEntry(DE, term) || !hasEntry(EN, term));
    expect(incomplete).toEqual([]);
  });

  it('all 38 mandatory UI-NFR-011 §3.3 terms are in the glossary', () => {
    expect(MANDATORY_TERMS).toHaveLength(37); // 38 minus the duplicate "pH-Wert"
    const missing = MANDATORY_TERMS.filter((term) => !hasEntry(DE, term) || !hasEntry(EN, term));
    expect(missing).toEqual([]);
  });
});

describe('glossary reference detectors (fixtures)', () => {
  it('finds every literal spelling', () => {
    const code = [
      '<FormNumberField name="a" helpTerm="ec" />',
      "<FormNumberField helpTerm='ph' />",
      "<X helpTerm={'vpd'} />",
      '<X helpTerm={"dli"} />',
      '<X helpTerm={`gdd`} />',
      "<SliderNumberField glossaryTerm=\"ppfd\" />",
      "const col = { id: 'ec', helpTerm: 'runoff', render };",
      '<HelpTooltip iconOnly term="npk" />',
      '<HelpTooltip\n  term="calmag"\n  iconOnly\n/>',
    ].join('\n');
    expect(referencedTerms(code).sort()).toEqual(
      ['calmag', 'dli', 'ec', 'gdd', 'npk', 'ph', 'ppfd', 'runoff', 'vpd'].sort(),
    );
  });

  it('ignores declarations and pass-throughs, and reports opaque values', () => {
    const clean = [
      'interface P { helpTerm?: string }',
      '  helpTerm,',
      '<FieldHelp helpTerm={helpTerm}>',
      '<HeaderLabelWithHelp helpTerm={col.helpTerm}>',
    ].join('\n');
    expect(referencedTerms(clean)).toEqual([]);
    expect(opaqueHelpTerms(clean)).toEqual([]);

    const opaque = [
      "<FormNumberField helpTerm={isTank ? 'ec' : 'ph'} />",
      'const col = { helpTerm: TERM_FOR_EC };',
      '<X helpTerm={terms.ec} />',
    ].join('\n');
    expect(opaqueHelpTerms(opaque)).toEqual(["isTank ? 'ec' : 'ph'", 'terms.ec', 'TERM_FOR_EC']);
  });
});
