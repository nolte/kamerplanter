import { describe, expect, it } from 'vitest';
import ts from 'typescript';

/**
 * #1564 — a value that is **re-allocated on every render** must not appear in a
 * `useEffect` dependency array.
 *
 * `WorkflowInstantiateDialog` declared `targetEntityTypes = ['plant_instance']`
 * as a parameter default and listed that array in the dependencies of the
 * effect that loads the dialog's data. A default parameter is evaluated per
 * call, so the array had a new identity on every render: each render tore the
 * in-flight load down (the cleanup sets `cancelled = true`, which also skips
 * the `finally` that clears `loadingTemplates`) and started a fresh one. One
 * mount issued **22** template requests in two seconds, and the empty-state
 * text appeared and disappeared once per lap — so
 * `shows the empty-template message and tolerates load failures` resolved or
 * not depending on where the polling `findByText` landed in that cycle. It
 * passed alone and failed under full-suite contention.
 *
 * The same identity churn reaches the component from its call site, so the
 * guard has two halves:
 *
 * 1. **Parameter defaults** — a destructured prop whose default allocates
 *    (`[]`, `{}`, `() => {}`, `new X()`) and that is named in a `useEffect`
 *    dependency array in the same component.
 * 2. **Call sites** — a JSX attribute whose value allocates per render, passed
 *    to a component in this source tree that names that prop in a `useEffect`
 *    dependency array. This half is what catches
 *    `targetEntityTypes={… ?? ['plant_instance']}`, where the churn is in the
 *    caller and the default is never reached.
 *
 * **Scoped to `useEffect`/`useLayoutEffect` deliberately.** The same churn in a
 * `useMemo`/`useCallback` dependency list only re-derives a value; it costs a
 * little work and cannot loop. An effect *acts* — it fetches, it sets state,
 * its cleanup cancels — so there the churn is a defect rather than waste.
 *
 * **What this does not cover.** An unstable value reached through a custom hook
 * (`const { handleError } = useApiError()`) is invisible here: whether that
 * object is stable is a property of the hook, not of this call site. The
 * repository's own convention (FRONTEND.md §6.1, "object return MUST be
 * `useMemo`-stabilised") is what covers that end, and `useApiError` follows it.
 *
 * The detector is exercised against fixtures in both directions at the end of
 * this file, including the restored #1564 defect as a positive fixture: a guard
 * nobody has seen fail is a guard nobody has measured.
 */

