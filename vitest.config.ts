import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['**/*.{ts,tsx}'],
      exclude: [
        'node_modules/**',
        'dist/**',
        '**/*.test.{ts,tsx}',
        '**/*.config.{ts,js}',
        '**/*.setup.{ts,js}',
        'types.ts',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
});
