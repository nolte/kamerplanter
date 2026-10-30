import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

// Issue #825 — a form element without `noValidate` lets the browser run its own
// constraint validation, which aborts submission before the `submit` event
// fires. `handleSubmit` never runs, so zod never runs, no helper text renders,
// and the user sees a native bubble in the browser's locale instead of ours.
// jsdom does not enforce native constraint validation, so no unit test can
// catch this — that is why the defence is static.
//
// `<Form>` (src/components/form/Form.tsx) applies `noValidate` after its prop
// spread, so it cannot be switched off; use it instead of a raw form element.
// The escape hatch is an explicit `noValidate`, which keeps the rule honest for
// the handful of non-RHF forms.
//
// A constant because flat config REPLACES a rule's options when a later block
// sets the same rule: every block that sets `no-restricted-syntax` must spread
// these selectors again, or the files it matches silently lose them.
const FORM_NO_VALIDATE_SELECTORS = [
  {
    selector:
      "JSXOpeningElement[name.name='form']:not(:has(JSXAttribute[name.name='noValidate']))",
    message:
      'Use <Form> from @/components/form/Form instead of a raw <form>. It sets noValidate, without which native validation bypasses zod (#825).',
  },
  {
    selector:
      "JSXOpeningElement:has(JSXAttribute[name.name='component'][value.value='form']):not(:has(JSXAttribute[name.name='noValidate']))",
    message:
      'Use <Form> from @/components/form/Form instead of component="form". It sets noValidate, without which native validation bypasses zod (#825).',
  },
  {
    // The two selectors above only test that a `noValidate` attribute is
    // *present*, so `noValidate={false}` satisfied them while leaving the
    // form exactly as broken. Caught by review of this PR: a guard whose
    // stated job is to make the bad state unreachable should not have an
    // opt-out that reads like compliance.
    selector:
      "JSXAttribute[name.name='noValidate'][value.expression.value=false]",
    message:
      'noValidate={false} re-enables native validation, which aborts submission before zod runs (#825). Drop the attribute and use <Form>.',
  },
];

// Issue #2518 — `src/features/**` must not depend on `src/pages/**`. A page is a
// route's leaf; a feature that reaches into one couples itself to that route's
// file layout. Code both need lives in `src/components/` (or hooks/utils/api).
//
// What the regex matches: a specifier that STARTS with `@/pages` or with one or
// more `../` followed by a `pages` segment (`pages`, `pages/...`). That reports
// `../pages/x` from any feature depth, even where it would resolve to a
// feature-local `pages/` folder rather than `src/pages` — no feature has such a
// folder, so the over-report is deliberate and costs nothing today.
// What it does NOT match: `pages.json` (the i18n namespace the feature tests
// load, `pages` is not followed by `/` or the end), `./pages/...`, names that
// merely contain `pages` (`@/components/pages-foo`, `./pagesUtil`), and the
// constructions `./../pages/...` and `../../../src/pages/...` — those reach
// `src/pages` but are NOT detected; review has to catch them.
const PAGES_IMPORT_REGEX = '^(@/|(\\.\\./)+)pages(/|$)';
const FEATURES_NOT_FROM_PAGES_MESSAGE =
  'src/features must not import from src/pages (#2518). Move the shared code to src/components/ (or hooks/, utils/, api/) and import it from there.';
const FEATURES_NOT_FROM_PAGES_IMPORT_PATTERN = {
  regex: PAGES_IMPORT_REGEX,
  message: FEATURES_NOT_FROM_PAGES_MESSAGE,
};
// `no-restricted-imports` checks import/export declarations only; a dynamic
// `import()` — the form `lazy(() => import(...))` takes — passes it unreported
// (measured on ESLint 10.13). These selectors cover the dynamic form, for a
// string literal and for a template literal's leading text. esquery's regex
// literal cannot contain `/`, hence `\x2F`.
const ESQUERY_PAGES_REGEX = '/^(@\\x2F|(\\.\\.\\x2F)+)pages(\\x2F|$)/';
const FEATURES_NOT_FROM_PAGES_SELECTORS = [
  {
    selector: `ImportExpression[source.value=${ESQUERY_PAGES_REGEX}]`,
    message: FEATURES_NOT_FROM_PAGES_MESSAGE,
  },
  {
    selector: `ImportExpression > TemplateLiteral.source > TemplateElement:first-child[value.raw=${ESQUERY_PAGES_REGEX}]`,
    message: FEATURES_NOT_FROM_PAGES_MESSAGE,
  },
  {
    // A feature test that mocks or loads a page module through vitest
    // (`vi.mock('@/pages/x')`, `await vi.importActual('@/pages/x')`) couples to
    // the page exactly like an import does, but the specifier is a plain call
    // argument that neither rule above sees.
    selector: `CallExpression[callee.object.name='vi'][callee.property.name=/^(mock|doMock|importActual|importMock)$/][arguments.0.type='Literal'][arguments.0.value=${ESQUERY_PAGES_REGEX}]`,
    message: FEATURES_NOT_FROM_PAGES_MESSAGE,
  },
];

export default tseslint.config(
  { ignores: ['dist', 'public'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-restricted-syntax': ['error', ...FORM_NO_VALIDATE_SELECTORS],
      // React Compiler diagnostics (eslint-plugin-react-hooks >=7.1) flag a
      // large number of pre-existing patterns across the codebase. Demote
      // them from error to warn for now so CI stays green; address them in
      // a dedicated cleanup pass.
      // TODO: Re-enable as error once the codebase is React-Compiler clean.
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/preserve-manual-memoization': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/purity': 'warn',
      'react-hooks/refs': 'warn',
    },
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },
  {
    // #2518 — features -> pages is forbidden, static and dynamic. Test files are
    // covered too: a feature test importing a page would be the same coupling.
    // The #825 selectors are spread in because this block replaces the rule's
    // options for every file it matches.
    files: ['src/features/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': ['error', { patterns: [FEATURES_NOT_FROM_PAGES_IMPORT_PATTERN] }],
      'no-restricted-syntax': ['error', ...FORM_NO_VALIDATE_SELECTORS, ...FEATURES_NOT_FROM_PAGES_SELECTORS],
    },
  },
  {
    // REQ-053 GP-NFR-009 / D-01: the garden editor talks to the `PlanRenderer` interface only.
    // A renderer implementation or rendering library imported here would weld the editor to one
    // renderer and make the Konva fallback a rewrite instead of a swap. Only the code that mounts
    // the editor (the lazy route) may pick `SvgPlanRenderer`; tests use `HeadlessPlanRenderer`.
    files: ['src/features/gardenPlanner/editor/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: ['konva', 'react-konva', 'fabric', 'pixi.js'].map((name) => ({
            name,
            message: 'The garden editor must not import a rendering library (GP-NFR-009). Use the PlanRenderer interface.',
          })),
          patterns: [
            {
              group: ['**/SvgPlanRenderer', '**/SvgPlanRenderer.*', '**/renderer/svg', '**/renderer/svg/**', '@pixi/*'],
              message:
                'The garden editor must not import a renderer implementation (GP-NFR-009). Import the PlanRenderer interface from the renderer barrel and receive the instance from the route.',
            },
            // This block replaces the features block's options for the editor
            // files, so the #2518 pattern must be repeated here.
            FEATURES_NOT_FROM_PAGES_IMPORT_PATTERN,
          ],
        },
      ],
    },
  },
  {
    // Node-side build/CI tooling (e.g. the bundle-budget gate) runs outside the
    // browser and legitimately uses Node globals like `process` and `console`.
    files: ['scripts/**/*.{js,mjs,cjs}'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
  prettier,
);
