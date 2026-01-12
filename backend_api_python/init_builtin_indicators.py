#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化内置技术指标
向数据库中添加常用的技术指标
"""
import sys
import os
import sqlite3
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 内置指标定义
BUILTIN_INDICATORS = [
    {
        'name': 'SMA 双均线策略',
        'description': '基于简单移动平均线的双均线交叉策略。当短期均线上穿长期均线时买入，下穿时卖出。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    SMA 双均线策略
    参数：
      - short_period: 短期均线周期，默认 20
      - long_period: 长期均线周期，默认 60
    """
    df = df.copy()

    # 获取参数（带默认值）
    short_period = 20
    long_period = 60

    # 计算均线
    df['sma_short'] = df['close'].rolling(window=short_period).mean()
    df['sma_long'] = df['close'].rolling(window=long_period).mean()

    # 生成信号
    df['signal'] = 'hold'
    df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 'buy'
    df.loc[df['sma_short'] < df['sma_long'], 'signal'] = 'sell'

    # 交叉点检测
    df['cross_above'] = (df['sma_short'] > df['sma_long']) & (df['sma_short'].shift(1) <= df['sma_long'].shift(1))
    df['cross_below'] = (df['sma_short'] < df['sma_long']) & (df['sma_short'].shift(1) >= df['sma_long'].shift(1))

    return df
'''
    },
    {
        'name': 'EMA 趋势策略',
        'description': '基于指数移动平均线的趋势跟踪策略。EMA 对价格变化更敏感，适合趋势明显的市场。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    EMA 趋势策略
    参数：
      - fast_period: 快速 EMA 周期，默认 12
      - slow_period: 慢速 EMA 周期，默认 26
    """
    df = df.copy()

    # 获取参数
    fast_period = 12
    slow_period = 26

    # 计算 EMA
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

    # 生成信号
    df['signal'] = 'hold'
    df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 'buy'
    df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = 'sell'

    # MACD 柱状图
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    return df
'''
    },
    {
        'name': 'RSI 相对强弱策略',
        'description': '基于 RSI 指标的超买超卖策略。RSI > 70 超买，RSI < 30 超卖。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    RSI 相对强弱策略
    参数：
      - period: RSI 周期，默认 14
      - overbought: 超买阈值，默认 70
      - oversold: 超卖阈值，默认 30
    """
    df = df.copy()

    # 获取参数
    period = 14
    overbought = 70
    oversold = 30

    # 计算 RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 生成信号
    df['signal'] = 'hold'
    df.loc[df['rsi'] < oversold, 'signal'] = 'buy'
    df.loc[df['rsi'] > overbought, 'signal'] = 'sell'

    return df
'''
    },
    {
        'name': '布林带突破策略',
        'description': '基于布林带的突破策略。价格触及下轨买入，触及上轨卖出。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    布林带突破策略
    参数：
      - period: 均线周期，默认 20
      - std_mult: 标准差倍数，默认 2
    """
    df = df.copy()

    # 获取参数
    period = 20
    std_mult = 2

    # 计算布林带
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    df['bb_std'] = df['close'].rolling(window=period).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_mult)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_mult)

    # 计算 %B (价格在布林带中的位置)
    df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # 生成信号
    df['signal'] = 'hold'
    df.loc[df['bb_percent'] < 0.2, 'signal'] = 'buy'
    df.loc[df['bb_percent'] > 0.8, 'signal'] = 'sell'

    return df
