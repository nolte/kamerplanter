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
 * file: `onClick={handleOpen}`, or any call in the handler's body — `() => handleOpen(x)` as well as
 * `() => { close(); handleOpen(x); }` — `useCallback(...)` included. A handler name is resolved in
 * the scope of the element (the enclosing component first, then outward), so two components of one
 * file with an equally named `handleOpen` are judged by their own declaration.
 *
 * **A link that also navigates.** An element that carries `to` or `href` *and* a navigating handler
 * is reported even when it is a button: `<Button component={RouterLink} to=… onClick={() =>
 * navigate(…)}>` follows the router link and then navigates a second time.
 *
 * **Not detected (known false negatives).** A member handler — `onClick={actions.open}`,
 * `onClick={() => props.onOpen()}` — is not resolved: the object's shape is unknown to a per-file
 * syntactic scan (a hook's return value, a prop, a context). The same holds for a destructured
 * hook result — `const { follow } = useRowFollow(href)`: the `TableRow` in `DataTableRowLink.tsx`
 * navigates through it and is no longer reported once names resolve per scope (before #3069 a
 * file-global name map matched it to the hook's inner `const follow` by accident; it was allowlisted
 * as the deliberate row-surface extension of the row's real cell link). Neither is a handler two levels deep
 * (`handleOpen` → `goTo` → `navigate`) or one imported from another module. Such a surface is caught
 * only by review; make it a link at the source when you meet one.
 *
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
  /** `surface`: a non-button navigates; `link-also-navigates`: an element with `to`/`href` navigates again. */
  kind: 'surface' | 'link-also-navigates';
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

/** The function-valued declaration `name` binds in the statement list `statements`, if any. */
function declarationIn(statements: ts.NodeArray<ts.Statement>, name: string): ts.Node | undefined {
  for (const statement of statements) {
    if (ts.isFunctionDeclaration(statement) && statement.name?.text === name) return statement;
    if (ts.isVariableStatement(statement)) {
      for (const declaration of statement.declarationList.declarations) {
        if (ts.isIdentifier(declaration.name) && declaration.name.text === name && declaration.initializer) {
          return declaration.initializer;
        }
      }
    }
  }
  return undefined;
}

/**
 * The declaration `name` resolves to as seen from `from`: the innermost enclosing block (the
 * component's body first), then outward to the file. A parameter of that name shadows anything
 * outside it and is unknown here.
 */
function resolveDeclaration(name: string, from: ts.Node): ts.Node | undefined {
  for (let node: ts.Node | undefined = from.parent; node; node = node.parent) {
    if (ts.isFunctionLike(node) && node.parameters.some((p) => ts.isIdentifier(p.name) && p.name.text === name)) {
      return undefined;
    }
    if (ts.isBlock(node) || ts.isSourceFile(node) || ts.isModuleBlock(node)) {
      const found = declarationIn(node.statements, name);
      if (found) return found;
    }
  }
  return undefined;
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

/**
 * The handlers an attribute delegates to: the identifier of `{handleOpen}`, or every plain-identifier
 * call in an inline handler's body — `() => handleOpen(x)`, `() => { close(); handleOpen(x); }`,
 * `() => void open()`. Member calls (`actions.open()`) are not resolved (see the header).
 */
function delegatedHandlerNames(expression: ts.Expression): string[] {
  if (ts.isIdentifier(expression)) return [expression.text];
  if (!ts.isArrowFunction(expression) && !ts.isFunctionExpression(expression)) return [];
  const callees: string[] = [];
  const visit = (n: ts.Node) => {
    if (ts.isCallExpression(n) && ts.isIdentifier(n.expression)) callees.push(n.expression.text);
    ts.forEachChild(n, visit);
  };
  visit(expression.body);
  return callees;
}

/** True for an element that is already a link: it carries a `to` or `href` attribute. */
function isLinkElement(attributes: ts.JsxAttributes, source: ts.SourceFile): boolean {
  return attributes.properties.some(
    (a) => ts.isJsxAttribute(a) && ['to', 'href'].includes(a.name.getText(source)),
  );
}

/** Every handler attribute that navigates on a non-button element of `code`, or on any link. */
export function findNavigatingSurfaces(code: string, fileName = 'x.tsx'): NavigateFinding[] {
  const source = ts.createSourceFile(fileName, code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const names = navigateNames(source);
  const findings: NavigateFinding[] = [];

  const navigates = (expression: ts.Expression): boolean => {
    if (callsNavigate(expression, names)) return true;
    return delegatedHandlerNames(expression).some((delegate) => {
      if (names.has(delegate)) return false;
      const declaration = resolveDeclaration(delegate, expression);
      return declaration !== undefined && callsNavigate(declaration, names);
    });
  };

  const checkAttributes = (tagName: ts.JsxTagNameExpression, attributes: ts.JsxAttributes) => {
    const element = tagNameText(tagName, source);
    const isLink = isLinkElement(attributes, source);
    if (BUTTON_ELEMENTS.has(element) && !isLink) return;
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
        kind: isLink ? 'link-also-navigates' : 'surface',
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

  it('follows a multi-statement inline handler into the handler it delegates to (#3069)', () => {
    const code = `const navigate = useNavigate();
export function X() {
  const handleOpen = (k: string) => navigate(\`/a/\${k}\`);
  return (<>
    <Card onClick={() => { close(); handleOpen(k); }} />
    <Paper onClick={() => { setBusy(true); void handleOpen(k); setBusy(false); }} />
    <Box onClick={() => { close(); setOpen(false); }} />
  </>);
}`;
    expect(findNavigatingSurfaces(code).map((f) => f.element)).toEqual(['Card', 'Paper']);
  });

  it('resolves a handler name in the enclosing component, not file-wide (#3069)', () => {
    const code = `const navigate = useNavigate();
function A() {
  const handleOpen = () => navigate('/a');
  return <Card onClick={handleOpen} />;
}
function B() {
  const handleOpen = () => setOpen(true);
  return <Paper onClick={handleOpen} />;
}
function C() {
  return <Box onClick={handleOpen} />;
}`;
    // A's handler navigates; B's equally named one does not; C sees no declaration in its scope chain.
    expect(findNavigatingSurfaces(code).map((f) => f.element)).toEqual(['Card']);
    // The order of declaration does not matter: B declared first must not shadow A.
    const swapped = code.replace(/function A\(\)[\s\S]*?\n}\n/, '') + '\nfunction A() {\n  const handleOpen = () => navigate("/a");\n  return <Card onClick={handleOpen} />;\n}';
    expect(findNavigatingSurfaces(swapped).map((f) => f.element)).toEqual(['Card']);
  });

  it('reports a link that also navigates, even on a button (#3069)', () => {
    const code = wrap(
      [
        '<Button component={RouterLink} to="/a" onClick={() => navigate("/a")}>a</Button>',
        '<MenuItem component="a" href="/b" onClick={handleSettings}>b</MenuItem>',
        '<Button component={RouterLink} to="/c" onClick={() => setOpen(false)}>c</Button>',
      ].join('\n'),
      'const handleSettings = () => { setAnchor(null); navigate("/settings"); };',
    );
    expect(findNavigatingSurfaces(code).map((f) => `${f.element}:${f.kind}`)).toEqual([
      'Button:link-also-navigates',
      'MenuItem:link-also-navigates',
    ]);
  });

  it('does not resolve member handlers (documented false negative)', () => {
    const code = wrap('<Card onClick={actions.open} />\n<Paper onClick={() => props.onOpen()} />');
    expect(findNavigatingSurfaces(code)).toEqual([]);
  });

  it('reports the line of the offending attribute', () => {
    const code = 'const navigate = useNavigate();\n<Box\n  sx={{}}\n  onClick={() => navigate("/x")}\n/>';
    expect(findNavigatingSurfaces(code)).toEqual([{ line: 4, element: 'Box', attribute: 'onClick', kind: 'surface' }]);
  });
});
