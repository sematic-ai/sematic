const path = require("path");
const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");
module.exports = {
  "stories": ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
  "addons": ["@storybook/addon-links", "@storybook/addon-essentials", "@storybook/addon-interactions", "@storybook/preset-create-react-app"],
  "framework": {
    name: "@storybook/react-webpack5",
    options: {}
  },
  "typescript": {
    check: false,
    reactDocgen: false
  },
  /**
   * Storybook Webpack customization
   * @param config Webpack config
   * @param configType DEVELOPMENT or PRODUCTION
   */
  webpackFinal: async (config, {
    configType
  }) => {
    // resolve TS aliases
    config.resolve.plugins = [...(config.resolve.plugins || []), new TsconfigPathsPlugin({
      configFile: path.resolve(__dirname, "../tsconfig.json"),
      extensions: config.resolve.extensions
    })];
    const filteredPlugins = config.plugins.filter(p => p.constructor.name !== 'ForkTsCheckerWebpackPlugin');
    config.plugins = filteredPlugins;

    // Fix wrong project root
    const babelLoaderRule = config.module.rules.find(
    // https://github.com/storybookjs/storybook/blob/next/lib/builder-webpack4/src/preview/babel-loader-preview.ts
    rule => !!rule.test && rule.test.toString().match(/jsx\|ts\|tsx/));
    // set correct project root
    babelLoaderRule.include = [path.resolve(__dirname, "../..")];

    // Tsx parsing
    config.module.rules.push({
      test: /\.tsx?$/,
      exclude: /node_modules/,
      include: [path.resolve(__dirname, "../..")],
      use: [{
        loader: require.resolve('babel-loader'),
        options: {
          presets: [require('@babel/preset-typescript').default, [require('@babel/preset-react').default, {
            runtime: 'automatic'
          }], require('@babel/preset-env').default]
        }
      }]
    });
    config.resolve.extensions.push('.ts', '.tsx');
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: 'javascript/auto'
    });
    config.resolve.extensions.push('.mjs');

    // Return the altered config
    return config;
  },
  docs: {
    autodocs: false
  }
};