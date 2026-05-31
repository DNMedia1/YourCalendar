import { defineConfig } from "cypress";

// E2E configuration for YourCalendar.
// The web app is started separately (locally or in CI) and served on
// http://127.0.0.1:8765. Cypress only drives the browser against that origin.
export default defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:8765",
    specPattern: "cypress/e2e/**/*.cy.js",
    supportFile: "cypress/support/e2e.js",
    fixturesFolder: false,
    // Keep CI artifacts predictable and lightweight.
    video: true,
    screenshotOnRunFailure: true,
    retries: {
      runMode: 1,
      openMode: 0,
    },
  },
});
