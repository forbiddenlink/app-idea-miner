/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/metrics": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // React core - very stable, long cache life
          "vendor-react": ["react", "react-dom"],
          // Router
          "vendor-router": ["react-router-dom"],
          // Data fetching + state
          "vendor-query": ["@tanstack/react-query", "axios", "zustand"],
          // Animation
          "vendor-motion": ["framer-motion"],
          // Charts (large – keep isolated for selective loading)
          "vendor-charts": ["recharts"],
          // UI primitives
          "vendor-ui": [
            "clsx",
            "class-variance-authority",
            "tailwind-merge",
            "@radix-ui/react-slot",
          ],
          // Icons (tree-shaken per page, but common core)
          "vendor-icons": ["lucide-react", "@heroicons/react"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    exclude: ["**/node_modules/**", "**/e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/test/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
        "src/**/*.d.ts",
      ],
      thresholds: {
        statements: 28,
        branches: 28,
        functions: 24,
        lines: 28,
      },
    },
  },
});
