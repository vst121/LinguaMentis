import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:3001",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "cd ../backend && uv run python -m tests.e2e_server",
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command:
        "NEXT_DIST_DIR=.next-e2e NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001/api/v1 pnpm exec next dev -p 3001",
      url: "http://127.0.0.1:3001",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
