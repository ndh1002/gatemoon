import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        tv: {
          bg: "#0b0e11",
          panel: "#11161c",
          border: "#1e2732",
          accent: "#f59e0b",
          cyan: "#22d3ee",
          danger: "#f43f5e",
          ok: "#34d399",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(245, 158, 11, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
