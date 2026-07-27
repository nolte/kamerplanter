import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

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
      // Issue #825 — a form element without `noValidate` lets the browser run
      // its own constraint validation, which aborts submission before the
      // `submit` event fires. `handleSubmit` never runs, so zod never runs, no
      // helper text renders, and the user sees a native bubble in the
      // browser's locale instead of ours. jsdom does not enforce native
      // constraint validation, so no unit test can catch this — that is why
      // the defence is static.
      //
      // `<Form>` (src/components/form/Form.tsx) applies `noValidate` after its
      // prop spread, so it cannot be switched off; use it instead of a raw
      // form element. The escape hatch is an explicit `noValidate`, which
      // keeps the rule honest for the handful of non-RHF forms.
      'no-restricted-syntax': [
        'error',
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
      ],
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
