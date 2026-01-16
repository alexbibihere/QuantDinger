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
