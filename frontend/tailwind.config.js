/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          50: '#eef8ff',
          100: '#d9edff',
          200: '#bce0ff',
          300: '#90caff',
          400: '#5aafff',
          500: '#3494ff',
          600: '#1877f2',
          700: '#0f5cd7',
          800: '#114baf',
          900: '#14418c',
          950: '#112a55',
        },
      },
    },
  },
  darkMode: 'media', // 基于系统偏好的暗黑模式
  plugins: [],
}
