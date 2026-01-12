/**
 * 多交易所涨幅榜对比 API
 */
import request from '@/utils/request'

/**
 * 对比多个交易所的涨幅榜数据
 * @param {Object} params
 * @param {String} params.market - 市场类型 spot/futures
 * @param {Number} params.limit - 返回数量
 */
export function compareExchanges (params) {
  return request({
    url: '/api/multi-exchange/compare',
    method: 'get',
    params
  })
}

/**
 * 获取Binance涨幅榜
 * @param {Object} params
 * @param {String} params.market - 市场类型 spot/futures
 * @param {Number} params.limit - 返回数量
 */
export function getBinanceGainers (params) {
  return request({
    url: '/api/multi-exchange/binance',
    method: 'get',
    params
  })
}

/**
 * 获取OKX涨幅榜
 * @param {Object} params
 * @param {String} params.market - 市场类型 spot/futures
 * @param {Number} params.limit - 返回数量
 */
export function getOKXGainers (params) {
  return request({
    url: '/api/multi-exchange/okx',
    method: 'get',
    params
  })
}
