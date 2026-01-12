/**
 * 涨幅榜统计分析API
 */
import request from '@/utils/request'

/**
 * 获取最常出现在涨幅榜的币种
 * @param {Object} options 参数选项
 * @param {number} options.limit 返回数量,默认20
 * @param {number} options.days 统计最近多少天,默认7
 */
export function getFrequentSymbols (options = {}) {
  const { limit = 20, days = 7 } = options

  return request({
    url: '/api/gainer-stats/frequent-symbols',
    method: 'get',
    params: {
      limit,
      days
    }
  })
}

/**
 * 获取指定币种的出现记录
 * @param {string} symbol 币种符号
 * @param {Object} options 参数选项
 * @param {number} options.days 查询最近多少天,默认30
 */
export function getSymbolAppearances (symbol, options = {}) {
  const { days = 30 } = options

  return request({
    url: `/api/gainer-stats/symbol/${symbol}/appearances`,
    method: 'get',
    params: {
      days
    }
  })
}

/**
 * 获取今天出现在涨幅榜的币种列表
 */
export function getTodayAppearances () {
  return request({
    url: '/api/gainer-stats/today',
    method: 'get'
  })
}

/**
 * 手动记录涨幅榜出现(用于测试)
 * @param {Object} data 记录数据
 * @param {Array<string>} data.symbols 币种列表
 * @param {string} data.date 日期字符串(可选)
 */
export function recordAppearances (data) {
  return request({
    url: '/api/gainer-stats/record',
    method: 'post',
    data
  })
}
