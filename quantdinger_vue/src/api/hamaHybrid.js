/**
 * HAMA指标混合模式API
 * 结合后端计算和Selenium的优势
 */
import request from '@/utils/request'

/**
 * 获取单个币种的HAMA指标(混合模式)
 * @param {string} symbol 币种符号,如 'BTCUSDT'
 * @param {object} options 参数选项
 * @param {string} options.interval 时间间隔,默认'15'
 * @param {boolean} options.useSelenium 是否强制使用Selenium,默认false
 * @param {boolean} options.forceRefresh 是否强制刷新缓存,默认false
 */
export function getHAMAIndicator (symbol, options = {}) {
  const { interval = '15', useSelenium = false, forceRefresh = false } = options

  return request({
    url: `/api/tradingview-selenium/hama-hybrid/${symbol}`,
    method: 'get',
    params: {
      interval,
      use_selenium: useSelenium.toString(),
      force_refresh: forceRefresh.toString()
    }
  })
}

/**
 * 批量获取多个币种的HAMA指标(混合模式+并行)
 * @param {array} symbols 币种符号数组
 * @param {object} options 参数选项
 * @param {string} options.interval 时间间隔,默认'15'
 * @param {boolean} options.useSelenium 是否强制使用Selenium,默认false
 * @param {number} options.maxParallel 最大并行数,默认5
 */
export function getBatchHAMAIndicators (symbols, options = {}) {
  const { interval = '15', useSelenium = false, maxParallel = 5 } = options

  // 根据币种数量动态计算超时时间 (每个币种约60秒,加上缓冲时间)
  const estimatedTime = symbols.length * 60 * 1000 // 每个币种60秒
  const timeout = Math.max(600000, estimatedTime) // 最少10分钟,最多根据币种数量

  console.log(`[HAMA] 批量请求 ${symbols.length} 个币种,超时时间: ${timeout / 1000} 秒`)

  return request({
    url: '/api/tradingview-selenium/hama-hybrid/batch',
    method: 'post',
    timeout: timeout, // 动态超时时间
    data: {
      symbols,
      interval,
      use_selenium: useSelenium,
      max_parallel: maxParallel
    }
  })
}

/**
 * 获取HAMA交叉信号
 * @param {string} symbol 币种符号
 * @param {string} interval 时间间隔,默认'15'
 */
export function getHAMACrossSignals (symbol, interval = '15') {
  return request({
    url: `/api/tradingview-selenium/hama-cross-signals/${symbol}`,
    method: 'get',
    params: { interval }
  })
}
