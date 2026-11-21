import { describe, expect, it } from 'vitest';
import ts from 'typescript';

/**
 * #3047 (N-18) — something that only takes the user somewhere is a link, not a click handler.
 *
 * A card, list item, chip or text whose `onClick` calls `navigate(...)` has no URL: it cannot be
 * opened in a new tab (Ctrl/Cmd/middle click do nothing), it is not announced as a link, and a
 * `Typography`/`Box`/`Chip` without a role is not even reachable by keyboard. #3017 fixed the
 * `DataTable` rows (`DataTableRowLink.tsx`); this guard keeps the rest from coming back.
 *
 * **The rule.** A JSX element whose `onClick`, `onAuxClick` or `onKeyDown` handler navigates must be
 * one of the {@link BUTTON_ELEMENTS}. Everything else renders the destination as a link instead:
 * `component={RouterLink} to=…` on the MUI element (`CardActionArea`, `ListItemButton`, `Chip`,
 * `Link`, `Box`), or a stretched link on the card's title when the card holds other controls
 * (`StretchedLink`).
 *
 * **What counts as a button.** An explicit action control — `Button`, `IconButton`, `Fab`,
 * `MenuItem`, `ToggleButton`, `LoadingButton`, a native `<button>`. Such a control may end in
 * navigation: "save and go", "skip the wizard", `navigate(-1)`, a menu entry that closes the menu
 * first. A plain link-shaped destination on a button is still better as `component={RouterLink}`,
 * but the button is already focusable and announced, so it is out of this guard's scope. A `Card`,
 * `CardActionArea`, `Box`, `Paper`, `ListItem`, `ListItemButton`, `TableRow`, `Chip`, `Typography`,
 * `Link` (as `<a>` without the router), `div` or any custom component is not a button here — a
 * custom component's `onClick` is unknown to this scan and is treated as the element it most likely
 * renders: a surface.
 *
 * **What counts as navigating.** The handler contains a call of `navigate` (or any other name bound
 * to `useNavigate()` in the file), directly or through one level of a handler declared in the same
 * file (`onClick={handleOpen}`, `onClick={() => handleOpen(x)}`, `useCallback(...)` included).
 * Props of custom components that are not DOM events (`onRowClick`, `onAction`, `onNavigate`) are
 * out of scope: the component decides what it renders.
 *
 * **The allowlist** names `file::Element` pairs that keep a navigating handler on purpose, with a
 * reason each. It may only shrink: an entry that no longer matches a finding fails the test.
 *
 * The scan is AST-based (TypeScript compiler API, like `swallowedErrorsAreLogged`), and the
 * detector is pinned by fixtures in both directions at the end of this file.
 */

