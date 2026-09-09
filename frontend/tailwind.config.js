/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc7fb',
          400: '#36abf6',
          500: '#0c8ee8',
          600: '#0170c6',
          700: '#0259a0',
          800: '#064b84',
          900: '#0b3f6e',
          950: '#072849',
        },
        survey: {
          green: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
          blue: '#2563eb',
          slate: '#334155'
        }
      }
    },
  },
  plugins: [],
}
