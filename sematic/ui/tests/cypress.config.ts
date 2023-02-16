import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:5001",
    supportFile: "support/e2e.ts",
    specPattern: "e2e/**/*.cy.{js,jsx,ts,tsx}",
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
  fileServerFolder: ".",
  fixturesFolder: "fixtures",
  screenshotsFolder: "cypress_screenshots",
  videosFolder: "cypress_video",
  reporter: 'junit',
  reporterOptions: {
    "mochaFile": "cypress_results/tests-[hash].xml",
    "toConsole": true
  }
});
