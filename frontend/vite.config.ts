import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// En desarrollo Vite hace de proxy hacia uvicorn; en producción FastAPI sirve frontend/dist.
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { "/api": backend, "/mcp": backend },
  },
  build: { outDir: "dist" },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/app/test-setup.ts"],
    css: false,
  },
});
