import { blankComments } from '../guards/jsxScan';

/**
 * Source-text helpers for the i18n key catalogue guard (#3025 M14, audit I-01/I-02).
 *
 * The guard answers two questions the type checker cannot: does every key the code
 * asks for exist, and does German have exactly the keys English has. It reads the
 * production sources as text (like every guard under `src/test/guards/`) and the
 * locale JSON as data. Everything here is pure so the test can run it against seeded
 * fixtures and prove it fails.
 *
 * What a key usage is, and how far each kind can be checked:
 *
 *  - **static** — `t('pages.x.y')`, `i18n.t("…")`, a template without `${}`, and
 *    `<Trans i18nKey="…">`. Checked fully: the key must exist.
 *  - **template** — `` t(`enums.phaseName.${phase}`) ``. Identifiers inside `${}` that
 *    name a string constant (declared in the file, or exported once anywhere in the
 *    tree) are substituted first, so `` t(`${PREFIX}.title`) `` is static again. What
 *    stays dynamic is checked up to its static head: `enums.phaseName.` must be a
 *    branch of the catalogue. The runtime value after it is not visible.
 *  - **unverifiable** — `t(labelKey)`, or a template whose head is unresolved
 *    (`` t(`${kind}.title`) ``). The scan cannot see what key that is. Those call
 *    sites are declared per file in the guard with the reason; a new one fails.
 *  - **key literal** — any string literal anywhere that starts with a catalogue
 *    namespace (`'pages.…'`, `'errors.…'`, `'enums.…'` …), e.g. a `labelKey` in a
 *    config array or the fallback of `errorKey(err, 'errors.…')`. This is what makes
 *    most `t(labelKey)` sites checkable after all: the key is written down somewhere.
 */

/** The flattened catalogue: `pages.x.y` -> the string. */
export type FlatCatalog = Map<string, string>;

export function flattenCatalog(
  node: Record<string, unknown>,
  prefix = '',
  out: FlatCatalog = new Map(),
): FlatCatalog {
  for (const [key, value] of Object.entries(node)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === 'object') {
      flattenCatalog(value as Record<string, unknown>, path, out);
    } else {
      out.set(path, String(value));
    }
  }
  return out;
}

/** i18next plural/ordinal suffixes — `count_one`, `count_other`, `place_ordinal_two`. */
const PLURAL_SUFFIX = /_(?:ordinal_)?(?:zero|one|two|few|many|other)$/;

export interface KeyIndex {
  /** The key resolves: a leaf, a plural family (`key_one`…), or a branch (`returnObjects`). */
  resolves(key: string): boolean;
  /** A translation string itself. */
  isLeaf(key: string): boolean;
  /** The base of a plural family (`key_one`, `key_other` …) — needs `count`. */
  isPluralBase(key: string): boolean;
  /** An object node — `t()` returns it only with `returnObjects: true`. */
  isBranch(key: string): boolean;
  /** Some key starts with `head` — the static head of a template key leads somewhere. */
  leadsSomewhere(head: string): boolean;
}

export function createKeyIndex(catalog: FlatCatalog): KeyIndex {
  const leaves = new Set(catalog.keys());
  const pluralBases = new Set<string>();
  const branches = new Set<string>();
  for (const key of leaves) {
    if (PLURAL_SUFFIX.test(key)) pluralBases.add(key.replace(PLURAL_SUFFIX, ''));
    const parts = key.split('.');
    for (let i = 1; i < parts.length; i += 1) branches.add(parts.slice(0, i).join('.'));
  }
  const sorted = [...leaves].sort();
  return {
    resolves: (key) => leaves.has(key) || pluralBases.has(key) || branches.has(key),
    isLeaf: (key) => leaves.has(key),
    isPluralBase: (key) => pluralBases.has(key),
    isBranch: (key) => branches.has(key),
    leadsSomewhere: (head) => {
      // Binary search for the first key >= head, then check the prefix.
      let lo = 0;
      let hi = sorted.length;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (sorted[mid] < head) lo = mid + 1;
        else hi = mid;
      }
      return lo < sorted.length && sorted[lo].startsWith(head);
    },
  };
}

/** `{{name}}` placeholders of one translation, sorted and de-duplicated. */
export function placeholders(text: string): string[] {
  return [...new Set([...text.matchAll(/\{\{\s*([\w.]+)[^}]*\}\}/g)].map((m) => m[1]))].sort();
}

/** Keys only one of two catalogues has. */
export function parityGaps(a: FlatCatalog, b: FlatCatalog): { onlyA: string[]; onlyB: string[] } {
  return {
    onlyA: [...a.keys()].filter((key) => !b.has(key)),
    onlyB: [...b.keys()].filter((key) => !a.has(key)),
  };
}

