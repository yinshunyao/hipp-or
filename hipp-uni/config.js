// 应用全局默认配置（可被 config.local.js 覆盖）
const defaultConfig = {
  // 测试环境
  // baseUrl: 'http://127.0.0.1:9000',
  // 生产环境
  baseUrl: 'http://127.0.0.1:46000',
  // 应用信息
  appInfo: {
    // 应用版本
    version: '1.0.0',
    // 隐私政策，不支持本地路径
    privacy: 'http://127.0.0.1:46000/docs/privacy',
    // 用户协议，不支持本地路径
    agreement: 'http://127.0.0.1:46000/docs/agreement'
  }
}

let localConfig = {}
try {
  // 本地私有配置：建议存放敏感地址/密钥，并加入 .gitignore
  const loadedLocalConfig = require('./config.local.js')
  // 兼容 CommonJS(module.exports) 和 ESModule(export default) 两种写法
  localConfig = loadedLocalConfig && loadedLocalConfig.default
    ? loadedLocalConfig.default
    : loadedLocalConfig
} catch (error) {
  // 未创建本地配置文件时保持默认配置
  localConfig = {}
}

module.exports = {
  ...defaultConfig,
  ...localConfig,
  appInfo: {
    ...defaultConfig.appInfo,
    ...(localConfig.appInfo || {})
  }
}
