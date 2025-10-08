import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import vueDevTools from "vite-plugin-vue-devtools";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDevelopment = mode === "development";
  return {
    plugins: [
      vue({
        features: {
          customElement: true,
          optionsAPI: isDevelopment,
        },
      }),
      vueDevTools(),
    ],
    server: {
      port: 8082,
      proxy: {
      },
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