/**
 * HAMA (Heiken Ashi Moving Average) 指标
 * 转换自 Pine Script 版本
 * 用于 KlineCharts 图表库
 */

/**
 * 计算 EMA (指数移动平均)
 * @param {Array} dataList - 数据数组
 * @param {Number} period - 周期
 * @returns {Array} EMA 值数组
 */
function calculateEMA (dataList, period) {
  const result = []
  const multiplier = 2 / (period + 1)

  for (let i = 0; i < dataList.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else if (i === period - 1) {
      // 第一個 EMA 值使用 SMA
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += dataList[j]
      }
      result.push(sum / period)
    } else {
      // 后续使用 EMA 公式
      const ema = (dataList[i] - result[i - 1]) * multiplier + result[i - 1]
      result.push(ema)
    }
  }

  return result
}

/**
 * 计算 WMA (加权移动平均)
 * @param {Array} dataList - 数据数组
 * @param {Number} period - 周期
 * @returns {Array} WMA 值数组
 */
function calculateWMA (dataList, period) {
  const result = []

  for (let i = 0; i < dataList.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      let weightSum = 0

      for (let j = 0; j < period; j++) {
        sum += dataList[i - j] * (period - j)
        weightSum += (period - j)
      }

      result.push(sum / weightSum)
    }
  }

  return result
}

/**
 * 计算 SMA (简单移动平均)
 * @param {Array} dataList - 数据数组
 * @param {Number} period - 周期
 * @returns {Array} SMA 值数组
 */
function calculateSMA (dataList, period) {
  const result = []

  for (let i = 0; i < dataList.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += dataList[i - j]
      }
      result.push(sum / period)
    }
  }

  return result
}

/**
 * 计算 HAMA 指标
 * @param {Array} klineData - K线数据数组 [{open, high, low, close, volume, time}]
 * @param {Object} options - 配置选项
 * @returns {Object} HAMA 指标结果
 */
export function calculateHAMA (klineData, options = {}) {
  const {
    openLength = 45,
    openType = 'EMA',
    highLength = 20,
    highType = 'EMA',
    lowLength = 20,
    lowType = 'EMA',
    closeLength = 40,
    closeType = 'WMA',
    maLength = 100,
    maType = 'WMA',
    bbLength = 400,
    bbMult = 2.0
  } = options

  // 提取 OHLC 数据
  const closeData = klineData.map(k => k.close)

  // 计算 HAMA 蜡烛图的源数据
  const sourceOpen = []
  const sourceHigh = []
  const sourceLow = []
  const sourceClose = []

  for (let i = 0; i < klineData.length; i++) {
    if (i === 0) {
      sourceOpen.push(klineData[i].open)
      sourceHigh.push(Math.max(klineData[i].high, klineData[i].close))
      sourceLow.push(Math.min(klineData[i].low, klineData[i].close))
      sourceClose.push((klineData[i].open + klineData[i].high + klineData[i].low + klineData[i].close) / 4)
    } else {
      sourceOpen.push((klineData[i - 1].open + klineData[i - 1].close) / 2)
      sourceHigh.push(Math.max(klineData[i].high, klineData[i].close))
      sourceLow.push(Math.min(klineData[i].low, klineData[i].close))
      sourceClose.push((klineData[i].open + klineData[i].high + klineData[i].low + klineData[i].close) / 4)
    }
  }

  // 计算 HAMA 蜡烛图
  const hamaOpen = calculateMA(sourceOpen, openLength, openType)
  const hamaHigh = calculateMA(sourceHigh, highLength, highType)
  const hamaLow = calculateMA(sourceLow, lowLength, lowType)
  const hamaClose = calculateMA(sourceClose, closeLength, closeType)

  // 计算 MA 线
  const ma = calculateMA(hamaClose, maLength, maType)

  // 计算布林带
  const bbBasis = calculateSMA(closeData, bbLength)
  const bbStdDev = []
  for (let i = 0; i < closeData.length; i++) {
    if (i < bbLength - 1) {
      bbStdDev.push(null)
    } else {
      // 计算标准差
      let sumSquaredDiff = 0
      for (let j = 0; j < bbLength; j++) {
        const diff = closeData[i - j] - bbBasis[i]
        sumSquaredDiff += diff * diff
      }
      bbStdDev.push(Math.sqrt(sumSquaredDiff / bbLength))
    }
  }

  const bbUpper = bbBasis.map((basis, i) => {
    if (basis === null || bbStdDev[i] === null) return null
    return basis + bbStdDev[i] * bbMult
  })

  const bbLower = bbBasis.map((basis, i) => {
    if (basis === null || bbStdDev[i] === null) return null
    return basis - bbStdDev[i] * bbMult
  })

  // 计算 HAMA 颜色
  const hamaColors = []
  for (let i = 0; i < hamaClose.length; i++) {
    if (hamaClose[i] === null || hamaOpen[i] === null) {
      hamaColors.push(null)
    } else {
      // 上涨为绿色,下跌为红色
      hamaColors.push(hamaClose[i] >= hamaOpen[i] ? '#26a69a' : '#ef5350')
    }
  }

  // 计算交叉信号
  const crossUp = []
  const crossDown = []
  for (let i = 1; i < hamaClose.length; i++) {
    if (hamaClose[i] === null || hamaClose[i - 1] === null || ma[i] === null || ma[i - 1] === null) {
      crossUp.push(null)
      crossDown.push(null)
    } else {
      // 金叉: HAMA 从下向上穿过 MA
      crossUp.push(
        hamaClose[i - 1] <= ma[i - 1] && hamaClose[i] > ma[i]
      )
      // 死叉: HAMA 从上向下穿过 MA
      crossDown.push(
        hamaClose[i - 1] >= ma[i - 1] && hamaClose[i] < ma[i]
      )
    }
  }

  return {
    hama: {
      open: hamaOpen,
      high: hamaHigh,
      low: hamaLow,
      close: hamaClose,
      colors: hamaColors,
      ma: ma
    },
    bollingerBands: {
      basis: bbBasis,
      upper: bbUpper,
      lower: bbLower,
      stdDev: bbStdDev
    },
    signals: {
      crossUp,
      crossDown
    }
  }
}

/**
 * 计算 MA (通用函数)
 */
function calculateMA (dataList, period, type = 'SMA') {
  switch (type) {
    case 'EMA':
      return calculateEMA(dataList, period)
    case 'WMA':
      return calculateWMA(dataList, period)
    case 'SMA':
    default:
      return calculateSMA(dataList, period)
  }
}
