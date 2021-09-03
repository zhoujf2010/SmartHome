// vue.config.js
const path = require("path");
const TerserPlugin = require("terser-webpack-plugin");

module.exports = {
  outputDir: path.resolve(__dirname, "../server/webpage"),
  publicPath:"/MyWx",

  chainWebpack: (config) => {
    config.optimization.minimizer('terser').tap((args) => {
      args[0].terserOptions.compress.drop_console = true
      return args
    })
  },


    // configureWebpack: {
    //   optimization: {
    //     minimizer: [
    //       new TerserPlugin({ terserOptions: { compress: { drop_console: false } } })
    //     ],
    //   },
    //   plugins: [
    //   ]
    // },
    pages: {
        index: {
          entry: 'src/app.ts',// page 的入口
          template: 'public/index.html',// 模板来源
          filename: 'index.html',// 在 dist/index.html 的输出
          title: 'MyHome',// 当使用 title 选项时，
          chunks: ['chunk-vendors', 'chunk-common', 'index'],
        }
      }
  }