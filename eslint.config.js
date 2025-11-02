// ESLint v9 Flat Config for React + TypeScript (Vite + Vitest)
// Mirrors legacy .eslintrc.json rules and ignores, adapted to flat config

import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import { FlatCompat } from '@eslint/eslintrc';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: __dirname });

export default [
  // Global ignores (flat config replacement for .eslintignore)
  {
    ignores: [
      'dist',
      'node_modules',
      '*.config.js',
      '*.config.ts',
      'backend/**',
      'terraform/**',
      'docs/**'
    ]
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  // Use compatibility layer for plugins that haven't shipped flat configs
  ...compat.config({ extends: ['plugin:react/recommended', 'plugin:react-hooks/recommended'] }),
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: { jsx: true }
      },
      globals: {
        // Browser + Node
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        module: 'readonly',
        process: 'readonly'
      }
    },
    settings: {
      react: { version: 'detect' }
    },
    rules: {
      // Keep previous intent but avoid blocking CI on unused vars in tests/dev
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      // Unescaped entities are stylistic; disable to reduce noise
      'react/no-unescaped-entities': 'off'
    }
  }
];
