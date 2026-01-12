import request from '@/utils/request'

/**
 * 获取币种的 MA100 数据
 */
export function getMA100Data (symbol, interval = '15m') {
  return request({
    url: '/api/indicator/verifyCode',
    method: 'post',
    data: {
      code: `import pandas as pd\nimport numpy as np\n\ndef calculate(df):\n    df = df.copy()\n    df['ma100'] = df['close'].rolling(window=100).mean()\n    return df`,
      symbol: symbol,
      interval: interval,
      limit: 200
    }
  })
}
