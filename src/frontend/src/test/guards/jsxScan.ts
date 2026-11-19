/**
 * Source-text helpers for the UI-NFR-022 testability guard (#3024).
 *
 * The guard reads `.tsx` files as text, the way the other guards in this
 * directory do (`import.meta.glob(..., { query: '?raw' })`). A plain regex over
 * the raw text is not enough for JSX opening tags: an attribute value such as
 * `onClick={() => x > 0}` or a comment like `// see <Controller disabled>`
 * contains a `>` that is not the end of the tag, and a commented-out
 * `<Dialog …>` must not count at all. These helpers do the minimum lexing that
 * makes the tag boundaries trustworthy:
 *
 * - comments are blanked (same length, newlines kept, so line numbers stay true);
 * - string, template and brace nesting is tracked while looking for a tag's end.
 *
 * Known limit: JSX text with an unmatched quote (`<p>Don't</p>`) is read as the
 * start of a string. Strings cannot span lines in JS, so the lexer ends such a
 * "string" at the next newline — the damage stays on that one line.
 */

/** One JSX opening tag found in a source file. */
export interface OpeningTag {
  /** Element name as written (`Dialog`, `FormDialog`, `MenuItem`). */
  name: string;
  /** The whole opening tag, `<Dialog … >` or `<Switch … />`, comments blanked. */
  text: string;
  /** 1-based line of the `<`. */
  line: number;
}

/**
 * The source with every `//` and `/* *\/` comment replaced by spaces.
 *
 * Strings and template literals are skipped so `'http://x'` is not a comment.
 * Length and newlines are preserved, so offsets and line numbers still match the
 * original file.
 */
export function blankComments(source: string): string {
  const out = source.split('');
  let i = 0;
  const n = source.length;
  // Stack of template-literal brace depths: inside `${ … }` we are back in code.
  const templateBraces: number[] = [];
  let braceDepth = 0;

  const skipQuoted = (quote: string) => {
    i += 1;
    while (i < n && source[i] !== quote && source[i] !== '\n') {
      if (source[i] === '\\') i += 1;
      i += 1;
    }
    i += 1;
  };

  const skipTemplate = () => {
    // Called with source[i] === '`' or when resuming after `}` of `${}`.
    i += 1;
    while (i < n) {
      const c = source[i];
      if (c === '\\') {
        i += 2;
        continue;
      }
      if (c === '`') {
        i += 1;
        return;
      }
      if (c === '$' && source[i + 1] === '{') {
        i += 2;
        templateBraces.push(braceDepth);
        braceDepth += 1;
        return;
      }
      i += 1;
    }
  };

  while (i < n) {
    const c = source[i];
    const next = source[i + 1];
    if (c === '/' && next === '/') {
      while (i < n && source[i] !== '\n') {
        out[i] = ' ';
        i += 1;
      }
      continue;
    }
    if (c === '/' && next === '*') {
      while (i < n && !(source[i] === '*' && source[i + 1] === '/')) {
        if (source[i] !== '\n') out[i] = ' ';
        i += 1;
      }
      if (i < n) {
        out[i] = ' ';
        out[i + 1] = ' ';
        i += 2;
      }
      continue;
    }
    if (c === '"' || c === "'") {
      skipQuoted(c);
      continue;
    }
    if (c === '`') {
      skipTemplate();
      continue;
    }
    if (c === '{') {
      braceDepth += 1;
    } else if (c === '}') {
      braceDepth -= 1;
      if (templateBraces.length && templateBraces[templateBraces.length - 1] === braceDepth) {
        templateBraces.pop();
        // Resume the template literal right after the closing brace.
        skipTemplate();
        continue;
      }
    }
    i += 1;
  }
  return out.join('');
}

/**
 * End offset (exclusive) of the opening tag starting at `start` (`<`), or -1.
 *
 * Attribute expressions `{…}` are followed by brace depth, with strings and
 * template literals inside them skipped; quoted attribute values are skipped at
 * depth 0. The tag ends at the first `>` outside all of them.
 */
