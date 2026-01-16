import request from '@/utils/request'

const api = {
  watchlist: '/api/tradingview-scanner/watchlist',
  perpetuals: '/api/tradingview-scanner/perpetuals',
  topGainers: '/api/tradingview-scanner/top-gainers',
  symbols: '/api/tradingview-scanner/symbols',
  stats: '/api/tradingview-scanner/stats'
}

/**
 * 获取默认关注列表
 * @param {Object} params
 * @param {number} params.limit - 限制返回数量 (默认20,最多100)
 */
export function getWatchlist (params = {}) {
  return request({
    url: api.watchlist,
    method: 'get',
    params
  })
}

/**
 * 获取币安永续合约列表
 * @param {Object} params
 * @param {number} params.limit - 限制返回数量 (默认50,最多200)
 */
export function getPerpetuals (params = {}) {
  return request({
    url: api.perpetuals,
    method: 'get',
    params
  })
}

/**
 * 获取涨幅榜
 * @param {Object} params
 * @param {number} params.limit - 限制返回数量 (默认20,最多100)
 * @param {number} params.min_change - 最小涨跌幅百分比 (可选)
 */
export function getTopGainers (params = {}) {
  return request({
    url: api.topGainers,
    method: 'get',
    params
  })
}

/**
 * 获取指定币种数据
 * @param {Object} data
 * @param {string[]} data.symbols - 币种列表,如 ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"]
 */
export function getSymbolsData (data) {
  return request({
    url: api.symbols,
    method: 'post',
    data
  })
}

/**
 * 获取统计信息
 */
export function getStats () {
  return request({
    url: api.stats,
    method: 'get'
  })
}

/**
 * 获取图表截图
 * @param {Object} params
 * @param {string} params.symbol - 币种符号
 * @param {string} params.interval - 时间周期
 */
export function getChartScreenshot (params = {}) {
  return request({
    url: '/api/tradingview-scanner/chart-screenshot',
    method: 'get',
    params
  })
}
