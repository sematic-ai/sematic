import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    supportFile: 'support/e2e.ts',
    specPattern: 'e2e/**/*.cy.{js,jsx,ts,tsx}',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
  fileServerFolder: '.',
  fixturesFolder: 'fixtures',
  videosFolder: 'cypress_video'
});
