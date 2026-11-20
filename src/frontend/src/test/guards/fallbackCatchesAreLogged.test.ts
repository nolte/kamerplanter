import { describe, expect, it } from 'vitest';
import ts from 'typescript';

/**
 * #3037 — a failed load must not pass for an empty one.
 *
 * `swallowedErrorsAreLogged` covers handlers that drop an error outright. This
 * guard covers the other half, the commonest "empty on error" shape: a handler
 * that answers a failure with a **fallback value** the caller renders as data —
 * `.catch(() => [])`, `.catch(() => null)`, `.catch(() => ({ plan: null }))`,
 * `catch { setX([]) }`, `.catch(() => { if (!stale()) setX(null); })`,
 * `.catch(noop)`. A failed plan read then shows "no plan assigned" with an
 * assign button, a failed site list an empty picker.
 *
 * **The rule.** Such a handler must carry **both** a comment saying why the
 * fallback is right here and a log call (`captureHandledError(...)` or
 * `console.*`). Better still, it does something else — sets an error state the
 * page renders with a retry — and is then out of scope.
 *
 * **What counts as a fallback handler.**
 * - a `.catch(cb)` whose callback returns a fallback value (`null`, `false`,
 *   `0`, `''`, `[]`, `new Map()`/`new Set()`, an object literal of fallbacks) or
 *   only calls `setX(<fallback>)`, possibly behind `if (...)` guards;
 * - a `.catch(noop)`-style identifier (`noop`, `ignore…`, `swallow…`);
 * - a `catch` clause that only calls `setX(<fallback>)`, or that only returns
 *   a fallback **after an `await`** in its `try`. A synchronous
 *   `try { return JSON.parse(raw) } catch { return null }` is a parser, not a
 *   load, and is left alone.
 *
 * Log calls and bare `if (cond) return;` guards are neutral. A handler that is
 * empty or returns `undefined` is `swallowedErrorsAreLogged`'s business.
 *
 * **The allowlist** names the files that still fall back silently, with a count
 * and one reason each. It may only shrink: a file whose count rises fails, and a
 * file whose count falls below its entry fails too, so the entry is lowered with
 * the fix instead of leaving headroom.
 *
 * The detector is exercised against fixtures in both directions at the end of
 * this file, including the shape that motivated it.
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

const LOG_CALL = /\b(captureHandledError|console\.(warn|error|info|debug|log))\s*\(/;
const COMMENT = /\/\/|\/\*/;
const NOOP_NAME = /^(noop|ignore\w*|swallow\w*)$/i;

function unwrap(expression: ts.Expression): ts.Expression {
  let current = expression;
  while (
    ts.isParenthesizedExpression(current) ||
    ts.isAsExpression(current) ||
    ts.isSatisfiesExpression(current) ||
    ts.isTypeAssertionExpression(current) ||
    ts.isNonNullExpression(current)
  ) {
    current = current.expression;
  }
  return current;
}

/** `null`, `false`, `0`, `''`, `[]`, `new Map()`, `{ plan: null }` — a value that reads as "nothing". */
function isFallbackValue(expression: ts.Expression): boolean {
  const e = unwrap(expression);
  if (e.kind === ts.SyntaxKind.NullKeyword || e.kind === ts.SyntaxKind.FalseKeyword) return true;
  if (ts.isIdentifier(e) && e.text === 'undefined') return true;
  if (ts.isNumericLiteral(e) && e.text === '0') return true;
  if ((ts.isStringLiteral(e) || ts.isNoSubstitutionTemplateLiteral(e)) && e.text === '') return true;
  if (ts.isArrayLiteralExpression(e)) return e.elements.length === 0;
  if (ts.isObjectLiteralExpression(e)) {
    return e.properties.every((p) => ts.isPropertyAssignment(p) && isFallbackValue(p.initializer));
  }
  if (ts.isNewExpression(e) && ts.isIdentifier(e.expression) && /^(Map|Set)$/.test(e.expression.text)) {
    return (e.arguments ?? []).length === 0;
  }
  return false;
}