/** Keys present in both whose `{{placeholders}}` differ. */
export function placeholderMismatches(a: FlatCatalog, b: FlatCatalog): string[] {
  return [...a.entries()]
    .filter(([key, text]) => b.has(key) && placeholders(text).join() !== placeholders(b.get(key) ?? '').join())
    .map(([key]) => key);
}

/** One part of a template literal: static text, or the source of a `${}` expression. */
type TemplatePart = { text: string } | { expr: string };

/**
 * Read the template literal that starts at `source[start] === '`'`, with nested
 * templates and braces inside `${}`. Returns its parts and the index after the
 * closing backtick, or `null` when the literal does not close.
 */
function readTemplate(source: string, start: number): { parts: TemplatePart[]; end: number } | null {
  const parts: TemplatePart[] = [];
  let i = start + 1;
  let text = '';
  while (i < source.length) {
    const c = source[i];
    if (c === '\\') {
      text += source.slice(i, i + 2);
      i += 2;
    } else if (c === '`') {
      if (text) parts.push({ text });
      return { parts, end: i + 1 };
    } else if (c === '$' && source[i + 1] === '{') {
      if (text) parts.push({ text });
      text = '';
      let depth = 1;
      let j = i + 2;
      while (j < source.length && depth > 0) {
        const d = source[j];
        if (d === '`') {
          const inner = readTemplate(source, j);
          if (!inner) return null;
          j = inner.end;
          continue;
        }
        if (d === "'" || d === '"') {
          j += 1;
          while (j < source.length && source[j] !== d && source[j] !== '\n') j += source[j] === '\\' ? 2 : 1;
        } else if (d === '{') depth += 1;
        else if (d === '}') depth -= 1;
        j += 1;
      }
      parts.push({ expr: source.slice(i + 2, j - 1).trim() });
      i = j;
    } else {
      text += c;
      i += 1;
    }
  }
  return null;
}

const IDENTIFIER = /^[A-Za-z_$][\w$]*$/;

/**
 * Split a top-level conditional `test ? a : b` (nested conditionals in `b` stay in `b`).
 * `?.` and `??` are not the operator; strings, templates and brackets are skipped.
 * `null` when the expression is not a conditional at its top level.
 */
export function splitConditional(expression: string): { test: string; consequent: string; alternate: string } | null {
  let depth = 0;
  let question = -1;
  let pending = 0;
  for (let i = 0; i < expression.length; i += 1) {
    const c = expression[i];
    if (c === "'" || c === '"') {
      i += 1;
      while (i < expression.length && expression[i] !== c) i += expression[i] === '\\' ? 2 : 1;
      continue;
    }
    if (c === '`') {
      const template = readTemplate(expression, i);
      if (!template) return null;
      i = template.end - 1;
      continue;
    }
    if (c === '(' || c === '[' || c === '{') depth += 1;
    else if (c === ')' || c === ']' || c === '}') depth -= 1;
    else if (depth === 0 && c === '?') {
      const next = expression[i + 1];
      if (next === '.' || next === '?') {
        i += 1;
        continue;
      }
      if (question === -1) question = i;
      pending += 1;
    } else if (depth === 0 && c === ':' && question !== -1) {
      pending -= 1;
      if (pending === 0) {
        return {
          test: expression.slice(0, question).trim(),
          consequent: expression.slice(question + 1, i).trim(),
          alternate: expression.slice(i + 1).trim(),
        };
      }
    }
  }
  return null;
}

/** String constants: `const NAME = 'x'` or `` const NAME = `${OTHER}.y` `` (resolved against `known`). */
function declaredConstants(source: string, known: ReadonlyMap<string, string>, exportedOnly: boolean): Map<string, string> {
  const found = new Map<string, string>();
  const declaration = exportedOnly
    ? /\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*(?::\s*string\s*)?=\s*/g
    : /\bconst\s+([A-Za-z_$][\w$]*)\s*(?::\s*string\s*)?=\s*/g;
  // Two passes so a constant built from a later one in the same file still resolves.
  for (let pass = 0; pass < 2; pass += 1) {
    for (const match of source.matchAll(declaration)) {
      const at = (match.index ?? 0) + match[0].length;
      const quote = source[at];
      let value: string | null = null;
      if (quote === "'" || quote === '"') {
        const close = source.indexOf(quote, at + 1);
        const literal = source.slice(at + 1, close);
        if (close > at && !literal.includes('\n')) value = literal;
      } else if (quote === '`') {
        const template = readTemplate(source, at);
        if (template) value = resolveParts(template.parts, (name) => found.get(name) ?? known.get(name));
      }
      if (value !== null) found.set(match[1], value);
    }
  }
  return found;
}

