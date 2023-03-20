const path = require("path");

module.exports = function override(config, env) {
    //do stuff with the webpack config...

    // Tsx parsing
    config.module.rules.push({
        test: /\.tsx?$/,
        exclude: /node_modules/,
        include: [path.resolve(__dirname, "../..")],
        use: [
          {
            loader: require.resolve('babel-loader'),
            options: {
              presets: [
                require('@babel/preset-typescript').default,
                [require('@babel/preset-react').default, { runtime: 'automatic' }],
                require('@babel/preset-env').default,
              ],
            },
          },
        ],
      });
      
    return config;
  }
  