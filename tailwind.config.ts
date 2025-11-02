import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          950: '#0f172a',
          900: '#111827',
          800: '#1f2937',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