function resolveParts(parts: TemplatePart[], lookup: (name: string) => string | undefined): string | null {
  let out = '';
  for (const part of parts) {
    if ('text' in part) out += part.text;
    else if (IDENTIFIER.test(part.expr) && lookup(part.expr) !== undefined) out += lookup(part.expr);
    else return null;
  }
  return out;
}

/**
 * Exported string constants of the whole tree, by name — only names exported by
 * exactly one file (a second `PREFIX` elsewhere would make the lookup a guess).
 */
export function exportedConstants(sources: Record<string, string>): Map<string, string> {
  const byName = new Map<string, string[]>();
  for (const source of Object.values(sources)) {
    for (const [name, value] of declaredConstants(blankComments(source), new Map(), true)) {
      byName.set(name, [...(byName.get(name) ?? []), value]);
    }
  }
  const unique = new Map<string, string>();
  for (const [name, values] of byName) if (values.length === 1) unique.set(name, values[0]);
  return unique;
}

export type KeyUsage =
  | {
      kind: 'static';
      line: number;
      key: string;
      /** The call's own options carry a `defaultValue` / `count` / `returnObjects: true`. */
      defaultValue: boolean;
      count: boolean;
      returnObjects: boolean;
      /** `<Trans i18nKey>` rather than a `t()` call (its options are props, not read). */
      trans?: boolean;
    }
  | { kind: 'template'; line: number; head: string; text: string }
  | { kind: 'unverifiable'; line: number; text: string };

/**
 * The source of the first call argument starting at `start`: up to the first comma or
 * closing paren at nesting depth 0, with strings and templates skipped. Whitespace is
 * collapsed so a multi-line argument reads as one line.
 */
function firstArgument(source: string, start: number): string {
  let depth = 0;
  let i = start;
  while (i < source.length) {
    const c = source[i];
    if (c === '`') {
      const template = readTemplate(source, i);
      if (!template) break;
      i = template.end;
      continue;
    }
    if (c === "'" || c === '"') {
      i += 1;
      while (i < source.length && source[i] !== c && source[i] !== '\n') i += source[i] === '\\' ? 2 : 1;
    } else if (c === '(' || c === '[' || c === '{') depth += 1;
    else if (c === ')' || c === ']' || c === '}') {
      if (depth === 0) break;
      depth -= 1;
    } else if (c === ',' && depth === 0) break;
    i += 1;
  }
  return source.slice(start, i).replace(/\s+/g, ' ').trim();
}

/**
 * The OWN options object after a key (`t('k', { … })`, `after` is the index behind the key),
 * with nested calls/groups dropped so `how: t(x, { defaultValue })` is not read as this
 * call's own. '' when the call has no options.
 */
function ownOptions(source: string, after: number): string {
  let i = after;
  while (/\s/.test(source[i] ?? '')) i += 1;
  if (source[i] !== ',') return '';
  let options = firstArgument(source, i + 1);
  let previous = '';
  while (previous !== options) {
    previous = options;
    options = options.replace(/\([^()]*\)/g, '#');
  }
  return options;
}

function optionFlags(source: string, after: number): { defaultValue: boolean; count: boolean; returnObjects: boolean } {
  const options = ownOptions(source, after);
  return {
    defaultValue: /\bdefaultValue\s*:/.test(options),
    count: /(?:^|[{,\s])count\s*[:,}]/.test(options),
    returnObjects: /\breturnObjects\s*:\s*true\b/.test(options),
  };
}

function lineAt(source: string, index: number): number {
  return source.slice(0, index).split('\n').length;
}

/**
 * Every translation lookup in one source file. `exported` are the tree-wide string
 * constants from {@link exportedConstants}.
 */
