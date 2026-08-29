/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--tg-bg, #0b0e14)",
        surface: "var(--surface, #141824)",
        surface2: "var(--surface2, #1b2030)",
        border: "var(--border, #262c3d)",
        accent: "#4d9eff",
        accent2: "#7c5cff",
        text: "var(--tg-text, #f4f6fb)",
        textdim: "var(--tg-hint, #8891a5)",
        success: "#3ddc84",
        danger: "#ff5c72",
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Inter", "sans-serif"],
      },
      boxShadow: {
        glow: "0 8px 32px -8px rgba(77, 158, 255, 0.35)",
        card: "0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
      borderRadius: {
        xl2: "20px",
      },
    },
  },
  plugins: [],
};
