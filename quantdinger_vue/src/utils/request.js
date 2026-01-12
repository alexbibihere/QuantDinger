import axios from 'axios'
// import store from '@/store'
import storage from 'store'
import notification from 'ant-design-vue/es/notification'
import { VueAxios } from './axios'
import { ACCESS_TOKEN } from '@/store/mutation-types'

// PHPSESSID 存储键名
const PHPSESSID_KEY = 'PHPSESSID'
// Locale storage key used by vue-i18n (see src/locales/index.js)
const LOCALE_KEY = 'lang'

// 创建 axios 实例
const request = axios.create({
  // API 请求的默认前缀
  // 生产环境应由 Nginx 处理，开发环境由 devServer proxy 处理
  baseURL: '/',
  timeout: 30000, // 请求超时时间 (30秒 - 支持慢速API)
  withCredentials: true // 允许携带 cookies
})

// 异常拦截处理器
const errorHandler = (error) => {
  if (error.response) {
    const data = error.response.data
    if (error.response.status === 403) {
      notification.error({
        message: 'Forbidden',
        description: data.message
      })
    }
    if (error.response.status === 401 && !(data.result && data.result.isLogin)) {
      notification.error({
        message: 'Unauthorized',
        description: 'Authorization verification failed'
      })
      // 不清理本地 token，避免刷新后丢失登录态；仅跳转到登录页
      const loginPath = '/user/login'
      const cur = window.location.pathname + window.location.search
      if (!cur.includes('/user/login')) {
        const redirect = encodeURIComponent(cur)
        window.location.assign(`${loginPath}?redirect=${redirect}`)
      }
    }
  }
  return Promise.reject(error)
}

// request interceptor
request.interceptors.request.use(config => {
  const token = storage.get(ACCESS_TOKEN)
  const lang = storage.get(LOCALE_KEY) || 'en-US'

  // Tell backend which UI language user is using, so AI reports can match it.
  // We keep both a custom header and the standard Accept-Language for compatibility.
  config.headers['X-App-Lang'] = lang
  config.headers['Accept-Language'] = lang

  // 如果 token 存在，将 token 添加到请求头
  if (token) {
    // 使用 Authorization header，格式为 Bearer {token}
    config.headers['Authorization'] = `Bearer ${token}`
    // 同时保留原有的 Access-Token header（如果后端需要）
    config.headers[ACCESS_TOKEN] = token
    // 兼容后端要求的 token 头
    config.headers['token'] = token
  }

  // 防止缓存导致的 304：为请求添加禁止缓存的头
  config.headers['Cache-Control'] = 'no-cache'
  config.headers['Pragma'] = 'no-cache'
  config.headers['If-Modified-Since'] = '0'

  // 为 GET 请求添加时间戳参数，避免缓存
  if ((config.method || 'get').toLowerCase() === 'get') {
    const ts = Date.now()
    config.params = Object.assign({}, config.params || {}, { _t: ts })
  }

  // 手动设置 PHPSESSID cookie，确保每次请求使用相同的 session
  // 注意：浏览器不允许手动设置 Cookie 请求头，需要通过 document.cookie 设置
  // 但由于跨域限制，可能无法直接设置 cookie，主要依赖 withCredentials: true
  const phpsessid = storage.get(PHPSESSID_KEY)
  if (phpsessid && typeof document !== 'undefined') {
    // 检查当前 document.cookie 中的 PHPSESSID
    const currentCookies = document.cookie
    const currentPhpsessidMatch = currentCookies.match(/PHPSESSID=([^;]+)/i)
    const currentPhpsessid = currentPhpsessidMatch ? currentPhpsessidMatch[1].trim() : null

    // 如果当前 cookie 中的 PHPSESSID 与保存的不一致，尝试更新
    // 注意：跨域情况下可能无法设置 cookie，这取决于 CORS 配置
    if (!currentPhpsessid || currentPhpsessid !== phpsessid) {
      // 尝试设置 cookie（可能因为跨域而失败，但不影响 withCredentials 的工作）
      try {
        // 尝试设置带 domain 的 cookie（仅当在相同域名下时有效）
        if (window.location.hostname.includes('quantdinger.com')) {
          document.cookie = `PHPSESSID=${phpsessid}; path=/; domain=.quantdinger.com; SameSite=None; Secure`
        } else {
          // 跨域情况下，只能依赖 withCredentials: true 和服务器设置
          // 这里尝试设置，但可能不会成功
          document.cookie = `PHPSESSID=${phpsessid}; path=/; SameSite=None; Secure`
        }
      } catch (e) {
        // 设置失败是正常的（跨域限制），主要依赖 withCredentials
      }
    }
  }

  return config
}, errorHandler)

// response interceptor
request.interceptors.response.use((response) => {
  // 从响应中提取 PHPSESSID 并保存
  // 由于浏览器安全限制，无法直接读取 set-cookie 头，需要通过 document.cookie 获取
  try {
    if (typeof document !== 'undefined') {
      // 从 document.cookie 获取 PHPSESSID（浏览器自动设置的）
      const cookies = document.cookie
      const phpsessidMatch = cookies.match(/PHPSESSID=([^;]+)/i)
      if (phpsessidMatch && phpsessidMatch[1]) {
        const phpsessid = phpsessidMatch[1].trim()
        // 保存 PHPSESSID 到 storage，有效期 24 小时
        const savedPhpsessid = storage.get(PHPSESSID_KEY)
        // 如果 PHPSESSID 发生变化，更新保存的值
        if (!savedPhpsessid || savedPhpsessid !== phpsessid) {
          storage.set(PHPSESSID_KEY, phpsessid, new Date().getTime() + 24 * 60 * 60 * 1000)
        }
      }
    }
  } catch (e) {
  }

  return response.data
}, errorHandler)

const installer = {
  vm: {},
  install (Vue) {
    Vue.use(VueAxios, request)
  }
}

export default request

export {
  installer as VueAxios,
  request as axios
}
