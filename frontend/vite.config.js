import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom", // simulates a browser DOM environment for component tests
    globals: true, // makes describe/it/expect available without importing
  },
});
