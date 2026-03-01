/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#1E40AF',
          700: '#1D4ED8',
          800: '#1E3A8A',
        },
        success: {
          50: '#ECFDF5',
          500: '#059669',
          600: '#047857',
        },
        danger: {
          500: '#DC2626',
        },
        warning: {
          500: '#F59E0B',
        },
      },
    },
  },
  plugins: [],
}