const SOURCES = import.meta.glob(['/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return !/\.(test|spec)\.tsx$/.test(path) && !path.startsWith('/src/test/') && !path.includes('/__mocks__/');
}

/** Elements that are an action control and may therefore end in navigation. */
export const BUTTON_ELEMENTS: ReadonlySet<string> = new Set([
  'Button',
  'IconButton',
  'Fab',
  'MenuItem',
  'ToggleButton',
  'LoadingButton',
  'button',
]);

const HANDLER_ATTRIBUTES: ReadonlySet<string> = new Set(['onClick', 'onAuxClick', 'onKeyDown']);

export interface NavigateFinding {
  line: number;
  element: string;
  attribute: string;
}

function tagNameText(name: ts.JsxTagNameExpression, source: ts.SourceFile): string {
  return name.getText(source);
}

/** Names bound to `useNavigate()` in the file; `navigate` is always included. */
function navigateNames(source: ts.SourceFile): Set<string> {
  const names = new Set(['navigate']);
  const visit = (node: ts.Node) => {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.initializer &&
      ts.isCallExpression(node.initializer) &&
      ts.isIdentifier(node.initializer.expression) &&
      node.initializer.expression.text === 'useNavigate'
    ) {
      names.add(node.name.text);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return names;
}

/** Function-valued declarations of the file by name: `const x = () => …`, `useCallback(…)`, `function x()`. */
function handlerDeclarations(source: ts.SourceFile): Map<string, ts.Node> {
  const declarations = new Map<string, ts.Node>();
  const visit = (node: ts.Node) => {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer) {
      declarations.set(node.name.text, node.initializer);
    } else if (ts.isFunctionDeclaration(node) && node.name) {
      declarations.set(node.name.text, node);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return declarations;
}

function callsNavigate(node: ts.Node, names: Set<string>): boolean {
  let found = false;
  const visit = (n: ts.Node) => {
    if (found) return;
    if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && names.has(n.expression.text)) {
      found = true;
      return;
    }
    ts.forEachChild(n, visit);
  };
  visit(node);
  return found;
}

/** The handler a `{ident}` or `{() => ident(...)}` attribute delegates to, if any. */
function delegatedHandlerName(expression: ts.Expression): string | null {
  if (ts.isIdentifier(expression)) return expression.text;
  if (ts.isArrowFunction(expression)) {
    let body: ts.Node = expression.body;
    if (ts.isBlock(body) && body.statements.length === 1 && ts.isExpressionStatement(body.statements[0])) {
      body = body.statements[0].expression;
    }
    if (ts.isVoidExpression(body as ts.Expression)) body = (body as ts.VoidExpression).expression;
    if (ts.isCallExpression(body as ts.Node) && ts.isIdentifier((body as ts.CallExpression).expression)) {
      return ((body as ts.CallExpression).expression as ts.Identifier).text;
    }
  }
  return null;
}

/** Every handler attribute that navigates on a non-button element of `code`. */
export function findNavigatingSurfaces(code: string, fileName = 'x.tsx'): NavigateFinding[] {
  const source = ts.createSourceFile(fileName, code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const names = navigateNames(source);
  const declarations = handlerDeclarations(source);
  const findings: NavigateFinding[] = [];

  const navigates = (expression: ts.Expression): boolean => {
    if (callsNavigate(expression, names)) return true;
    const delegate = delegatedHandlerName(expression);
    if (delegate === null || names.has(delegate)) return false;
    const declaration = declarations.get(delegate);
    return declaration !== undefined && callsNavigate(declaration, names);
  };

  const checkAttributes = (tagName: ts.JsxTagNameExpression, attributes: ts.JsxAttributes) => {
    const element = tagNameText(tagName, source);
    if (BUTTON_ELEMENTS.has(element)) return;
    for (const attribute of attributes.properties) {
      if (!ts.isJsxAttribute(attribute)) continue;
      const attributeName = attribute.name.getText(source);
      if (!HANDLER_ATTRIBUTES.has(attributeName)) continue;
      const initializer = attribute.initializer;
      if (!initializer || !ts.isJsxExpression(initializer) || !initializer.expression) continue;
      if (!navigates(initializer.expression)) continue;
      findings.push({
        line: source.getLineAndCharacterOfPosition(attribute.getStart(source)).line + 1,
        element,
        attribute: attributeName,
      });
    }
  };

  const visit = (node: ts.Node) => {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      checkAttributes(node.tagName, node.attributes);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return findings;
}

/** Every handler attribute that navigates, on any element — the guard's coverage measure. */
export function countNavigatingHandlers(code: string): number {
  const source = ts.createSourceFile('x.tsx', code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const names = navigateNames(source);
  let count = 0;
  const visit = (node: ts.Node) => {
    if (ts.isJsxAttribute(node) && HANDLER_ATTRIBUTES.has(node.name.getText(source))) {
      const initializer = node.initializer;
      if (initializer && ts.isJsxExpression(initializer) && initializer.expression && callsNavigate(initializer.expression, names)) {
        count += 1;
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return count;
}

/**
 * `file::Element` pairs that keep a navigating handler deliberately. Shrink-only.
 */
const ALLOWLIST: Readonly<Record<string, string>> = {
  'components/common/DataTableRowLink.tsx::TableRow':
    'the row keeps its native row role (a table row must stay a row); its first cell carries the real ' +
    '<a href> and the row handler only extends that link to the rest of the surface, modifier and ' +
    'middle clicks included (#3017)',
  'components/common/DataTableRowLink.tsx::Box':
    'the DataTable mobile card is role="link" with Enter and modifier-click handling — it cannot be an ' +
    '<a> because a card may hold row actions, and nested interactive content inside <a> is invalid (#3017)',
};

function rel(path: string): string {
  return path.replace(/^\/src\//, '');
}

const production = Object.entries(SOURCES).filter(([path]) => isProductionSource(path));

describe('navigation on a non-button element is a link (#3047)', () => {
  const findings = production.flatMap(([path, code]) =>
    findNavigatingSurfaces(code, path).map((f) => ({ ...f, file: rel(path) })),
  );

  it('no surface navigates from a click handler outside the allowlist', () => {
    const unexpected = findings
      .filter((f) => !(`${f.file}::${f.element}` in ALLOWLIST))
      .map((f) => `${f.file}:${f.line} <${f.element} ${f.attribute}> navigates — render it as a link`);
    expect(unexpected).toEqual([]);
  });

  it('the allowlist only lists pairs that still occur (shrink-only)', () => {
    const present = new Set(findings.map((f) => `${f.file}::${f.element}`));
    expect(Object.keys(ALLOWLIST).filter((entry) => !present.has(entry))).toEqual([]);
  });

  it('every allowlist entry gives a reason', () => {
    expect(Object.entries(ALLOWLIST).filter(([, reason]) => reason.trim().length < 20).map(([k]) => k)).toEqual([]);
  });

  it('scans a realistic share of the source tree and sees the navigating handlers it judges', () => {
    // A glob or parser failure that finds nothing would pass the rule above vacuously.
    expect(production.length).toBeGreaterThan(500);
    const handlers = production.reduce((sum, [, code]) => sum + countNavigatingHandlers(code), 0);
    expect(handlers).toBeGreaterThan(30);
  });
});

describe('findNavigatingSurfaces — fixtures', () => {
  const wrap = (jsx: string, extra = '') =>
    `const navigate = useNavigate();\n${extra}\nexport function X() {\n  return (\n${jsx}\n  );\n}`;

  it('rejects a card, chip, list item, text and box that navigate', () => {
    const code = wrap(
      [
        '<CardActionArea onClick={() => navigate(`/a/${k}`)} />',
        '<Chip clickable onClick={(e) => { e.stopPropagation(); navigate("/b"); }} />',
        '<ListItemButton onClick={() => navigate("/c")} />',
        '<Typography component="a" href="/d" onClick={(e) => { e.preventDefault(); navigate("/d"); }}>d</Typography>',
        '<Box role="link" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") navigate("/e"); }} />',
      ].join('\n'),
    );
    expect(findNavigatingSurfaces(code).map((f) => `${f.element}:${f.attribute}`)).toEqual([
      'CardActionArea:onClick',
      'Chip:onClick',
      'ListItemButton:onClick',
      'Typography:onClick',
      'Box:onKeyDown',
    ]);
  });

  it('follows one level of a handler declared in the file, and a renamed navigate', () => {
    const code = `const go = useNavigate();
const open = useCallback(() => go('/x'), [go]);
function handleRow(key: string) { go(\`/y/\${key}\`); }
export function X() {
  return (<>
    <Card onClick={open} />
    <Paper onClick={() => handleRow(k)} />
    <div onClick={() => void open()} />
  </>);
}`;
    expect(findNavigatingSurfaces(code).map((f) => f.element)).toEqual(['Card', 'Paper', 'div']);
  });

  it('accepts buttons that navigate, links without a handler, and surfaces that do not navigate', () => {
    const code = wrap(
      [
        '<Button onClick={() => navigate(-1)}>back</Button>',
        '<IconButton onClick={() => navigate("/settings")} aria-label="s" />',
        '<MenuItem onClick={handleSettings}>s</MenuItem>',
        '<button type="button" onClick={() => navigate("/x")} />',
        '<CardActionArea component={RouterLink} to="/a" />',
        '<Chip component={RouterLink} to="/b" clickable onClick={() => setOpen(false)} />',
        '<Box onClick={() => setExpanded((p) => !p)} />',
      ].join('\n'),
      'const handleSettings = () => { setAnchor(null); navigate("/settings"); };',
    );
    expect(findNavigatingSurfaces(code)).toEqual([]);
  });

  it('reports the line of the offending attribute', () => {
    const code = 'const navigate = useNavigate();\n<Box\n  sx={{}}\n  onClick={() => navigate("/x")}\n/>';
    expect(findNavigatingSurfaces(code)).toEqual([{ line: 4, element: 'Box', attribute: 'onClick' }]);
  });
});