export function keyUsages(rawSource: string, exported: ReadonlyMap<string, string> = new Map()): KeyUsage[] {
  const source = blankComments(rawSource);
  const local = declaredConstants(source, exported, false);
  const lookup = (name: string) => local.get(name) ?? exported.get(name);
  const usages: KeyUsage[] = [];

  for (const match of source.matchAll(/(?<![\w$.])(?:i18n(?:ext)?\.)?t\(\s*/g)) {
    const at = (match.index ?? 0) + match[0].length;
    const line = lineAt(source, match.index ?? 0);
    const quote = source[at];
    if (quote === "'" || quote === '"') {
      const close = source.indexOf(quote, at + 1);
      if (close > at) {
        const key = source.slice(at + 1, close);
        usages.push({ kind: 'static', line, key, ...optionFlags(source, close + 1) });
      }
      continue;
    }
    if (quote === '`') {
      const template = readTemplate(source, at);
      if (!template) continue;
      const text = source.slice(at, template.end);
      const resolved = resolveParts(template.parts, lookup);
      if (resolved !== null) {
        usages.push({ kind: 'static', line, key: resolved, ...optionFlags(source, template.end) });
        continue;
      }
      // The static head: the parts up to the first expression that does not resolve.
      let head = '';
      for (const part of template.parts) {
        if ('text' in part) head += part.text;
        else if (IDENTIFIER.test(part.expr) && lookup(part.expr) !== undefined) head += lookup(part.expr);
        else break;
      }
      usages.push(head ? { kind: 'template', line, head, text } : { kind: 'unverifiable', line, text });
      continue;
    }
    // `t()` with no argument is not a lookup; an identifier, a member/call expression
    // or a conditional is a key the scan cannot read from this call alone.
    if (source[at] === ')') continue;
    usages.push({ kind: 'unverifiable', line, text: firstArgument(source, at) });
  }

  for (const match of source.matchAll(/\bi18nKey=(?:"([^"]+)"|\{\s*'([^']+)'\s*\}|\{\s*"([^"]+)"\s*\})/g)) {
    usages.push({
      kind: 'static',
      line: lineAt(source, match.index ?? 0),
      key: match[1] ?? match[2] ?? match[3],
      defaultValue: false,
      count: false,
      returnObjects: false,
      trans: true,
    });
  }
  return usages;
}

/**
 * String literals shaped like a catalogue key (`'pages.x.y'`, `"errors.z"`) in one
 * source — wherever they are written, not only inside `t()`. `namespaces` are the
 * top-level keys of the catalogue.
 */
export function keyLiterals(rawSource: string, namespaces: readonly string[]): { line: number; key: string }[] {
  const source = blankComments(rawSource);
  const pattern = new RegExp(`(['"\`])((?:${namespaces.join('|')})\\.[A-Za-z0-9_.-]+)\\1`, 'g');
  return [...source.matchAll(pattern)].map((match) => ({
    line: lineAt(source, match.index ?? 0),
    // `'enums.phaseName.'` is a prefix someone appends to; it must name a branch.
    key: match[2].replace(/\.$/, ''),
  }));
}

/**
 * Template literals shaped like a catalogue key after the string constants are
 * substituted — `` `${PREFIX}.title` `` with `PREFIX = 'pages.x'` is `pages.x.title`.
 * A fully resolved one is a `key`; one with a runtime part keeps its static `head`
 * (`` `enums.phaseName.${phase}` `` -> `enums.phaseName.`). Covers the branches of
 * `t(cond ? `${PREFIX}.a` : `${PREFIX}.b`)`, which the call scan cannot read.
 */
export function keyTemplates(
  rawSource: string,
  namespaces: readonly string[],
  exported: ReadonlyMap<string, string> = new Map(),
): { line: number; key?: string; head?: string }[] {
  const source = blankComments(rawSource);
  const local = declaredConstants(source, exported, false);
  const lookup = (name: string) => local.get(name) ?? exported.get(name);
  const shaped = new RegExp(`^(?:${namespaces.join('|')})\\.`);
  const found: { line: number; key?: string; head?: string }[] = [];
  let i = 0;
  while (i < source.length) {
    const c = source[i];
    if (c === "'" || c === '"') {
      i += 1;
      while (i < source.length && source[i] !== c && source[i] !== '\n') i += source[i] === '\\' ? 2 : 1;
      i += 1;
      continue;
    }
    if (c !== '`') {
      i += 1;
      continue;
    }
    const template = readTemplate(source, i);
    if (!template) break;
    const line = lineAt(source, i);
    // Only templates with an expression; a plain one is already a quoted-style literal.
    if (template.parts.some((part) => 'expr' in part)) {
      const resolved = resolveParts(template.parts, lookup);
      if (resolved !== null) {
        if (shaped.test(resolved) && /^[\w.-]+$/.test(resolved)) found.push({ line, key: resolved.replace(/\.$/, '') });
      } else {
        let head = '';
        for (const part of template.parts) {
          if ('text' in part) head += part.text;
          else if (IDENTIFIER.test(part.expr) && lookup(part.expr) !== undefined) head += lookup(part.expr);
          else break;
        }
        if (shaped.test(head) && /^[\w.-]+$/.test(head)) found.push({ line, head });
      }
    }
    // A template nested in another one's `${}` is not visited (a `t()` there is
    // still seen by `keyUsages`).
    i = template.end;
  }
  return found;
}
