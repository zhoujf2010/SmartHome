/* eslint-disable */
const path = require('path');
const fs = require('fs');

const demoPath = path.resolve(__dirname, '../demo');
const publicPath = path.resolve(__dirname, '../public');
const vuePath = path.resolve(__dirname, '../node_modules/vue/dist');
const distPath = path.resolve(__dirname, '../dist');

console.log('拷贝demo资源:');
copy(path.join(vuePath, './vue.js'), path.join(demoPath, 'vue.js'));
copy(path.join(vuePath, './vue.min.js'), path.join(demoPath, 'vue.min.js'));
copy(path.join(publicPath, './mock-min.js'), path.join(demoPath, 'mock-min.js'));
copy(path.join(publicPath, './data.js'), path.join(demoPath, 'data.js'));
copyFolder(distPath, demoPath, /demo\.html$/);
console.log('拷贝demo资源完成');

function mkDirExist(path) {
  if (!fs.existsSync(path)) {
    fs.mkdirSync(path);
  }
}

function copy(src, dist) {
  fs.createReadStream(src).pipe(fs.createWriteStream(dist));
}

function copyFolder(src, output, ignore) {
  mkDirExist(path.resolve(output));

  src = path.resolve(src);

  let temp = '';

  if (fs.existsSync(src)) {
    fs.readdirSync(src).forEach(file => {
      if (ignore && ignore.test(file)) {
        return;
      }
      temp = path.resolve(src, file);
      if (fs.statSync(temp).isDirectory()) {
        copyFolder(temp, path.resolve(output, file));
      } else {
        copy(temp, path.resolve(output, file));
      }
    });
  }
}