function tagEnd(code: string, start: number): number {
  let i = start + 1;
  let depth = 0;
  const n = code.length;
  while (i < n) {
    const c = code[i];
    if (c === '"' || c === "'") {
      const quote = c;
      i += 1;
      while (i < n && code[i] !== quote && code[i] !== '\n') {
        if (code[i] === '\\' && depth > 0) i += 1;
        i += 1;
      }
      i += 1;
      continue;
    }
    if (c === '`' && depth > 0) {
      i += 1;
      let inner = 0;
      while (i < n) {
        if (code[i] === '\\') {
          i += 2;
          continue;
        }
        if (code[i] === '$' && code[i + 1] === '{') {
          inner += 1;
          i += 2;
          continue;
        }
        if (code[i] === '}' && inner > 0) {
          inner -= 1;
          i += 1;
          continue;
        }
        if (code[i] === '`' && inner === 0) break;
        i += 1;
      }
      i += 1;
      continue;
    }
    if (c === '{') depth += 1;
    else if (c === '}') depth -= 1;
    else if (c === '>' && depth === 0) return i + 1;
    i += 1;
  }
  return -1;
}

/**
 * Every JSX opening tag of the given element names in `source`.
 *
 * Matches `<Name` followed by whitespace, `>` or `/` — so `<DialogTitle` is not a
 * `Dialog`, and a generic like `useState<Dialog>` (no attribute position) is not
 * mistaken for a tag unless it is literally followed by whitespace.
 */
export function openingTags(source: string, names: readonly string[]): OpeningTag[] {
  const code = blankComments(source);
  const pattern = new RegExp(`<(${names.join('|')})(?=[\\s>/])`, 'g');
  const tags: OpeningTag[] = [];
  for (const match of code.matchAll(pattern)) {
    const start = match.index ?? 0;
    const end = tagEnd(code, start);
    if (end < 0) continue;
    tags.push({
      name: match[1],
      text: code.slice(start, end),
      line: code.slice(0, start).split('\n').length,
    });
  }
  return tags;
}

/**
 * Value of a JSX attribute in an opening tag: the literal without quotes for
 * `attr="x"`, the expression text without the outer braces for `attr={x}`, or
 * `null` when the attribute is absent.
 */
export function attributeValue(tag: string, attribute: string): string | null {
  const at = new RegExp(`\\s${attribute.replace(/[-]/g, '\\-')}=`).exec(tag);
  if (!at) return null;
  let i = at.index + at[0].length;
  const open = tag[i];
  if (open === '"' || open === "'") {
    const close = tag.indexOf(open, i + 1);
    return close < 0 ? null : tag.slice(i + 1, close);
  }
  if (open !== '{') return null;
  let depth = 0;
  const start = i;
  for (; i < tag.length; i += 1) {
    if (tag[i] === '{') depth += 1;
    else if (tag[i] === '}') {
      depth -= 1;
      if (depth === 0) return tag.slice(start + 1, i).trim();
    }
  }
  return null;
}

/** Whether the tag sets a `data-testid` — as a JSX attribute or inside `slotProps`/`inputProps`. */
export function hasTestId(tag: string): boolean {
  return /\sdata-testid=/.test(tag) || /['"]data-testid['"]\s*:/.test(tag);
}

/**
 * Whether the element the tag's `aria-labelledby` points at is defined in the
 * same file: a literal `aria-labelledby="x"` needs an `id="x"`, an expression
 * `aria-labelledby={expr}` needs an `id={expr}` with the same expression text.
 *
 * Catches the silent failure of hand-paired id strings: a typo in either half
 * leaves the dialog unnamed and no test notices.
 */
export function labelledByResolves(tag: string, fileSource: string): boolean {
  const value = attributeValue(tag, 'aria-labelledby');
  if (value === null) return false;
  const code = blankComments(fileSource);
  const literal = /\saria-labelledby="/.test(tag);
  if (literal) {
    return new RegExp(`\\sid="${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`).test(code);
  }
  const normalise = (s: string) => s.replace(/\s+/g, '');
  const wanted = normalise(value);
  for (const match of code.matchAll(/\sid=\{/g)) {
    const tagStart = (match.index ?? 0) - 1;
    const text = code.slice(tagStart, tagStart + 400);
    const id = attributeValue(text, 'id');
    if (id !== null && normalise(id) === wanted) return true;
  }
  return false;
}

/** Line numbers (1-based) at which `pattern` matches the comment-blanked source. */
export function matchLines(source: string, pattern: RegExp): number[] {
  const code = blankComments(source);
  const global = new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`);
  return [...code.matchAll(global)].map((m) => code.slice(0, m.index ?? 0).split('\n').length);
}
