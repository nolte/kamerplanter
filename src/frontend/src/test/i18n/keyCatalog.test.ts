import { describe, expect, it } from 'vitest';
import { deFull, enFull } from '../i18nTestResources';
import {
  createKeyIndex,
  exportedConstants,
  flattenCatalog,
  keyLiterals,
  keyTemplates,
  keyUsages,
  parityGaps,
  placeholderMismatches,
  type FlatCatalog,
  type KeyIndex,
} from './keyUsageScan';

/**
 * #3025 M14 (audit I-01/I-02) — every key the code asks for exists, and German and
 * English carry the same keys with the same placeholders.
 *
 * Thirteen statically used keys without a definition (I-01) reached the UI as raw
 * keys because nothing compared the code with the catalogue. This guard does, in
 * four layers (details in `keyUsageScan.ts`):
 *
 *  1. **Parity** — the flattened DE and EN catalogues have the same keys, and each
 *     key has the same `{{placeholders}}` in both.
 *  2. **Static lookups** — `t('…')`, `i18n.t(…)`, `<Trans i18nKey="…">` and templates
 *     whose `${}` parts are string constants resolve to a key (a leaf, a plural family
 *     `key_one`/`key_other`, or a branch read with `returnObjects`).
 *  3. **Key-shaped literals** — every string or template literal starting with a
 *     catalogue namespace (`'pages.…'`, `` `${PREFIX}.title` `` …), wherever it is
 *     written: a `labelKey` in a config array, a `Record<Enum, key>` table, the
 *     fallback of `errorKey(…)`, the branches of a conditional. Most indirect
 *     lookups are covered here, because their keys are written down somewhere.
 *  4. **Runtime parts** — `` t(`enums.phaseName.${phase}`) ``: the static head must be
 *     a branch of the catalogue. The value after it comes from data at runtime and is
 *     **not visible** to this guard (a phase the backend adds without a label shows
 *     up raw). Enum label lists that the code owns are pinned by their own parity
 *     tests in this directory (diary, notification channels …).
 *
 * What remains are lookups whose key the call itself does not show (`t(labelKey)`).
 * They are not skipped silently: each must match one of the declared
 * `INDIRECT_LOOKUP_SHAPES` below, each shape says why its keys are covered (or that
 * they are not), and a shape no call site uses any more fails as stale.
 *
 * Blind spots, deliberately accepted: a translation function under another name
 * (`const { t: tr } = …`), keys assembled in a helper and returned as a plain
 * string without any key-shaped literal, the suffix appended to a prefix that is
 * handed in as a prop, and keys the server sends (`trigger_reason_i18n_key`,
 * `unavailable_reason`).
 */

