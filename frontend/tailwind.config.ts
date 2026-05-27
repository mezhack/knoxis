import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4ff",
          100: "#dce5ff",
          500: "#4461d7",
          600: "#3451c4",
          700: "#2840a8",
          800: "#1f3090",
          900: "#152275",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
