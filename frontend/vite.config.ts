import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Vite proxy → /api/* идёт на backend, без CORS-боли.
    // Когда фронт открыт на localhost:5173, /api проксируется в backend:8000.
    // (для SSE proxy тоже работает корректно — Vite передаёт стрим)
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,  // нужно для hot reload внутри Docker на некоторых системах
    },
  },
});
