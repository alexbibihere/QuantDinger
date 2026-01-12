import request from '@/utils/request'

const api = {
  topGainers: '/api/gainer-analysis/top-gainers',
  analyzeSymbol: '/api/gainer-analysis/analyze-symbol',
  refresh: '/api/gainer-analysis/refresh'
}

/**
 * 获取涨幅榜和 HAMA 指标分析
 * @param {Object} params
 * @param {number} params.limit - 返回数量，默认 20
 * @param {string} params.market - 市场类型 (spot/futures)，默认 spot
 */
export function getTopGainers (params = {}) {
  return request({
    url: api.topGainers,
    method: 'get',
    params
  })
}

/**
 * 分析单个币种的 HAMA 指标
 * @param {Object} data
 * @param {string} data.symbol - 币种符号，如 BTCUSDT
 */
export function analyzeSymbol (data) {
  return request({
    url: api.analyzeSymbol,
    method: 'post',
    data
  })
}

/**
 * 刷新涨幅榜和分析数据
 * @param {Object} data
 * @param {number} data.limit - 返回数量，默认 20
 * @param {string} data.market - 市场类型 (spot/futures)，默认 spot
 */
export function refreshAnalysis (data = {}) {
  return request({
    url: api.refresh,
    method: 'post',
    data
  })
}
