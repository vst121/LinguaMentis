import { defineConfig } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  {
    ignores: [".next/**", ".next-e2e/**", "test-results/**", "playwright-report/**"],
  },
  {
    extends: [...nextCoreWebVitals, ...nextTypescript],
  },
]);
