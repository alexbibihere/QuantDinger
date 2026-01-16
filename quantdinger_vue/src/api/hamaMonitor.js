/**
 * HAMA信号监控API
 */
import request from '@/utils/request'

/**
 * 获取监控状态
 */
export function getMonitorStatus () {
  return request({
    url: '/api/hama-monitor/status',
    method: 'get'
  })
}

/**
 * 启动监控服务
 */
export function startMonitor () {
  return request({
    url: '/api/hama-monitor/start',
    method: 'post'
  })
}

/**
 * 停止监控服务
 */
export function stopMonitor () {
  return request({
    url: '/api/hama-monitor/stop',
    method: 'post'
  })
}

/**
 * 获取监控币种列表
 */
export function getMonitoredSymbols () {
  return request({
    url: '/api/hama-monitor/symbols',
    method: 'get'
  })
}

/**
 * 添加监控币种
 * @param {Object} data { symbol: string, market_type: string }
 */
export function addSymbol (data) {
  return request({
    url: '/api/hama-monitor/symbols/add',
    method: 'post',
    data
  })
}

/**
 * 按需计算单个币种的HAMA状态
 * @param {Object} data { symbol: string, market_type?: string }
 */
export function calculateHama (data) {
  return request({
    url: '/api/hama-monitor/calculate',
    method: 'post',
    data
  })
}

/**
 * 移除监控币种
 * @param {Object} data { symbol: string }
 */
export function removeSymbol (data) {
  return request({
    url: '/api/hama-monitor/symbols/remove',
    method: 'post',
    data
  })
}

/**
 * 添加涨幅榜前N名到监控
 * @param {Object} data { limit: number, market: string }
 */
export function addTopGainers (data) {
  return request({
    url: '/api/hama-monitor/symbols/add-top-gainers',
    method: 'post',
    data
  })
}

/**
 * 获取信号历史
 * @param {Object} params { limit: number }
 */
export function getSignals (params = {}) {
  return request({
    url: '/api/hama-monitor/signals',
    method: 'get',
    params
  })
}

/**
 * 清空信号历史
 */
export function clearSignals () {
  return request({
    url: '/api/hama-monitor/clear-signals',
    method: 'post'
  })
}

/**
 * 获取监控配置
 */
export function getMonitorConfig () {
  return request({
    url: '/api/hama-monitor/config',
    method: 'get'
  })
}

/**
 * 更新监控配置
 * @param {Object} data { check_interval: number, signal_cooldown: number }
 */
export function updateMonitorConfig (data) {
  return request({
    url: '/api/hama-monitor/config',
    method: 'post',
    data
  })
}
