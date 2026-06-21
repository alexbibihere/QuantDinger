"""
涨幅榜历史服务（使用 SQLite 存储）
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.utils.db import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FuturesGainersHistory:
    """涨幅榜历史服务"""

    def record_appearance(
        self,
        symbol: str,
        exchange: str,
        price: float = None,
        change_percentage: float = None,
        volume: float = None,
        rank: int = None,
        high_24h: float = None,
        low_24h: float = None,
        open_24h: float = None,
        date: str = None
    ):
        """
        记录币种在涨幅榜中的出现

        Args:
            symbol: 币种符号
            exchange: 交易所 (binance, okx)
            price: 价格
            change_percentage: 涨跌幅
            volume: 24小时成交量
            rank: 当天排名
            high_24h: 24小时最高价
            low_24h: 24小时最低价
            open_24h: 24小时开盘价
            date: 日期字符串 (YYYY-MM-DD), 默认为今天
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # 使用 INSERT OR REPLACE 避免重复记录
                cursor.execute("""
                    INSERT OR REPLACE INTO qd_futures_gainers_history
                    (date, symbol, exchange, rank, price, change_percentage, volume_24h, high_24h, low_24h, open_24h, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date, symbol, exchange, rank, price, change_percentage,
                    volume, high_24h, low_24h, open_24h,
                    int(datetime.now().timestamp())
                ))

                conn.commit()
                logger.debug(f"记录涨幅榜: {symbol} @ {exchange} on {date}")

        except Exception as e:
            logger.error(f"记录涨幅榜历史失败: {e}")

    def batch_record(self, gainers_data: List[Dict], exchange: str, date: str = None):
        """
        批量记录涨幅榜数据

        Args:
            gainers_data: 涨幅榜数据列表
            exchange: 交易所 (binance, okx)
            date: 日期字符串
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for item in gainers_data:
                    symbol = item.get('symbol')
                    if not symbol:
                        continue

                    cursor.execute("""
                        INSERT OR REPLACE INTO qd_futures_gainers_history
                        (date, symbol, exchange, rank, price, change_percentage, volume_24h, high_24h, low_24h, open_24h, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date, symbol, exchange,
                        item.get('rank'),
                        item.get('price'),
                        item.get('change_percentage'),
                        item.get('volume'),
                        item.get('high_24h'),
                        item.get('low_24h'),
                        item.get('open_24h'),
                        int(datetime.now().timestamp())
                    ))

                conn.commit()
                logger.info(f"已批量记录 {len(gainers_data)} 个涨幅榜币种到历史 ({exchange} on {date})")

        except Exception as e:
            logger.error(f"批量记录涨幅榜历史失败: {e}")

    def get_today_appearances(self) -> List[str]:
        """获取今天出现在涨幅榜的币种列表"""
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol
                    FROM qd_futures_gainers_history
                    WHERE date = ?
                """, (today,))

                rows = cursor.fetchall()
                return [row['symbol'] for row in rows]

        except Exception as e:
            logger.error(f"获取今日涨幅榜失败: {e}")
            return []

    def get_symbol_history(self, symbol: str, days: int = 30) -> Dict:
        """
        获取单个币种的涨幅历史记录

        Args:
            symbol: 币种符号
            days: 查询最近多少天

        Returns:
            包含该币种所有历史记录的字典
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        date, exchange, rank, price, change_percentage,
                        volume_24h, high_24h, low_24h, open_24h
                    FROM qd_futures_gainers_history
                    WHERE symbol = ? AND date >= ?
                    ORDER BY date DESC
                """, (symbol, cutoff_date))

                rows = cursor.fetchall()

                appearances = []
                for row in rows:
                    appearances.append({
                        'date': row['date'],
                        'exchange': row['exchange'],
                        'rank': row['rank'],
                        'price': row['price'],
                        'change_percentage': row['change_percentage'],
                        'volume': row['volume_24h'],
                        'high_24h': row['high_24h'],
                        'low_24h': row['low_24h'],
                        'open_24h': row['open_24h']
                    })

                # 获取总出现次数
                cursor.execute("""
                    SELECT COUNT(DISTINCT date) as total_count
                    FROM qd_futures_gainers_history
                    WHERE symbol = ?
                """, (symbol,))
                count_row = cursor.fetchone()
                total_count = count_row['total_count'] if count_row else 0

                return {
                    'symbol': symbol,
                    'total_appearances': total_count,
                    'appearances': appearances
                }

        except Exception as e:
            logger.error(f"获取币种 {symbol} 历史记录失败: {e}")
            return {'symbol': symbol, 'total_appearances': 0, 'appearances': []}

    def get_all_symbols_history(self, days: int = 7, min_appearances: int = 1) -> List[Dict]:
        """
        获取所有币种的历史记录（用于排行榜）

        Args:
            days: 查询最近多少天
            min_appearances: 最小出现次数

        Returns:
            币种历史列表
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # 获取每个币种的出现次数
                cursor.execute("""
                    SELECT
                        symbol,
                        COUNT(DISTINCT date) as total_appearances
                    FROM qd_futures_gainers_history
                    WHERE date >= ?
                    GROUP BY symbol
                    HAVING total_appearances >= ?
                    ORDER BY total_appearances DESC
                """, (cutoff_date, min_appearances))

                count_rows = cursor.fetchall()
                result = []

                for row in count_rows:
                    symbol = row['symbol']
                    symbol_history = self.get_symbol_history(symbol, days)

                    if symbol_history['total_appearances'] >= min_appearances:
                        result.append(symbol_history)

                return result

        except Exception as e:
            logger.error(f"获取所有币种历史失败: {e}")
            return []

    def get_daily_history(self, days: int = 7) -> List[Dict]:
        """
        获取每日涨幅榜历史

        Args:
            days: 查询最近多少天

        Returns:
            每日历史数据列表
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT DISTINCT date
                    FROM qd_futures_gainers_history
                    WHERE date >= ?
                    ORDER BY date DESC
                """, (cutoff_date,))

                date_rows = cursor.fetchall()
                history = []

                for date_row in date_rows:
                    date = date_row['date']

                    # 获取该日期的所有币种
                    cursor.execute("""
                        SELECT
                            symbol, exchange, rank, price, change_percentage,
                            volume_24h, high_24h, low_24h, open_24h
                        FROM qd_futures_gainers_history
                        WHERE date = ?
                        ORDER BY rank ASC
                    """, (date,))

                    symbol_rows = cursor.fetchall()
                    symbols = []
                    symbol_details = []

                    for row in symbol_rows:
                        symbols.append(row['symbol'])
                        symbol_details.append({
                            'symbol': row['symbol'],
                            'count': row['rank'],  # rank 作为 count 占位
                            'price': row['price'],
                            'changePercentage': row['change_percentage'],
                            'volume': row['volume_24h'],
                            'rank': row['rank']
                        })

                    history.append({
                        'date': date,
                        'count': len(symbols),
                        'symbols': symbols,
                        'symbolDetails': symbol_details
                    })

                return history

        except Exception as e:
            logger.error(f"获取每日历史失败: {e}")
            return []

    def get_top_frequent_symbols(self, limit: int = 20, days: int = 7) -> List[Dict]:
        """
        获取最常出现在涨幅榜的币种

        Args:
            limit: 返回数量
            days: 统计最近多少天

        Returns:
            币种统计列表
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        symbol,
                        COUNT(DISTINCT date) as count
                    FROM qd_futures_gainers_history
                    WHERE date >= ?
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT ?
                """, (cutoff_date, limit))

                rows = cursor.fetchall()
                result = []

                total_days = min(days, 30)
                for row in rows:
                    result.append({
                        'symbol': row['symbol'],
                        'count': row['count'],
                        'percentage': round(row['count'] / total_days * 100, 1)
                    })

                return result

        except Exception as e:
            logger.error(f"获取涨幅榜统计失败: {e}")
            return []

    def clear_old_data(self, keep_days: int = 30):
        """清理过期数据"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM qd_futures_gainers_history
                    WHERE date < ?
                """, (cutoff_date,))

                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"清理了 {deleted_count} 条过期涨幅榜历史记录")

        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")


# 全局实例
_history_service = None


def get_futures_gainers_history():
    """获取涨幅榜历史服务实例"""
    global _history_service
    if _history_service is None:
        _history_service = FuturesGainersHistory()
    return _history_service
