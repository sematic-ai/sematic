import { defineConfig } from "cypress";
import { initPlugin } from "@frsource/cypress-plugin-visual-regression-diff/plugins";

export default defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:5001",
    supportFile: "support/e2e.ts",
    specPattern: "e2e/**/*.cy.{js,jsx,ts,tsx}",
    setupNodeEvents(on, config) {
      // implement node event listeners here
      initPlugin(on, config);
    },
  },

  fileServerFolder: ".",
  fixturesFolder: "fixtures",
  screenshotsFolder: "cypress_screenshots",
  videosFolder: "cypress_video",
  reporter: "junit",

  reporterOptions: {
    mochaFile: "cypress_results/tests-[hash].xml",
    toConsole: true,
  },

  component: {
    supportFile: "support/component.ts",
    indexHtmlFile: 'support/component-index.html',
    specPattern: ["../../packages/main/src/**/*.cy.{ts,tsx}"],

    devServer: {
      framework: "create-react-app",
      bundler: "webpack",
    },

    setupNodeEvents(on, config) {
      // implement node event listeners here
      initPlugin(on, config);
    },
  },
});
