import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        hat: {
          white: {
            bg: "#f8fafc",
            border: "#cbd5e1",
            text: "#334155",
            accent: "#64748b",
          },
          red: {
            bg: "#fff1f2",
            border: "#fecdd3",
            text: "#be123c",
            accent: "#e11d48",
          },
          black: {
            bg: "#0f172a",
            border: "#334155",
            text: "#f8fafc",
            accent: "#475569",
          },
          yellow: {
            bg: "#fffbeb",
            border: "#fde68a",
            text: "#b45309",
            accent: "#d97706",
          },
          green: {
            bg: "#f0fdf4",
            border: "#bbf7d0",
            text: "#15803d",
            accent: "#16a34a",
          },
          blue: {
            bg: "#eff6ff",
            border: "#bfdbfe",
            text: "#1d4ed8",
            accent: "#2563eb",
          },
        },
      },
    },
  },
  plugins: [],
};

export default config;
