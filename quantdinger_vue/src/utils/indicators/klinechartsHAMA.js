/**
 * HAMA 指标配置 (用于 klinecharts)
 * 转换自 Pine Script 版本
 */

import { calculateHAMA } from './hamaIndicator'

/**
 * HAMA 指标配置
 * 符合 klinecharts v9 的指标注册格式
 */
export const HAMAIndicator = {
  id: 'HAMA',
  name: 'HAMA蜡烛图',
  shortName: 'HAMA',
  description: 'Heiken Ashi Moving Average 蜡烛图 + 布林带',
  type: 'candle',

  // 默认参数
  defaultParameters: {
    // HAMA 参数
    openLength: 45,
    openType: 'EMA',
    highLength: 20,
    highType: 'EMA',
    lowLength: 20,
    lowType: 'EMA',
    closeLength: 40,
    closeType: 'WMA',

    // MA 线参数
    maLength: 100,
    maType: 'WMA',

    // 布林带参数
    bbLength: 400,
    bbMult: 2.0,

    // 样式参数
    bullColor: '#00FF00',
    bearColor: '#FF0000',
    neutralColor: '#FFFF00',
    wickColor: 'rgba(128, 128, 128, 0.4)',
    useGradient: true,
    showMA: true
  },

  // 参数定义
  parameterDefinitions: [
    { name: 'openLength', title: '开盘价长度', type: 'number', min: 1, max: 200, default: 45 },
    { name: 'openType', title: '开盘价类型', type: 'select', options: ['EMA', 'SMA', 'WMA'], default: 'EMA' },
    { name: 'highLength', title: '最高价长度', type: 'number', min: 1, max: 200, default: 20 },
    { name: 'highType', title: '最高价类型', type: 'select', options: ['EMA', 'SMA', 'WMA'], default: 'EMA' },
    { name: 'lowLength', title: '最低价长度', type: 'number', min: 1, max: 200, default: 20 },
    { name: 'lowType', title: '最低价类型', type: 'select', options: ['EMA', 'SMA', 'WMA'], default: 'EMA' },
    { name: 'closeLength', title: '收盘价长度', type: 'number', min: 1, max: 200, default: 40 },
    { name: 'closeType', title: '收盘价类型', type: 'select', options: ['EMA', 'SMA', 'WMA'], default: 'WMA' },
    { name: 'maLength', title: 'MA线长度', type: 'number', min: 1, max: 500, default: 100 },
    { name: 'maType', title: 'MA线类型', type: 'select', options: ['EMA', 'SMA', 'WMA'], default: 'WMA' },
    { name: 'bbLength', title: '布林带周期', type: 'number', min: 1, max: 500, default: 400 },
    { name: 'bbMult', title: '布林带倍数', type: 'number', min: 0.1, max: 5, step: 0.1, default: 2.0 },
    { name: 'bullColor', title: '牛市颜色', type: 'color', default: '#00FF00' },
    { name: 'bearColor', title: '熊市颜色', type: 'color', default: '#FF0000' },
    { name: 'useGradient', title: '使用渐变', type: 'boolean', default: true },
    { name: 'showMA', title: '显示MA线', type: 'boolean', default: true }
  ],

  // 样式定义
  styles: {
    candle: {
      type: 'candle',
      title: 'HAMA蜡烛',
      candleType: 'candle', // area, candle, bar, line
      bar: {
        upColor: '#00FF00',
        downColor: '#FF0000',
        noChangeColor: '#888888'
      },
      tooltip: []
    },
    ma: {
      type: 'line',
      title: 'MA线',
      color: '#FFD700',
      lineWidth: 2,
      smooth: false
    },
    bbUpper: {
      type: 'line',
      title: '布林带上轨',
      color: '#FFA500',
      lineWidth: 1,
      smooth: true
    },
    bbLower: {
      type: 'line',
      title: '布林带下轨',
      color: '#FF0000',
      lineWidth: 1,
      smooth: true
    },
    bbBasis: {
      type: 'line',
      title: '布林带中轨',
      color: '#800080',
      lineWidth: 1,
      smooth: true
    }
  },

  // 计算函数
  calc: (klineData, parameters = {}) => {
    const params = { ...HAMAIndicator.defaultParameters, ...parameters }

    // 使用已有的 HAMA 计算函数
    const result = calculateHAMA(klineData, params)

    // 转换为 klinecharts 期望的格式
    const formattedResult = {
      candle: [], // HAMA 蜡烛图数据
      ma: [], // MA 线数据
      bbUpper: [], // 布林带上轨
      bbLower: [], // 布林带下轨
      bbBasis: [] // 布林带中轨
    }

    // 格式化蜡烛图数据
    if (result.hama) {
      for (let i = 0; i < klineData.length; i++) {
        const timestamp = klineData[i].timestamp
        const hamaOpen = result.hama.open[i]
        const hamaHigh = result.hama.high[i]
        const hamaLow = result.hama.low[i]
        const hamaClose = result.hama.close[i]
        const color = result.hama.colors[i]

        if (hamaOpen !== null && hamaOpen !== undefined) {
          formattedResult.candle.push({
            timestamp,
            open: hamaOpen,
            high: hamaHigh,
            low: hamaLow,
            close: hamaClose,
            color: color || (hamaClose >= hamaOpen ? params.bullColor : params.bearColor)
          })
        } else {
          formattedResult.candle.push({
            timestamp,
            open: 0,
            high: 0,
            low: 0,
            close: 0
          })
        }

        // MA 线
        if (result.hama.ma && result.hama.ma[i] !== null) {
          formattedResult.ma.push({
            timestamp,
            value: result.hama.ma[i]
          })
        }

        // 布林带
        if (result.bollingerBands) {
          if (result.bollingerBands.upper && result.bollingerBands.upper[i] !== null) {
            formattedResult.bbUpper.push({
              timestamp,
              value: result.bollingerBands.upper[i]
            })
          }
          if (result.bollingerBands.lower && result.bollingerBands.lower[i] !== null) {
            formattedResult.bbLower.push({
              timestamp,
              value: result.bollingerBands.lower[i]
            })
          }
          if (result.bollingerBands.basis && result.bollingerBands.basis[i] !== null) {
            formattedResult.bbBasis.push({
              timestamp,
              value: result.bollingerBands.basis[i]
            })
          }
        }
      }
    }

    return formattedResult
  },

  // 创建视图函数 (用于渲染)
  createView: (container, klineCharts, styles) => {
    // klinecharts v9 的视图创建
    // 这里返回空，因为 klinecharts 会自动处理
    return null
  },

  // 销毁视图函数
  destroyView: (view) => {
    if (view) {
      // 清理资源
    }
  }
}

