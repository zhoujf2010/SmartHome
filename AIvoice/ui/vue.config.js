// vue.config.js
const path = require("path");
const TerserPlugin = require("terser-webpack-plugin");


module.exports = {
  outputDir: path.resolve(__dirname, "../server/webpage"),
  publicPath:"/test",

  // chainWebpack: (config) => {
  //   config.optimization.minimizer('terser').tap((args) => {
  //     args[0].terserOptions.compress.drop_console = true
  //     return args
  //   })
  // },

    configureWebpack: {
      plugins: [
      ]
    },
  }