/** `setX(<fallback>)` — a state setter writing "nothing". */
function isFallbackSet(expression: ts.Expression): boolean {
  const e = unwrap(expression);
  return (
    ts.isCallExpression(e) &&
    ts.isIdentifier(e.expression) &&
    /^set[A-Z]/.test(e.expression.text) &&
    e.arguments.length === 1 &&
    isFallbackValue(e.arguments[0])
  );
}

type StatementKind = 'neutral' | 'set' | 'return' | 'other';

function kindOf(statement: ts.Statement, source: ts.SourceFile): StatementKind {
  if (
    ts.isExpressionStatement(statement) &&
    ts.isCallExpression(statement.expression) &&
    LOG_CALL.test(statement.getText(source))
  ) {
    return 'neutral';
  }
  if (
    ts.isIfStatement(statement) &&
    !statement.elseStatement &&
    ts.isReturnStatement(statement.thenStatement) &&
    !statement.thenStatement.expression
  ) {
    return 'neutral';
  }
  if (ts.isExpressionStatement(statement) && isFallbackSet(statement.expression)) return 'set';
  if (ts.isReturnStatement(statement) && statement.expression && isFallbackValue(statement.expression)) {
    return 'return';
  }
  if (ts.isIfStatement(statement) && !statement.elseStatement) {
    const inner = ts.isBlock(statement.thenStatement)
      ? [...statement.thenStatement.statements]
      : [statement.thenStatement];
    const kinds = inner.map((s) => kindOf(s, source));
    if (inner.length > 0 && kinds.every((k) => k === 'set' || k === 'return')) {
      return kinds.includes('set') ? 'set' : 'return';
    }
  }
  return 'other';
}

/** Whether `node` awaits something itself (nested functions are not looked into). */
function containsAwait(node: ts.Node): boolean {
  let found = false;
  const visit = (child: ts.Node) => {
    if (found) return;
    if (ts.isAwaitExpression(child)) {
      found = true;
      return;
    }
    if (ts.isFunctionLike(child)) return;
    ts.forEachChild(child, visit);
  };
  visit(node);
  return found;
}

function blockFallsBack(block: ts.Block, source: ts.SourceFile, asyncTry: boolean): boolean {
  const kinds = block.statements.map((s) => kindOf(s, source));
  if (kinds.includes('other')) return false;
  if (kinds.includes('set')) return true;
  return kinds.includes('return') && asyncTry;
}

interface FallbackFinding {
  line: number;
  kind: 'catch' | '.catch' | '.catch(noop)';
}

