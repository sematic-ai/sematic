import { defineConfig } from "cypress";
import { initPlugin } from "@frsource/cypress-plugin-visual-regression-diff/plugins";
import {createReactAppHandler} from "@cypress/webpack-dev-server/dist/helpers/createReactAppHandler";
import { devServer }  from "@cypress/webpack-dev-server";

const TsconfigPathsWebpackPlugin = require('tsconfig-paths-webpack-plugin');

export default defineConfig({
  env: {
    pluginVisualRegressionImagesPath: 'cypress_screenshots/upper_level/{spec_path}',
    pluginVisualRegressionForceDeviceScaleFactor: true,
  },
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
    specPattern: [
      "../main/src/**/*.cy.{ts,tsx}",
      "../common/src/**/*.cy.{ts,tsx}"
    ],

    devServer: (cypressConfig) => {
      const handler = createReactAppHandler(cypressConfig);
      const webpackConfig = handler.frameworkConfig;

      (webpackConfig.resolve!.plugins!).push(new TsconfigPathsWebpackPlugin({}));

      return devServer({
        ...cypressConfig,
        webpackConfig: {
        ...webpackConfig,
        },
      })
    },

    setupNodeEvents(on, config) {
      // implement node event listeners here
      initPlugin(on, config);

      return config      
    },
  },
});
