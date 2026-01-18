/**
 * HAMA 行情 API
 */
import { axios } from '@/utils/request'

const API_PREFIX = '/api/hama-market'

/**
 * 获取 HAMA 监控列表
 * @param {Object} params - { symbols: string, market: string }
 * @returns {Promise}
 */
export function getHamaWatchlist (params) {
  return axios({
    url: `${API_PREFIX}/watchlist`,
    method: 'get',
    params
  })
}

/**
 * 获取单个币种的 HAMA 指标
 * @param {Object} params - { symbol: string, interval: string, limit: number }
 * @returns {Promise}
 */
export function getHamaSymbol (params) {
  return axios({
    url: `${API_PREFIX}/symbol`,
    method: 'get',
    params
  })
}

/**
 * 获取 HAMA 信号列表
 * @param {Object} params - { symbols: string }
 * @returns {Promise}
 */
export function getHamaSignals (params) {
  return axios({
    url: `${API_PREFIX}/signals`,
    method: 'get',
    params
  })
}

/**
 * 获取热门币种列表
 * @returns {Promise}
 */
export function getHotSymbols () {
  return axios({
    url: `${API_PREFIX}/hot-symbols`,
    method: 'get'
  })
}

/**
 * 健康检查
 * @returns {Promise}
 */
export function healthCheck () {
  return axios({
    url: `${API_PREFIX}/health`,
    method: 'get'
  })
}

/**
 * 获取 Brave 监控器状态
 * @returns {Promise}
 */
export function getBraveStatus () {
  return axios({
    url: `${API_PREFIX}/brave/status`,
    method: 'get'
  })
}

/**
 * 手动触发 Brave 监控
 * @param {Object} data - { symbols: array, browser_type: string }
 * @returns {Promise}
 */
export function triggerBraveMonitor (data) {
  return axios({
    url: `${API_PREFIX}/brave/monitor`,
    method: 'post',
    data
  })
}

/**
 * 启动持续监控
 * @param {Object} data - { symbols: array, interval: number, browser_type: string }
 * @returns {Promise}
 */
export function startBraveMonitoring (data) {
  return axios({
    url: `${API_PREFIX}/brave/start`,
    method: 'post',
    data
  })
}

/**
 * 停止持续监控
 * @returns {Promise}
 */
export function stopBraveMonitoring () {
  return axios({
    url: `${API_PREFIX}/brave/stop`,
    method: 'post'
  })
}

/**
 * OCR 识别单个币种的 HAMA 指标
 * @param {Object} data - { symbol: string, tv_url: string }
 * @returns {Promise}
 */
export function ocrCapture (data) {
  return axios({
    url: `${API_PREFIX}/ocr/capture`,
    method: 'post',
    data
  })
}

/**
 * OCR 批量识别多个币种的 HAMA 指标
 * @param {Object} data - { symbols: array }
 * @returns {Promise}
 */
export function ocrBatchCapture (data) {
  return axios({
    url: `${API_PREFIX}/ocr/batch`,
    method: 'post',
    data
  })
}

// ==================== 币种管理 API ====================

/**
 * 获取币种列表
 * @param {Object} params - { enabled: boolean, market: string }
 * @returns {Promise}
 */
export function getSymbolsList (params) {
  return axios({
    url: `${API_PREFIX}/symbols/list`,
    method: 'get',
    params
  })
}

/**
 * 添加新币种
 * @param {Object} data - { symbol: string, symbol_name: string, market: string, enabled: boolean, priority: number, notify_enabled: boolean, notify_threshold: number, notes: string }
 * @returns {Promise}
 */
export function addSymbol (data) {
  return axios({
    url: `${API_PREFIX}/symbols/add`,
    method: 'post',
    data
  })
}

/**
 * 更新币种信息
 * @param {Object} data - { symbol: string, symbol_name: string, market: string, enabled: boolean, priority: number, notify_enabled: boolean, notify_threshold: number, notes: string }
 * @returns {Promise}
 */
export function updateSymbol (data) {
  return axios({
    url: `${API_PREFIX}/symbols/update`,
    method: 'post',
    data
  })
}

/**
 * 删除币种
 * @param {Object} data - { symbol: string }
 * @returns {Promise}
 */
export function deleteSymbol (data) {
  return axios({
    url: `${API_PREFIX}/symbols/delete`,
    method: 'post',
    data
  })
}

/**
 * 启用/禁用币种
 * @param {Object} data - { symbol: string, enabled: boolean }
 * @returns {Promise}
 */
export function toggleSymbol (data) {
  return axios({
    url: `${API_PREFIX}/symbols/enable`,
    method: 'post',
    data
  })
}

/**
 * 批量启用/禁用币种
 * @param {Object} data - { symbols: array, enabled: boolean }
 * @returns {Promise}
 */
export function batchEnableSymbols (data) {
  return axios({
    url: `${API_PREFIX}/symbols/batch-enable`,
    method: 'post',
    data
  })
}
