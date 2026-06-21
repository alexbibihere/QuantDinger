/**
 * 呱呱选币 API - 使用原生 fetch 绕过 Axios 拦截器
 */

const API_BASE = '/api/guagua'

async function guaguaFetch (url, params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') query.append(k, v)
  })
  const qs = query.toString()
  const fullUrl = qs ? `${url}?${qs}` : url
  const res = await fetch(fullUrl)
  // 先检查 HTTP 状态码，如果失败则读取文本错误信息
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
  }
  // 尝试解析 JSON，如果后端返回了非 JSON 内容（如 Flask 500 HTML 页面），也抛出友好错误
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json') && !contentType.includes('text/json')) {
    const text = await res.text()
    throw new Error(`返回内容不是JSON (${contentType || '未知类型'}): ${text.slice(0, 200)}`)
  }
  return res.json()
}

/**
 * 获取呱呱选币信号数据
 */
export function getGuaguaSignals (params = {}) {
  return guaguaFetch(`${API_BASE}/signals`, params)
}

/**
 * 获取呱呱选币汇总统计
 */
export function getGuaguaSummary () {
  return guaguaFetch(`${API_BASE}/summary`)
}

/**
 * 获取呱呱选币观点分享
 */
export function getGuaguaPosts (limit = 10) {
  return guaguaFetch(`${API_BASE}/posts`, { limit })
}

/**
 * 检测呱呱选币连接状态
 */
export function getGuaguaHealth () {
  return guaguaFetch(`${API_BASE}/health`)
}