const ALL_TSX = import.meta.glob('/src/**/*.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/**
 * Production sources only.
 *
 * The call-site half asks "does this caller hand the callee a fresh value on
 * every render", and in a test the answer is structurally no: the test body
 * builds the element once and never re-renders it, so an array literal written
 * inline there has a stable identity for the whole case. Measured on the five
 * `<Harness slotsForArea={[…]} />` sites in
 * `LocationAssignmentSection.test.tsx`, which the unscoped glob reported and
 * which cannot loop for exactly that reason. Keeping them in would make the
 * guard a thing people silence rather than read.
 */
const SOURCES = Object.fromEntries(
  Object.entries(ALL_TSX).filter(([name]) => !name.startsWith('/src/test/')),
);

const EFFECT_HOOKS = new Set(['useEffect', 'useLayoutEffect']);

/** Expression kinds that produce a new object identity every time they run. */
const ALLOCATING_KINDS = new Set<ts.SyntaxKind>([
  ts.SyntaxKind.ArrayLiteralExpression,
  ts.SyntaxKind.ObjectLiteralExpression,
  ts.SyntaxKind.ArrowFunction,
  ts.SyntaxKind.FunctionExpression,
  ts.SyntaxKind.NewExpression,
]);

/** Array-returning members: `xs.map(…)` is a fresh array on every render too. */
const ALLOCATING_MEMBERS = new Set([
  'map',
  'filter',
  'slice',
  'concat',
  'flat',
  'flatMap',
  'split',
]);

function parse(fileName: string, source: string): ts.SourceFile {
  return ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
}

function allocatesPerRender(expr: ts.Expression): boolean {
  if (ALLOCATING_KINDS.has(expr.kind)) return true;
  // `a ?? ['x']` / `a || ['x']` — the fallback allocates whenever it is taken.
  if (ts.isBinaryExpression(expr)) {
    const op = expr.operatorToken.kind;
    if (op === ts.SyntaxKind.QuestionQuestionToken || op === ts.SyntaxKind.BarBarToken) {
      return allocatesPerRender(expr.left) || allocatesPerRender(expr.right);
    }
  }
  if (ts.isConditionalExpression(expr)) {
    return allocatesPerRender(expr.whenTrue) || allocatesPerRender(expr.whenFalse);
  }
  if (ts.isParenthesizedExpression(expr)) return allocatesPerRender(expr.expression);
  if (
    ts.isCallExpression(expr) &&
    ts.isPropertyAccessExpression(expr.expression) &&
    ALLOCATING_MEMBERS.has(expr.expression.name.text)
  ) {
    return true;
  }
  return false;
}

function line(sf: ts.SourceFile, node: ts.Node): number {
  return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
}

/** Every identifier named in an effect dependency array anywhere in `node`. */
function effectDepNames(sf: ts.SourceFile, node: ts.Node): Map<string, number> {
  const names = new Map<string, number>();
  const walk = (n: ts.Node): void => {
    if (
      ts.isCallExpression(n) &&
      ts.isIdentifier(n.expression) &&
      EFFECT_HOOKS.has(n.expression.text)
    ) {
      const deps = n.arguments[1];
      if (deps && ts.isArrayLiteralExpression(deps)) {
        for (const dep of deps.elements) {
          if (ts.isIdentifier(dep) && !names.has(dep.text)) names.set(dep.text, line(sf, n));
        }
      }
    }
    ts.forEachChild(n, walk);
  };
  walk(node);
  return names;
}

interface ComponentShape {
  /** Props the component names in one of its effect dependency arrays. */
  effectProps: Set<string>;
}

/** Function-shaped declarations whose name starts upper-case — i.e. components. */
function componentsOf(sf: ts.SourceFile): Map<string, ComponentShape> {
  const found = new Map<string, ComponentShape>();
  const walk = (node: ts.Node): void => {
    let name: string | null = null;
    let fn: ts.FunctionLikeDeclaration | null = null;
    if (ts.isFunctionDeclaration(node) && node.name) {
      name = node.name.text;
      fn = node;
    } else if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.initializer &&
      (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer))
    ) {
      name = node.name.text;
      fn = node.initializer;
    }
    if (name && fn && /^[A-Z]/.test(name)) {
      const props = new Set<string>();
      for (const param of fn.parameters) {
        if (!ts.isObjectBindingPattern(param.name)) continue;
        for (const el of param.name.elements) {
          if (ts.isIdentifier(el.name)) props.add(el.name.text);
        }
      }
      const deps = effectDepNames(sf, fn);
      const effectProps = new Set([...props].filter((p) => deps.has(p)));
      if (effectProps.size > 0) found.set(name, { effectProps });
    }
    ts.forEachChild(node, walk);
  };
  walk(sf);
  return found;
}

/** Half 1: a destructured parameter default that allocates, named in effect deps. */
export function findUnstableParameterDefaults(fileName: string, source: string): string[] {
  const sf = parse(fileName, source);
  const findings: string[] = [];
  const walk = (node: ts.Node): void => {
    if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
      const deps = effectDepNames(sf, node);
      for (const param of node.parameters) {
        if (!ts.isObjectBindingPattern(param.name)) continue;
        for (const el of param.name.elements) {
          if (!ts.isIdentifier(el.name) || !el.initializer) continue;
          if (!allocatesPerRender(el.initializer)) continue;
          const depLine = deps.get(el.name.text);
          if (depLine === undefined) continue;
          findings.push(
            `${fileName}:${line(sf, el)} prop '${el.name.text}' has a per-render default and is an effect dependency at line ${depLine}`,
          );
        }
      }
    }
    ts.forEachChild(node, walk);
  };
  walk(sf);
  return findings;
}

