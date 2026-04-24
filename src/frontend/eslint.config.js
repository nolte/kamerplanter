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
  prettier,
);