'''
    },
    {
        'name': 'MACD 策略',
        'description': '经典 MACD 策略。MACD 线上穿信号线买入，下穿卖出。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    MACD 策略
    参数：
      - fast_period: 快速 EMA，默认 12
      - slow_period: 慢速 EMA，默认 26
      - signal_period: 信号线周期，默认 9
    """
    df = df.copy()

    # 获取参数
    fast_period = 12
    slow_period = 26
    signal_period = 9

    # 计算 MACD
    ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # 生成信号
    df['signal'] = 'hold'
    df.loc[df['macd_hist'] > 0, 'signal'] = 'buy'
    df.loc[df['macd_hist'] < 0, 'signal'] = 'sell'

    # 金叉死叉检测
    df['golden_cross'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df['death_cross'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))

    return df
'''
    },
    {
        'name': 'KDJ 随机指标策略',
        'description': '基于 KDJ 指标的策略。K 线上穿 D 线且在低位买入，K 线下穿 D 线且在高位卖出。',
        'code': '''
import pandas as pd
import numpy as np

def calculate(df):
    """
    KDJ 随机指标策略
    参数：
      - period: 周期，默认 9
      - k_period: K 值平滑周期，默认 3
      - d_period: D 值平滑周期，默认 3
    """
    df = df.copy()

    # 获取参数
    period = 9
    k_period = 3
    d_period = 3

    # 计算 KDJ
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100

    df['k'] = rsv.ewm(com=k_period - 1, adjust=False).mean()
    df['d'] = df['k'].ewm(com=d_period - 1, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']

    # 生成信号
    df['signal'] = 'hold'
    df.loc[(df['k'] < 30) & (df['k'] > df['d']), 'signal'] = 'buy'
    df.loc[(df['k'] > 70) & (df['k'] < df['d']), 'signal'] = 'sell'

    return df
'''
    }
]


def init_builtin_indicators(user_id=1, db_path='data/quantdinger.db'):
    """
    初始化内置指标到数据库

    Args:
        user_id: 用户 ID，默认为 1
        db_path: 数据库路径
    """
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # 检查表是否存在
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='qd_indicator_codes'
        """)

        if not cur.fetchone():
            # 创建表
            cur.execute("""
                CREATE TABLE qd_indicator_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    is_buy INTEGER DEFAULT 0,
                    end_time INTEGER DEFAULT 1,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL,
                    description TEXT,
                    publish_to_community INTEGER DEFAULT 0,
                    pricing_type TEXT DEFAULT 'free',
                    price REAL DEFAULT 0,
                    is_encrypted INTEGER DEFAULT 0,
                    preview_image TEXT,
                    createtime DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f'[OK] 创建 qd_indicator_codes 表')

        # 插入内置指标
        inserted_count = 0
        skipped_count = 0

        for indicator in BUILTIN_INDICATORS:
            # 检查是否已存在
            cur.execute("""
                SELECT id FROM qd_indicator_codes
                WHERE name = ? AND user_id = ?
            """, (indicator['name'], user_id))

            if cur.fetchone():
                print(f'[SKIP] 指标已存在: {indicator["name"]}')
                skipped_count += 1
                continue

            # 插入新指标
            cur.execute("""
                INSERT INTO qd_indicator_codes
                  (user_id, is_buy, end_time, name, code, description,
                   publish_to_community, pricing_type, price, is_encrypted,
                   preview_image, createtime, updatetime, created_at, updated_at)
                VALUES (?, 0, 1, ?, ?, ?, 0, 'free', 0, 0, '', ?, ?, ?, ?)
            """, (
                user_id,
                indicator['name'],
                indicator['code'],
                indicator['description'],
                now, now, now, now
            ))

            inserted_count += 1
            print(f'[OK] 添加指标: {indicator["name"]}')

        conn.commit()

        print(f'\n=== 初始化完成 ===')
        print(f'新增: {inserted_count} 个')
        print(f'跳过: {skipped_count} 个')
        print(f'总计: {len(BUILTIN_INDICATORS)} 个内置指标')

        # 显示所有指标
        cur.execute("""
            SELECT id, name, description
            FROM qd_indicator_codes
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,))

        indicators = cur.fetchall()
        print(f'\n数据库中的指标列表:')
        for ind in indicators:
            print(f'  [{ind[0]}] {ind[1]}')

    except Exception as e:
        conn.rollback()
        print(f'[ERROR] 初始化失败: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    print('=== 初始化内置技术指标 ===\n')

    # 从环境变量或命令行获取数据库路径
    db_path = os.getenv('SQLITE_DATABASE_FILE', 'data/quantdinger.db')

    print(f'数据库路径: {db_path}')
    print(f'用户 ID: 1 (默认管理员)')
    print()

    init_builtin_indicators(user_id=1, db_path=db_path)

    print('\n现在可以在交易助手页面选择指标了！')
