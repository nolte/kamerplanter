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
 * - a `.catch(cb)` — or the rejection handler of `.then(ok, cb)` — whose
 *   callback returns a fallback value (`null`, `false`, `0`, `''`, `[]`,
 *   `new Map()`/`new Set()`, an object literal of fallbacks) or calls
 *   `setX(<fallback>)`, at the top level or inside `if`/`else` branches;
 * - a `.catch(noop)`-style identifier (`noop`, `ignore…`, `swallow…`);
 * - a `catch` clause that calls `setX(<fallback>)`, or that returns a fallback
 *   **after an `await`** in its `try`. A synchronous
 *   `try { return JSON.parse(raw) } catch { return null }` is a parser, not a
 *   load, and is left alone.
 *
 * Other statements beside the fallback do not acquit it (#3037 SCR-006): the
 * common "fallback plus done-flag" shape `.catch(() => { setItems([]);
 * setDone(true); })` is still a fallback. A handler is out of scope only when
 * it **surfaces** the failure: an error setter (`setXError` / `setXFailed` /
 * `setXFailure`), a named reporter that puts it on screen (`handleError`,
 * `report…Failure` / `report…Error`, `…Failed` — the name is the contract), a
 * toast (`notification.error(...)`), or a `throw`. Nested functions inside the
 * handler are not looked into. Log calls (`captureHandledError`, `console.*`,
 * `log…Failure`/`log…Error` wrappers) and bare `if (cond) return;` guards are
 * neutral. A handler that is empty or returns `undefined` is
 * `swallowedErrorsAreLogged`'s business. Comments are found by the TypeScript
 * scanner, so `'https://…'` in a string is no comment.
 *
 * **Not detected, and why** (deliberately not widened now, SCR-012):
 * - handler factories — `.catch(degrade('plan', { plan: null }))`: the
 *   fallback is built in another function; resolving it needs data flow across
 *   declarations. The one factory in the tree (`PlantingRunDetailPage`) logs and
 *   flags the leg itself.
 * - constant identifiers — `.catch(() => EMPTY_LIST)`: an identifier says
 *   nothing about its value without resolving the binding; only the literal
 *   fallbacks above are recognised.
 * - ignored `Promise.allSettled` results — a rejected leg read as "nothing" is
 *   decided where the results are consumed, not in a handler; there is no
 *   handler node to judge.
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

// `logEnrichmentFailure(...)`-style wrappers are log calls too: the name is the contract.
const LOG_CALL = /\b(captureHandledError|console\.(warn|error|info|debug|log)|log\w*(Failure|Error))\s*\(/;
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

/** `setLoadError(...)`, `setPlansFailed(...)`, `setFailure(...)` — the failure is put on screen. */
const ERROR_SETTER = /^set\w*(Error|Failed|Failure)$/;
/**
 * Named reporters that put the failure on screen: `handleError` (toast),
 * `reportSectionFailure` / `sectionFailed` (a page's section banner). The name
 * is the contract — a helper so named that only logs would slip through.
 */
const ERROR_REPORTER = /^(handle\w*Error|report\w*(Failure|Error)|\w+Failed)$/;
/** `notification.error(...)` — a toast. */
const TOAST_OBJECT = /^(notification|notify|snackbar)$/;

/**
 * Walks `node` without entering nested functions: what a nested callback does
 * happens later, not as this handler's answer to the failure.
 */
function walkOwn(node: ts.Node, visit: (child: ts.Node) => void): void {
  const step = (child: ts.Node) => {
    visit(child);
    if (ts.isFunctionLike(child)) return;
    ts.forEachChild(child, step);
  };
  ts.forEachChild(node, step);
}

/** Whether the handler reports the failure instead of hiding it: an error setter or a rethrow. */
function surfacesFailure(node: ts.Node): boolean {
  let found = false;
  const check = (child: ts.Node) => {
    if (found) return;
    if (ts.isThrowStatement(child)) found = true;
    else if (ts.isCallExpression(child)) {
      const callee = child.expression;
      if (ts.isIdentifier(callee)) {
        found = ERROR_SETTER.test(callee.text) || ERROR_REPORTER.test(callee.text);
      } else if (
        ts.isPropertyAccessExpression(callee) &&
        callee.name.text === 'error' &&
        ts.isIdentifier(callee.expression) &&
        TOAST_OBJECT.test(callee.expression.text)
      ) {
        found = true;
      }
    }
  };
  check(node);
  walkOwn(node, check);
  return found;
}

/**
 * The fallbacks a block answers with: `setX(<fallback>)` statements and
 * `return <fallback>` — at the top level and inside `if`/`else` branches and
 * nested blocks. Other statements (a done-flag, a toast, a log) do not make a
 * fallback block innocent; they only sit beside it.
 */
function collectFallbacks(statements: readonly ts.Statement[]): { sets: number; returns: number } {
  const found = { sets: 0, returns: 0 };
  const visit = (statement: ts.Statement) => {
    if (ts.isExpressionStatement(statement) && isFallbackSet(statement.expression)) {
      found.sets += 1;
    } else if (ts.isReturnStatement(statement) && statement.expression && isFallbackValue(statement.expression)) {
      found.returns += 1;
    } else if (ts.isIfStatement(statement)) {
      visit(statement.thenStatement);
      if (statement.elseStatement) visit(statement.elseStatement);
    } else if (ts.isBlock(statement)) {
      statement.statements.forEach(visit);
    }
  };
  statements.forEach(visit);
  return found;
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

/**
 * A block falls back when it answers with at least one fallback setter (or a
 * fallback `return`, where returns count) and neither sets an error state nor
 * rethrows. Log calls are neutral here; the reporter asks for one beside a
 * comment.
 */
function blockFallsBack(block: ts.Block, asyncTry: boolean): boolean {
  if (surfacesFailure(block)) return false;
  const { sets, returns } = collectFallbacks(block.statements);
  return sets > 0 || (returns > 0 && asyncTry);
}

interface FallbackFinding {
  line: number;
  kind: 'catch' | '.catch' | '.catch(noop)' | '.then(_, onRejected)';
}

/**
 * Whether `text` holds a real comment. Scans tokens, so `'https://…'` inside a
 * string or template literal is not mistaken for one (#3037 SCR-012).
 */
function hasComment(text: string, jsx: boolean): boolean {
  const scanner = ts.createScanner(
    ts.ScriptTarget.Latest,
    false,
    jsx ? ts.LanguageVariant.JSX : ts.LanguageVariant.Standard,
    text,
  );
  for (let token = scanner.scan(); token !== ts.SyntaxKind.EndOfFileToken; token = scanner.scan()) {
    if (token === ts.SyntaxKind.SingleLineCommentTrivia || token === ts.SyntaxKind.MultiLineCommentTrivia) {
      return true;
    }
  }
  return false;
}

/** Whether a `.catch`-style callback answers a failure with a fallback. */
function handlerFallsBack(handler: ts.ArrowFunction | ts.FunctionExpression): boolean {
  const body = handler.body;
  if (ts.isBlock(body)) return blockFallsBack(body, true);
  if (surfacesFailure(body)) return false;
  const value = unwrap(body);
  return (
    isFallbackSet(body) ||
    (isFallbackValue(body) && !(ts.isIdentifier(value) && value.text === 'undefined'))
  );
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
  const jsx = fileName.endsWith('x');
  const report = (node: ts.Node, kind: FallbackFinding['kind'], text: string | null) => {
    if (text !== null && hasComment(text, jsx) && LOG_CALL.test(text)) return;
    findings.push({ line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1, kind });
  };

  const visit = (node: ts.Node) => {
    if (ts.isCatchClause(node) && ts.isTryStatement(node.parent)) {
      if (blockFallsBack(node.block, containsAwait(node.parent.tryBlock))) {
        // `getFullText` keeps the comments inside the braces.
        report(node, 'catch', node.block.getFullText(source));
      }
    } else if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
      const method = node.expression.name.text;
      // `.catch(onRejected)` and the rejection handler of `.then(onFulfilled, onRejected)`.
      const handler =
        method === 'catch' && node.arguments.length === 1
          ? node.arguments[0]
          : method === 'then' && node.arguments.length === 2
            ? node.arguments[1]
            : null;
      if (handler && (ts.isArrowFunction(handler) || ts.isFunctionExpression(handler))) {
        if (handlerFallsBack(handler)) {
          report(node, method === 'catch' ? '.catch' : '.then(_, onRejected)', handler.getFullText(source));
        }
      } else if (handler && ts.isIdentifier(handler) && NOOP_NAME.test(handler.text)) {
        report(node, method === 'catch' ? '.catch(noop)' : '.then(_, onRejected)', null);
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
  '/src/features/gardenPlanner/templates/TemplateImportDialog.tsx': {
    count: 1,
    reason:
      "deliberate: a failed confirm clears the stale dry-run report and `refuse(error)` shows the refusal (409 proposes a free name); no load reads as 'none' here",
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
  '/src/pages/standorte/LocationDetailPage.tsx': {
    count: 1,
    reason:
      "open: a failed bed-summary read (not an offline miss) shows the plain location page instead of the bed view; the bed view has no error slot with a retry yet",
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
    // SCR-006: another call beside the fallback does not acquit it.
    ['a fallback plus a done-flag', 'p.catch(() => { setItems([]); setDone(true); });'],
    ['a fallback in an else branch', 'p.catch((e) => { if (gone(e)) { setItem(null); } else { setItems([]); } });'],
    // SCR-012: the rejection handler of a two-argument `.then`.
    ['a .then rejection handler returning a fallback', 'p.then((r) => r.items, () => []);'],
    ['a .then rejection handler that is noop', 'p.then(use, noop);'],
    // SCR-012: `//` inside a string literal is no comment.
    [
      'a URL in a string mistaken for a comment',
      "p.catch((e) => { captureHandledError(e, { from: 'https://example.org' }); return []; });",
    ],
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
    ['a .then rejection handler that sets an error state', 'p.then(use, () => setLoadError(true));'],
    ['a fallback with a toast', 'p.catch((e) => { setItems([]); handleError(e); });'],
    ['a fallback with a section reporter', "p.catch((e) => { setItems([]); reportSectionFailure('items', e); });"],
    ['a fallback with a failure setter', 'try { await f(); } catch (e) { setReport(null); setFailure(e); }'],
    ['a 404 as empty, else an error state', 'p.catch((e) => { if (gone(e)) { setItem(null); return; } setLoadError(true); });'],
    [
      'a commented, logged fallback with a URL in a string',
      "p.catch((e) => {\n  // hint only\n  captureHandledError(e, { from: 'https://example.org' });\n  return [];\n});",
    ],
  ];

  it.each(FLAGGED)('flags %s', (_name, code) => {
    expect(findUnloggedFallbacks(code)).toHaveLength(1);
  });

  it.each(ACCEPTED)('accepts %s', (_name, code) => {
    expect(findUnloggedFallbacks(code)).toEqual([]);
  });
});
