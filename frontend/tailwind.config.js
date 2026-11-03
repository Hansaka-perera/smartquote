export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)", panel: "var(--panel)", sunk: "var(--sunk)", ink: "var(--ink)", mute: "var(--mute)",
        line: "var(--line)", accent: "var(--accent)", "accent-ink": "var(--accent-ink)",
        ok: "var(--ok)", warn: "var(--warn)", bad: "var(--bad)",
      },
      fontFamily: {
        sans: ['Bahnschrift', '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ["Consolas", '"Cascadia Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