const SOURCES = import.meta.glob(
  ['/src/**/*.ts', '/src/**/*.tsx', '!/src/**/*.test.ts', '!/src/**/*.test.tsx', '!/src/test/**', '!/src/**/*.d.ts'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

const DE: FlatCatalog = flattenCatalog(deFull);
const EN: FlatCatalog = flattenCatalog(enFull);
const INDEX: KeyIndex = createKeyIndex(DE);
const NAMESPACES = Object.keys(deFull);
const EXPORTED = exportedConstants(SOURCES);

/**
 * Key-shaped literals that are not translation keys. Keep it short; each needs a reason.
 */
const NOT_A_KEY: Record<string, string> = {
  'common.white': 'MUI palette path (`theme.palette.common.white`) passed as a `color`/`sx` value',
  'common.black': 'MUI palette path (`theme.palette.common.black`) passed as a `color`/`sx` value',
};

/**
 * The declared shapes of a lookup whose key the call does not show. A call site
 * matching none of them fails: either make the key visible (a literal, a constant)
 * or declare the shape here with the reason its keys are (or are not) covered.
 */
const INDIRECT_LOOKUP_SHAPES: { name: string; pattern: RegExp; coverage: string }[] = [
  {
    name: 'key sent by the server',
    pattern: /^(?:state\.trigger_reason_i18n_key|entry\?\.unavailable_reason \?\? '[\w.]+')$/,
    coverage:
      'NOT covered: the backend names the key (REQ-018 trigger reason, REQ-045 widget gate); only the ' +
      'literal fallback after `??` is checked by layer 3',
  },
  {
    name: 'conditional between keys',
    pattern: /^[^?]+\?(?![.?])[\s\S]+:[\s\S]+$/,
    coverage: 'each branch is a key-shaped literal or template and is checked by layer 3',
  },
  {
    name: 'key variable or property',
    pattern: /^(?:[\w$]+(?:\?\.|\.))*[\w$]*(?:[kK]ey|I18nKey)$/,
    coverage: 'carries a key written as a literal elsewhere (config arrays, props), checked by layer 3',
  },
  {
    name: 'key table lookup',
    pattern: /^(?:[A-Z][A-Z0-9_]*|[a-z][\w$]*Keys)\[[^\]]+\](?:\s*\?\?\s*[\s\S]+)?$/,
    coverage: 'a `Record<…, key>` of key literals, checked by layer 3; the fallback after `??` too',
  },
  {
    name: 'key function',
    pattern: /^(?:errorKey|refusalKey)\([\s\S]*\)$|^quotaKey \?\? errorKey\(/,
    coverage: 'returns keys written as literals in its body (api/errors.ts, the refusal map), checked by layer 3',
  },
  {
    name: 'error key in state',
    pattern: /^(?:error|state\.message)(?:\s*\?\?\s*'errors\.generic')?$/,
    coverage: 'holds the result of `errorKey()` (api/errors.ts), whose keys are literals checked by layer 3',
  },
  {
    name: 'key-or-text passthrough',
    pattern: /^(?:label|description|crumb\.label)$/,
    coverage:
      'a prop that is a key or already-translated text, rendered with `defaultValue: label` or from ' +
      'key-literal props at every call site; not resolvable here',
  },
  {
    name: 'prefix handed in',
    pattern: /^`\$\{(?:base|listPrefix|empty|boundaryTexts)\}\.[\s\S]*`$/,
    coverage:
      'the head is a prop/parameter; the prefixes the callers pass are key-shaped literals checked by ' +
      'layer 3, the suffix is not checked against them',
  },
  {
    name: 'fallback array',
    pattern: /^\[`[\s\S]+`,[\s\S]+\]$/,
    coverage: 'i18next key-fallback array; the template head is checked by layer 4',
  },
];

function shapeOf(expression: string): string | null {
  return INDIRECT_LOOKUP_SHAPES.find((shape) => shape.pattern.test(expression))?.name ?? null;
}

/** All findings of layers 2–4 for one source, as `line: problem` strings. */
function undefinedKeys(source: string, index: KeyIndex, exported: ReadonlyMap<string, string>): string[] {
  const out: string[] = [];
  for (const usage of keyUsages(source, exported)) {
    if (usage.kind === 'static' && !index.resolves(usage.key)) out.push(`${usage.line}: t('${usage.key}')`);
    if (usage.kind === 'template' && !index.leadsSomewhere(usage.head)) out.push(`${usage.line}: ${usage.head}…`);
  }
  for (const literal of keyLiterals(source, NAMESPACES)) {
    if (!(literal.key in NOT_A_KEY) && !index.resolves(literal.key)) out.push(`${literal.line}: '${literal.key}'`);
  }
  for (const template of keyTemplates(source, NAMESPACES, exported)) {
    if (template.key !== undefined && !index.resolves(template.key)) out.push(`${template.line}: \`${template.key}\``);
    if (template.head !== undefined && !index.leadsSomewhere(template.head)) out.push(`${template.line}: \`${template.head}…\``);
  }
  return [...new Set(out)];
}

/**
 * I-05 — `t('pages.x', { defaultValue: '…' })` renders the fallback when the key is gone, so
 * neither the reader nor layer 2 notices. A RUNTIME key keeps its `defaultValue`: there it
 * is the deliberate fallback for a backend value the catalogue does not know yet (the raw
 * enum value instead of a raw key), and its static head is still checked by layer 4.
 */
function staticKeysWithDefault(source: string, exported: ReadonlyMap<string, string>): string[] {
  return keyUsages(source, exported).flatMap((usage) =>
    usage.kind === 'static' && usage.defaultValue ? [`${usage.line}: t('${usage.key}', { defaultValue })`] : [],
  );
}

function undeclaredIndirectLookups(source: string, exported: ReadonlyMap<string, string>): string[] {
  return keyUsages(source, exported)
    .filter((usage) => usage.kind === 'unverifiable' && shapeOf(usage.text) === null)
    .map((usage) => `${usage.line}: t(${usage.kind === 'unverifiable' ? usage.text : ''})`);
}

describe('i18n key catalogue (#3025 M14, I-01/I-02)', () => {
  it('scans the production tree and both full catalogues (nothing is empty)', () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(500);
    expect(Object.keys(SOURCES)).toContain('/src/components/layout/Breadcrumbs.tsx');
    expect(DE.size).toBeGreaterThan(5000);
    expect(NAMESPACES).toEqual(expect.arrayContaining(['common', 'pages', 'enums', 'glossary', 'errors']));
  });

  it('German and English define the same keys', () => {
    expect(parityGaps(DE, EN)).toEqual({ onlyA: [], onlyB: [] });
  });

  it('German and English use the same {{placeholders}} per key', () => {
    expect(placeholderMismatches(DE, EN)).toEqual([]);
  });

  it('every key the code names exists (static lookups, key-shaped literals, template heads)', () => {
    const offenders = Object.entries(SOURCES).flatMap(([file, source]) =>
      undefinedKeys(source, INDEX, EXPORTED).map((hit) => `${file}:${hit}`),
    );
    expect(offenders).toEqual([]);
  });

  it('a static key never carries a defaultValue, so a missing key stays visible (I-05)', () => {
    const offenders = Object.entries(SOURCES).flatMap(([file, source]) =>
      staticKeysWithDefault(source, EXPORTED).map((hit) => `${file}:${hit}`),
    );
    expect(offenders).toEqual([]);
  });

  it('every lookup whose key the call does not show has a declared shape', () => {
    const offenders = Object.entries(SOURCES).flatMap(([file, source]) =>
      undeclaredIndirectLookups(source, EXPORTED).map((hit) => `${file}:${hit}`),
    );
    expect(offenders).toEqual([]);
  });

  it('keeps every declared shape and non-key literal in use (no stale entries)', () => {
    const indirect = Object.values(SOURCES).flatMap((source) =>
      keyUsages(source, EXPORTED).flatMap((usage) => (usage.kind === 'unverifiable' ? [usage.text] : [])),
    );
    for (const shape of INDIRECT_LOOKUP_SHAPES) {
      expect(indirect.some((text) => shape.pattern.test(text)), shape.name).toBe(true);
    }
    const literals = new Set(Object.values(SOURCES).flatMap((source) => keyLiterals(source, NAMESPACES).map((l) => l.key)));
    for (const key of Object.keys(NOT_A_KEY)) {
      expect(literals.has(key), key).toBe(true);
      expect(INDEX.resolves(key), `${key} became a real key`).toBe(false);
    }
  });

  describe('the guard can fail (seeded fixtures)', () => {
    const catalog = flattenCatalog({
      common: { save: 'Speichern', item_one: '{{count}} Eintrag', item_other: '{{count}} Einträge' },
      pages: { x: { title: 'Titel', list: { a: 'A' } } },
      enums: { phaseName: { seedling: 'Keimling' } },
    });
    const index = createKeyIndex(catalog);
    const exported = new Map([['SHARED_PREFIX', 'pages.x']]);

    it('accepts leaves, plural families, branches and resolved constants', () => {
      const source = [
        "t('common.save');",
        "t('common.item', { count: 2 });",
        "t('pages.x.list', { returnObjects: true });",
        "const PREFIX = 'pages.x';",
        't(`${PREFIX}.title`);',
        't(`${SHARED_PREFIX}.title`);',
        't(`enums.phaseName.${phase}`);',
        '<Trans i18nKey="pages.x.title" />',
        "const columns = [{ labelKey: 'pages.x.list.a' }];",
      ].join('\n');
      expect(undefinedKeys(source, index, exported)).toEqual([]);
    });

    it('reports a seeded undefined static key', () => {
      expect(undefinedKeys("t('common.missing');", index, exported)).toContain("1: t('common.missing')");
    });

    it('reports an undefined key in a config literal, a constant template and a Trans', () => {
      const source = [
        "const cols = [{ labelKey: 'pages.x.nope' }];",
        "const PREFIX = 'pages.x';",
        't(`${PREFIX}.nope`);',
        '<Trans i18nKey="pages.x.gone" />',
      ].join('\n');
      expect(undefinedKeys(source, index, exported)).toEqual(
        expect.arrayContaining(["1: 'pages.x.nope'", "3: t('pages.x.nope')", "4: t('pages.x.gone')"]),
      );
    });

    it('reports a runtime key whose static head leads nowhere', () => {
      expect(undefinedKeys('t(`enums.phase.${phase}`);', index, exported)).toEqual(
        expect.arrayContaining(['1: enums.phase.…']),
      );
    });

    it('reports an indirect lookup that matches no declared shape', () => {
      expect(undeclaredIndirectLookups('t(computeSomething(x));', new Map())).toEqual([
        '1: t(computeSomething(x))',
      ]);
      expect(undeclaredIndirectLookups('t(def.labelKey); t(isEdit ? \'common.save\' : \'common.create\');', new Map())).toEqual([]);
    });

    it('reports a defaultValue on a static key, not on a runtime key or a nested call', () => {
      expect(staticKeysWithDefault("t('pages.x.title', { defaultValue: 'Titel' });", exported)).toEqual([
        "1: t('pages.x.title', { defaultValue })",
      ]);
      expect(
        staticKeysWithDefault(
          [
            't(`enums.phaseName.${phase}`, { defaultValue: phase });',
            "t('pages.x.title', { how: t(`enums.x.${v}`, { defaultValue: v }) });",
          ].join('\n'),
          exported,
        ),
      ).toEqual([]);
    });

    it('does not read comments', () => {
      expect(undefinedKeys("// t('common.missing')\n/* 'pages.gone' */", index, exported)).toEqual([]);
    });

    it('reports a seeded parity gap and a placeholder mismatch', () => {
      const de = flattenCatalog({ a: { b: 'x {{n}}', c: 'y' } });
      const en = flattenCatalog({ a: { b: 'x {{m}}' } });
      expect(parityGaps(de, en)).toEqual({ onlyA: ['a.c'], onlyB: [] });
      expect(placeholderMismatches(de, en)).toEqual(['a.b']);
    });
  });
});
