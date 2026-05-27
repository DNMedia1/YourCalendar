/** @type {import('tailwindcss').Config} */
export default {
  content: ["./web/**/*.{html,js}", "./stories/**/*.js"],
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        line: "var(--line)",
        primary: "var(--primary)",
        accent: "var(--accent)",
        danger: "var(--danger)",
      },
      borderRadius: {
        yc: "var(--radius)",
      },
      boxShadow: {
        yc: "var(--shadow)",
        lift: "var(--shadow-lift)",
      },
      spacing: {
        touch: "var(--touch-target)",
      },
    },
  },
  plugins: [],
};
