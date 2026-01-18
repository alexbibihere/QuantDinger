/**
 * HAMA 指标注册器
 * 将 HAMA 指标注册到 KlineCharts 图表
 */

import { calculateHAMA } from './hamaIndicator'

/**
 * 注册 HAMA 指标到 KlineCharts
 * @param {Object} chart - KlineCharts 图表实例
 * @param {Array} klineData - K线数据
 * @returns {Object} 指标配置
 */
export function registerHAMAIndicator (chart, klineData = []) {
  // 创建 HAMA 蜡烛图指标
  const hamaCandleIndicator = {
    name: 'HAMA',
    shortName: 'HAMA',
    series: 'candle_stick',
    calcParams: [45, 20, 20, 40],
    figures: [
      {
        key: 'open',
        title: 'Open',
        type: 'candle_stick'
      },
      {
        key: 'high',
        title: 'High',
        type: 'candle_stick'
      },
      {
        key: 'low',
        title: 'Low',
        type: 'candle_stick'
      },
      {
        key: 'close',
        title: 'Close',
        type: 'candle_stick'
      }
    ],
    calc: (dataList) => {
      // 计算 HAMA 数据
      const hamaResult = calculateHAMA(dataList)
      const result = []

      for (let i = 0; i < dataList.length; i++) {
        result.push({
          open: hamaResult.hama.open[i] || null,
          high: hamaResult.hama.high[i] || null,
          low: hamaResult.hama.low[i] || null,
          close: hamaResult.hama.close[i] || null,
          timestamp: dataList[i].timestamp
        })
      }

      return result
    }
  }

  // 创建 MA 线指标
  const maIndicator = {
    name: 'HAMA_MA',
    shortName: 'MA',
    series: 'line',
    calcParams: [100],
    figures: [{
      key: 'ma',
      title: 'MA',
      type: 'line'
    }],
    calc: (dataList) => {
      const hamaResult = calculateHAMA(dataList)
      const result = []

      for (let i = 0; i < dataList.length; i++) {
        result.push({
          ma: hamaResult.hama.ma[i] || null,
          timestamp: dataList[i].timestamp
        })
      }

      return result
    }
  }

  // 创建布林带指标
  const bbIndicator = {
    name: 'HAMA_BB',
    shortName: 'BB',
    series: 'line',
    calcParams: [400, 2],
    figures: [
      {
        key: 'upper',
        title: '上轨',
        type: 'line'
      },
      {
        key: 'basis',
        title: '中轨',
        type: 'line'
      },
      {
        key: 'lower',
        title: '下轨',
        type: 'line'
      }
    ],
    calc: (dataList) => {
      const hamaResult = calculateHAMA(dataList)
      const result = []

      for (let i = 0; i < dataList.length; i++) {
        result.push({
          upper: hamaResult.bollingerBands.upper[i] || null,
          basis: hamaResult.bollingerBands.basis[i] || null,
          lower: hamaResult.bollingerBands.lower[i] || null,
          timestamp: dataList[i].timestamp
        })
      }

      return result
    }
  }

  // 注册所有指标
  try {
    // 先注册指标模板
    if (typeof chart.registerIndicator === 'function') {
      chart.registerIndicator(hamaCandleIndicator)
      chart.registerIndicator(maIndicator)
      chart.registerIndicator(bbIndicator)
    }

    // 创建指标实例
    const paneId1 = chart.createIndicator(hamaCandleIndicator, false, { id: 'candle_pane' })
    const paneId2 = chart.createIndicator(maIndicator, false, { id: 'candle_pane' })
    const paneId3 = chart.createIndicator(bbIndicator, false, { id: 'candle_pane' })

    console.log('✅ HAMA 指标已成功注册到 KlineCharts')
    return {
      success: true,
      indicators: ['HAMA', 'HAMA_MA', 'HAMA_BB'],
      panes: [paneId1, paneId2, paneId3]
    }
  } catch (error) {
    console.error('❌ 注册 HAMA 指标失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 移除 HAMA 指标
 * @param {Object} chart - KlineCharts 图表实例
 */
export function removeHAMAIndicator (chart) {
  try {
    // 尝试按名称移除
    if (typeof chart.removeIndicator === 'function') {
      try { chart.removeIndicator('candle_pane', 'HAMA') } catch (e) {}
      try { chart.removeIndicator('candle_pane', 'HAMA_MA') } catch (e) {}
      try { chart.removeIndicator('candle_pane', 'HAMA_BB') } catch (e) {}
    }

    console.log('✅ HAMA 指标已移除')
    return true
  } catch (error) {
    console.error('❌ 移除 HAMA 指标失败:', error)
    return false
  }
}

/**
 * 更新 HAMA 指标数据
 * @param {Object} chart - KlineCharts 图表实例
 * @param {Array} klineData - 新的K线数据
 */
export function updateHAMAIndicator (chart, klineData) {
  // 先移除旧指标
  removeHAMAIndicator(chart)

  // 重新计算并注册
  return registerHAMAIndicator(chart, klineData)
}
