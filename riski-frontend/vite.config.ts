import { fileURLToPath, URL } from "node:url";

import type { ProxyOptions } from "vite";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import vueDevTools from "vite-plugin-vue-devtools";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDevelopment = mode === "development";
  const isDevNoMock = mode === "development-no-mock";
  const enableOptionsAPI = isDevelopment || isDevNoMock;
  const proxy: Record<string, string | ProxyOptions> | undefined = isDevNoMock
    ? {
        "/api": {
          target: "http://localhost:8080",
          changeOrigin: true,
        },
      }
    : undefined;
  return {
    plugins: [
      vue({
        features: {
          customElement: true,
          optionsAPI: enableOptionsAPI,
        },
      }),
      vueDevTools(),
    ],
    server: {
      port: 8082,
      proxy,
    },
    resolve: {
      dedupe: ["vue"],
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    build: {
      manifest: true, // required for post build logic in 'processes' folder
      rollupOptions: {
        input: {
          "riski-search-webcomponent": "./src/riski-search-webcomponent.ts",
        },
        output: {
          entryFileNames: "entry-[name]-[hash].js",
          dir: "dist/src",
        },
      },
    },
  };
});