/** Half 2: a JSX attribute that allocates, for a prop the callee uses as an effect dep. */
export function findUnstableCallSites(
  fileName: string,
  source: string,
  components: Map<string, ComponentShape>,
): string[] {
  const sf = parse(fileName, source);
  const findings: string[] = [];
  const walk = (node: ts.Node): void => {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const shape = components.get(node.tagName.getText(sf));
      if (shape) {
        for (const attr of node.attributes.properties) {
          if (!ts.isJsxAttribute(attr) || !ts.isIdentifier(attr.name)) continue;
          if (!shape.effectProps.has(attr.name.text)) continue;
          const init = attr.initializer;
          if (!init || !ts.isJsxExpression(init) || !init.expression) continue;
          if (!allocatesPerRender(init.expression)) continue;
          findings.push(
            `${fileName}:${line(sf, attr)} <${node.tagName.getText(sf)} ${attr.name.text}={…}> allocates per render and the callee uses '${attr.name.text}' as an effect dependency`,
          );
        }
      }
    }
    ts.forEachChild(node, walk);
  };
  walk(sf);
  return findings;
}

function componentIndex(sources: Record<string, string>): Map<string, ComponentShape> {
  const index = new Map<string, ComponentShape>();
  for (const [name, source] of Object.entries(sources)) {
    for (const [component, shape] of componentsOf(parse(name, source))) {
      const existing = index.get(component);
      if (existing) {
        for (const p of shape.effectProps) existing.effectProps.add(p);
      } else {
        index.set(component, shape);
      }
    }
  }
  return index;
}

describe('a per-render allocation is never an effect dependency (#1564)', () => {
  it('finds a source tree to inspect', () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(200);
    expect(Object.keys(SOURCES).some((n) => n.startsWith('/src/test/'))).toBe(false);
  });

  it('has no prop whose default allocates and is an effect dependency', () => {
    const findings = Object.entries(SOURCES).flatMap(([name, source]) =>
      findUnstableParameterDefaults(name, source),
    );
    expect(findings).toEqual([]);
  });

  it('has no call site passing a per-render allocation into an effect dependency', () => {
    const index = componentIndex(SOURCES);
    const findings = Object.entries(SOURCES).flatMap(([name, source]) =>
      findUnstableCallSites(name, source, index),
    );
    expect(findings).toEqual([]);
  });
});

// ── Self-test: the detector against both directions ──────────────────
//
// The positive fixtures are the #1564 defect restored, in both of its shapes.

const DEFECT_COMPONENT = `
  export default function Dialog({ open, targetEntityTypes = ['plant_instance'] }: Props) {
    useEffect(() => {
      if (!open) return;
      load(targetEntityTypes);
    }, [open, targetEntityTypes]);
    return null;
  }
`;

const REPAIRED_COMPONENT = `
  export default function Dialog({ open, targetEntityTypes = ['plant_instance'] }: Props) {
    const targetTypesKey = targetEntityTypes.join('|');
    const targetTypes = useMemo(() => targetTypesKey.split('|'), [targetTypesKey]);
    useEffect(() => {
      if (!open) return;
      load(targetTypes);
    }, [open, targetTypes]);
    return null;
  }
`;

const DEFECT_CALL_SITE = `
  export function Page() {
    return <Dialog open targetEntityTypes={workflow?.target_entity_types ?? ['plant_instance']} />;
  }
`;

const REPAIRED_CALL_SITE = `
  export function Page() {
    return <Dialog open targetEntityTypes={targetTypes} />;
  }
`;

describe('the detector itself', () => {
  it('reports the restored defect in the component', () => {
    expect(findUnstableParameterDefaults('/fixture.tsx', DEFECT_COMPONENT)).toHaveLength(1);
  });

  it('stays silent on the repaired component', () => {
    expect(findUnstableParameterDefaults('/fixture.tsx', REPAIRED_COMPONENT)).toEqual([]);
  });

  it('reports a caller that allocates the prop the callee watches', () => {
    const index = componentIndex({ '/dialog.tsx': DEFECT_COMPONENT });
    expect(findUnstableCallSites('/page.tsx', DEFECT_CALL_SITE, index)).toHaveLength(1);
  });

  it('stays silent when the caller passes a stable value', () => {
    const index = componentIndex({ '/dialog.tsx': DEFECT_COMPONENT });
    expect(findUnstableCallSites('/page.tsx', REPAIRED_CALL_SITE, index)).toEqual([]);
  });

  it('ignores the same churn in a useMemo dependency list, which cannot loop', () => {
    const memoOnly = `
      export default function Card({ rows = [] }: Props) {
        const total = useMemo(() => rows.length, [rows]);
        return total;
      }
    `;
    expect(findUnstableParameterDefaults('/fixture.tsx', memoOnly)).toEqual([]);
  });
});
