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
        // Function form, not the object form. The object form matches a
        // module only when Rollup resolves it under the exact bare
        // specifier given ("react", "react-dom"), but react-dom also pulls
        // in "scheduler" and other react-dom/* submodules, and every other
        // vendor chunk below (router, query, motion, charts) itself
        // imports react. With the object form, Rollup let one of those
        // other chunks claim react's modules first, leaving "vendor-react"
        // an empty ~0.05kB chunk and React shipping inside the main
        // index-*.js bundle instead. The function form is called per
        // resolved module id, so every react/react-dom/scheduler module
        // is bucketed correctly regardless of which chunk imports it first.
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          // React core - very stable, long cache life
          if (/node_modules\/(react|react-dom|scheduler)\//.test(id)) {
            return "vendor-react";
          }
          // Router
          if (id.includes("react-router")) return "vendor-router";
          // Data fetching + state
          if (id.includes("@tanstack/react-query") || id.includes("axios")) {
            return "vendor-query";
          }
          // Animation
          if (id.includes("framer-motion")) return "vendor-motion";
          // Charts (large – keep isolated for selective loading)
          if (id.includes("recharts")) return "vendor-charts";
          // UI primitives
          if (
            id.includes("/clsx/") ||
            id.includes("class-variance-authority") ||
            id.includes("tailwind-merge") ||
            id.includes("@radix-ui/react-slot")
          ) {
            return "vendor-ui";
          }
          // Icons (tree-shaken per page, but common core)
          if (id.includes("lucide-react")) return "vendor-icons";
          return undefined;
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