/**
 * 注册 HAMA 指标到 klinecharts
 * @param {Object} chart - klinecharts 图表实例
 * @returns {Object} 指标配置
 */
export function registerHAMAIndicator (chart) {
  if (!chart) {
    console.error('图表实例不存在')
    return null
  }

  try {
    // 使用 klinecharts v9 的 API 注册指标
    const indicator = chart.createIndicator('HAMA', 'candle', true)

    // 设置指标样式
    if (indicator && HAMAIndicator.styles) {
      Object.keys(HAMAIndicator.styles).forEach(key => {
        indicator.setStyle(key, HAMAIndicator.styles[key])
      })
    }

    return indicator
  } catch (error) {
    console.error('注册 HAMA 指标失败:', error)
    return null
  }
}

/**
 * 更新 HAMA 指标数据
 * @param {Object} chart - klinecharts 图表实例
 * @param {Array} klineData - K线数据
 * @param {Object} parameters - 指标参数
 */
export function updateHAMAIndicator (chart, klineData, parameters = {}) {
  if (!chart || !klineData || klineData.length === 0) {
    return
  }

  try {
    // 计算指标数据
    HAMAIndicator.calc(klineData, parameters)

    // 更新图表上的指标
    // klinecharts v9 的更新 API
    chart.applyNewData(klineData)

    // 如果需要,可以在这里添加额外的叠加层
    // 例如: 交叉信号标签
  } catch (error) {
    console.error('更新 HAMA 指标失败:', error)
  }
}

export default HAMAIndicator
