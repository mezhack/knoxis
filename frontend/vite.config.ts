import { existsSync } from "fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dentro do Docker, /.dockerenv existe — usa o nome do serviço do Compose.
// Fora do Docker, usa localhost.
const apiTarget =
  process.env.VITE_API_TARGET ??
  (existsSync("/.dockerenv") ? "http://backend:8000" : "http://localhost:8000");

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
  },
});
