/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // 海洋环境系统的主题色
        ocean: {
          light: '#63B3ED',
          DEFAULT: '#2B6CB0',
          dark: '#1A365D',
        },
        success: '#48BB78',
        warning: '#ECC94B',
        error: '#F56565',
        info: '#4FD1C5',
        // Shadcn UI 需要的颜色变量
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      // 间距系统（基于4px单位）
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
      },
      // 字体大小
      fontSize: {
        'title-1': ['24px', { lineHeight: '1.25' }],
        'title-2': ['20px', { lineHeight: '1.25' }],
        'title-3': ['18px', { lineHeight: '1.25' }],
        'body': ['16px', { lineHeight: '1.5' }],
        'secondary': ['14px', { lineHeight: '1.5' }],
        'small': ['12px', { lineHeight: '1.5' }],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        // 自定义圆角
        'xl': '16px',
      },
      boxShadow: {
        'light': '0 1px 3px rgba(0,0,0,0.1)',
        'medium': '0 4px 6px rgba(0,0,0,0.1)',
        'heavy': '0 10px 15px -3px rgba(0,0,0,0.1)',
        'focus': '0 0 0 3px rgba(43,108,176,0.5)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}