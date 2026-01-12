/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Genaryn brand colors
        primary: {
          DEFAULT: '#1a5490',
          50: '#e6f0f9',
          100: '#cce1f3',
          200: '#99c3e6',
          300: '#66a5da',
          400: '#3387cd',
          500: '#1a5490',
          600: '#154373',
          700: '#103256',
          800: '#0b2239',
          900: '#05111d',
        },
        secondary: {
          DEFAULT: '#ffd700',
          50: '#fffce6',
          100: '#fff9cc',
          200: '#fff299',
          300: '#ffec66',
          400: '#ffe533',
          500: '#ffd700',
          600: '#ccac00',
          700: '#998100',
          800: '#665600',
          900: '#332b00',
        },
        // Military-themed colors
        tactical: '#4a5568',
        operational: '#2d3748',
        strategic: '#1a202c',
        success: '#48bb78',
        warning: '#ed8936',
        danger: '#f56565',
        info: '#4299e1',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}