/** Every fallback-returning handler of `code` that lacks the comment or the log call. */
function findUnloggedFallbacks(code: string, fileName = 'x.tsx'): FallbackFinding[] {
  const source = ts.createSourceFile(
    fileName,
    code,
    ts.ScriptTarget.Latest,
    true,
    fileName.endsWith('x') ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const findings: FallbackFinding[] = [];
  const report = (node: ts.Node, kind: FallbackFinding['kind'], text: string | null) => {
    if (text !== null && COMMENT.test(text) && LOG_CALL.test(text)) return;
    findings.push({ line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1, kind });
  };

  const visit = (node: ts.Node) => {
    if (ts.isCatchClause(node) && ts.isTryStatement(node.parent)) {
      if (blockFallsBack(node.block, source, containsAwait(node.parent.tryBlock))) {
        // `getFullText` keeps the comments inside the braces.
        report(node, 'catch', node.block.getFullText(source));
      }
    } else if (
      ts.isCallExpression(node) &&
      ts.isPropertyAccessExpression(node.expression) &&
      node.expression.name.text === 'catch' &&
      node.arguments.length === 1
    ) {
      const handler = node.arguments[0];
      if (ts.isArrowFunction(handler) || ts.isFunctionExpression(handler)) {
        const body = handler.body;
        const fallsBack = ts.isBlock(body)
          ? blockFallsBack(body, source, true)
          : isFallbackSet(body) ||
            (isFallbackValue(body) && !(ts.isIdentifier(unwrap(body)) && (unwrap(body) as ts.Identifier).text === 'undefined'));
        if (fallsBack) report(node, '.catch', handler.getFullText(source));
      } else if (ts.isIdentifier(handler) && NOOP_NAME.test(handler.text)) {
        report(node, '.catch(noop)', null);
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return findings;
}

/**
 * Files that still fall back silently, with how many handlers and why. Shrinks only — see the header.
 *
 * - **deliberate** — best-effort work whose fallback is the documented answer
 *   (offline storage, a display-only hint, a clipboard refusal the caller reports).
 * - **open** — a load whose failure still reads as "none"; the reason names what
 *   is missing before it can show an error with a retry.
 */
const ALLOWLIST: Readonly<Record<string, { count: number; reason: string }>> = {
  '/src/components/admin/PestRecognitionAdminCard.tsx': {
    count: 1,
    reason:
      "open: a class's preview images read a failed load as 'no images'; the accordion row has no error slot yet",
  },
  '/src/components/pests/PestImageGallery.tsx': {
    count: 1,
    reason:
      "open: the pest gallery reads a failed load as 'no images'; it needs an error state with retry",
  },
  '/src/features/gardenPlanner/offline/planCache.ts': {
    count: 2,
    reason:
      'deliberate: the offline plan cache is best effort (IndexedDB unavailable, quota, private mode); a miss falls back to the network read',
  },
  '/src/features/gardenPlanner/offline/queue.ts': {
    count: 8,
    reason:
      "deliberate: without IndexedDB the write queue degrades to 'no queue'; null/0/false are the documented 'not done' answers its callers act on",
  },
  '/src/features/gardenPlanner/season/seasonApi.ts': {
    count: 1,
    reason:
      'deliberate: display-only rotation hint (GP-API-039, documented on the function); an aborted or failed read gives no hint, never an error',
  },
  '/src/main.tsx': {
    count: 1,
    reason:
      'deliberate: the app mounts even if error tracking cannot start; there is nothing to report the failure to',
  },
  '/src/pages/durchlaeufe/BatchPhaseTransitionDialog.tsx': {
    count: 1,
    reason:
      'open: legacy LifecycleConfig fallback — a 404 (species without lifecycle) is the normal empty case and must be told apart from a failure first',
  },
  '/src/pages/pflanzen/LifecycleConfigSection.tsx': {
    count: 1,
    reason:
      'open: legacy LifecycleConfig read — a 404 (species without lifecycle) is the normal empty case and must be told apart from a failure first',
  },
  '/src/pages/pflanzen/PlantPhaseTimeline.tsx': {
    count: 1,
    reason:
      'open: legacy LifecycleConfig fallback — a 404 (species without lifecycle) is the normal empty case and must be told apart from a failure first',
  },
  '/src/pages/pflanzen/ProfilesSection.tsx': {
    count: 2,
    reason:
      'open: requirement/nutrient profiles answer 404 when none is set; a failure must be told apart from that before the section can show an error',
  },
  '/src/pages/pflege/components/SpringReturnAssistant.tsx': {
    count: 1,
    reason:
      'open: a failed profile read hides the spring-return list as if nothing were overwintered; the assistant card has no error slot yet',
  },
  '/src/pages/stammdaten/ReferenceImageCuration.tsx': {
    count: 1,
    reason:
      "open: the curation grid reads a failed load as 'no images'; it needs an error state with retry",
  },
  '/src/pages/tenants/TenantSettingsPage.tsx': {
    count: 1,
    reason:
      "deliberate: a clipboard refusal (permission, insecure context) returns false and the caller shows 'copy failed'",
  },
};

function measure(): Map<string, number> {
  const counts = new Map<string, number>();
  for (const [path, code] of Object.entries(SOURCES)) {
    if (!isProductionSource(path)) continue;
    const findings = findUnloggedFallbacks(code, path);
    if (findings.length > 0) counts.set(path, findings.length);
  }
  return counts;
}

describe('fallback-returning catches carry a reason and a log call (#3037)', () => {
  const counts = measure();

  it('no file has more silent fallbacks than its allowlist entry permits', () => {
    const over = [...counts]
      .filter(([path, count]) => count > (ALLOWLIST[path]?.count ?? 0))
      .map(([path, count]) => {
        const lines = findUnloggedFallbacks(SOURCES[path], path).map((f) => f.line).join(', ');
        return `${path}: ${count} > ${ALLOWLIST[path]?.count ?? 0} (lines ${lines})`;
      });
    expect(over).toEqual([]);
  });

  it('the allowlist has no stale headroom — lower the entry with the fix', () => {
    const stale = Object.entries(ALLOWLIST)
      .filter(([path, entry]) => (counts.get(path) ?? 0) < entry.count)
      .map(([path, entry]) => `${path}: ${counts.get(path) ?? 0} < ${entry.count}`);
    expect(stale).toEqual([]);
  });

  it('every allowlist entry gives a reason', () => {
    const missing = Object.entries(ALLOWLIST)
      .filter(([, entry]) => !/^(deliberate|open): .{20,}/.test(entry.reason))
      .map(([path]) => path);
    expect(missing).toEqual([]);
  });

  it('scans a realistic share of the source tree', () => {
    const scanned = Object.keys(SOURCES).filter(isProductionSource);
    expect(scanned.length).toBeGreaterThan(500);
  });
});

describe('findUnloggedFallbacks — fixtures', () => {
  const FLAGGED: [string, string][] = [
    [
      // Verbatim from PlantingRunDetailPage before #3037 — the shape that motivated this guard.
      'the PlantingRunDetailPage plan leg',
      'async function f() {\n  const [planResult] = await Promise.all([\n    runApi.getRunNutrientPlan(key).catch(() => ({ plan: null })),\n  ]);\n}',
    ],
    ['a .catch returning an empty array', 'p.catch(() => []);'],
    ['a .catch returning a typed empty array', 'p.catch(() => [] as Item[]);'],
    ['a .catch returning null', 'p.catch(() => null);'],
    ['a .catch returning false', 'p.catch(() => false);'],
    ['a .catch returning an empty Map', 'p.catch(() => new Map());'],
    ['a .catch setting an empty list', 'p.catch(() => setItems([]));'],
    ['a guarded setter in a .catch block', 'p.catch(() => { if (!stale()) setItems([]); });'],
    ['a setter after a bare-return guard', 'p.catch(() => { if (cancelled) return; setItem(null); });'],
    ['a .catch(noop)', 'p.catch(noop);'],
    ['a catch clause setting an empty list', 'try { f(); } catch { setItems([]); }'],
    ['an async catch clause returning a fallback', 'async function f() { try { return await g(); } catch { return []; } }'],
    ['a comment without a log call', 'p.catch(() => {\n  // fine\n  return [];\n});'],
    ['a log call without a comment', 'p.catch((e) => { captureHandledError(e); return []; });'],
  ];
  const ACCEPTED: [string, string][] = [
    ['a commented, logged fallback', 'p.catch((e) => {\n  // labels only\n  captureHandledError(e);\n  return [];\n});'],
    ['a commented, logged catch clause', 'try { f(); } catch (e) {\n  // best effort\n  console.warn(e);\n  setItems([]);\n}'],
    ['a handler that sets an error state', 'p.catch(() => setError(true));'],
    ['a handler that flags and falls back', 'p.catch(() => { setItems([]); setLoadError(true); });'],
    ['a named error handler', 'p.catch(handleError);'],
    ['a synchronous parser', 'function parse(raw) { try { return JSON.parse(raw); } catch { return null; } }'],
    ['a rethrow', 'try { f(); } catch (e) { throw e; }'],
    ['an empty swallow (the other guard)', 'p.catch(() => {});'],
    ['a value that is data, not a fallback', "p.catch(() => ({ status: 'offline' }));"],
  ];

  it.each(FLAGGED)('flags %s', (_name, code) => {
    expect(findUnloggedFallbacks(code)).toHaveLength(1);
  });

  it.each(ACCEPTED)('accepts %s', (_name, code) => {
    expect(findUnloggedFallbacks(code)).toEqual([]);
  });
});
