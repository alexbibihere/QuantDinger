"""
涨幅榜币种出现次数统计服务
记录哪些币种经常出现在涨幅榜中
"""
import json
import time
from typing import Dict, List
from datetime import datetime, timedelta
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GainerAppearanceTracker:
    """涨幅榜币种出现次数跟踪器"""

    def __init__(self, redis_client=None):
        """
        初始化跟踪器

        Args:
            redis_client: Redis客户端
        """
        self.redis_client = redis_client
        self.key_prefix = "gainer_appearance"
        self.daily_key = f"{self.key_prefix}:daily"
        self.stats_key = f"{self.key_prefix}:stats"

    def record_appearance(self, symbol: str, date: str = None, price: float = None,
                         change_percentage: float = None, volume: float = None, rank: int = None):
        """
        记录币种在涨幅榜中的出现（包含完整涨幅信息）

        Args:
            symbol: 币种符号
            date: 日期字符串 (YYYY-MM-DD),默认为今天
            price: 价格
            change_percentage: 涨跌幅
            volume: 成交量
            rank: 当天排名
        """
        if not self.redis_client:
            logger.warning("Redis客户端未初始化,无法记录涨幅榜出现次数")
            return

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # 数据结构改为: 以币种为key，value为包含所有历史记录的列表
            symbol_key = f"{self.key_prefix}:symbol:{symbol}"

            # 获取该币种的历史记录
            history_data = self.redis_client.get(symbol_key)
            if history_data:
                history = json.loads(history_data)
            else:
                history = {'appearances': []}

            # 检查当天是否已记录
            existing_record = next((r for r in history['appearances'] if r['date'] == date), None)

            # 构造当天记录
            daily_record = {
                'date': date,
                'price': price,
                'change_percentage': change_percentage,
                'volume': volume,
                'rank': rank,
                'timestamp': datetime.now().isoformat()
            }

            if existing_record:
                # 更新已存在的记录
                existing_record.update(daily_record)
            else:
                # 添加新记录
                history['appearances'].append(daily_record)

                # 更新总出现次数
                self.redis_client.hincrby(self.stats_key, symbol, 1)

            # 保持记录按日期降序排列
            history['appearances'].sort(key=lambda x: x['date'], reverse=True)

            # 只保留最近30天的记录
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            history['appearances'] = [r for r in history['appearances'] if r['date'] >= cutoff_date]

            # 保存到Redis（30天过期）
            self.redis_client.setex(symbol_key, 30 * 24 * 3600, json.dumps(history))

            # 同时记录到每日索引（用于快速查询某天有哪些币种）
            daily_index_key = f"{self.daily_key}:{date}"
            self.redis_client.sadd(daily_index_key, symbol)
            self.redis_client.expire(daily_index_key, 30 * 24 * 3600)

            logger.debug(f"记录币种 {symbol} 在 {date} 的涨幅信息")

        except Exception as e:
            logger.error(f"记录涨幅信息失败: {e}")

    def get_top_frequent_symbols(self, limit: int = 20, days: int = 7) -> List[Dict]:
        """
        获取最常出现在涨幅榜的币种

        Args:
            limit: 返回数量
            days: 统计最近多少天

        Returns:
            币种统计列表,按出现次数降序排列
            [
                {"symbol": "BTCUSDT", "count": 15, "percentage": 75.0},
                {"symbol": "ETHUSDT", "count": 12, "percentage": 60.0},
                ...
            ]
        """
        if not self.redis_client:
            logger.warning("Redis客户端未初始化")
            return []

        try:
            # 获取总统计
            all_stats = self.redis_client.hgetall(self.stats_key)

            if not all_stats:
                return []

            # 转换并排序
            symbol_counts = []
            for symbol, count in all_stats.items():
                symbol_counts.append({
                    'symbol': symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol,
                    'count': int(count)
                })

            # 按出现次数降序排序
            symbol_counts.sort(key=lambda x: x['count'], reverse=True)

            # 计算百分比(基于最近days天)
            total_days = min(days, 30)  # 最多30天
            result = []
            for item in symbol_counts[:limit]:
                item['percentage'] = round(item['count'] / total_days * 100, 1)
                result.append(item)

            return result

        except Exception as e:
            logger.error(f"获取涨幅榜统计失败: {e}")
            return []

    def get_symbol_appearance_days(self, symbol: str, days: int = 30) -> List[str]:
        """
        获取指定币种在哪些日期出现在涨幅榜

        Args:
            symbol: 币种符号
            days: 查询最近多少天

        Returns:
            日期列表 ["2024-01-10", "2024-01-09", ...]
        """
        if not self.redis_client:
            return []

        try:
            appearance_days = []

            # 查询最近N天的数据
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_key = f"{self.daily_key}:{date}"

                if self.redis_client.sismember(daily_key, symbol):
                    appearance_days.append(date)

            return appearance_days

        except Exception as e:
            logger.error(f"获取币种 {symbol} 出现日期失败: {e}")
            return []

    def get_today_appearances(self) -> List[str]:
        """
        获取今天出现在涨幅榜的币种列表

        Returns:
            币种符号列表
        """
        if not self.redis_client:
            return []

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"{self.daily_key}:{today}"

            members = self.redis_client.smembers(daily_key)
            return [m.decode('utf-8') if isinstance(m, bytes) else m for m in members]

        except Exception as e:
            logger.error(f"获取今日涨幅榜失败: {e}")
            return []

    def get_symbol_history(self, symbol: str, days: int = 30) -> Dict:
        """
        获取单个币种的完整涨幅历史记录

        Args:
            symbol: 币种符号
            days: 查询最近多少天

        Returns:
            包含该币种所有历史记录的字典
            {
                'symbol': 'BTCUSDT',
                'total_appearances': 15,
                'appearances': [
                    {
                        'date': '2026-01-13',
                        'price': 42500.50,
                        'change_percentage': 5.2,
                        'volume': 1000000,
                        'rank': 1
                    },
                    ...
                ]
            }
        """
        if not self.redis_client:
            return {'symbol': symbol, 'total_appearances': 0, 'appearances': []}

        try:
            symbol_key = f"{self.key_prefix}:symbol:{symbol}"
            history_data = self.redis_client.get(symbol_key)

            if not history_data:
                return {'symbol': symbol, 'total_appearances': 0, 'appearances': []}

            history = json.loads(history_data)
            appearances = history.get('appearances', [])

            # 过滤指定天数
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            filtered_appearances = [a for a in appearances if a['date'] >= cutoff_date]

            # 获取总出现次数
            total_count_bytes = self.redis_client.hget(self.stats_key, symbol)
            total_count = int(total_count_bytes) if total_count_bytes else len(appearances)

            return {
                'symbol': symbol,
                'total_appearances': total_count,
                'appearances': filtered_appearances
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
        if not self.redis_client:
            return []

        try:
            # 从统计中获取所有币种
            all_stats = self.redis_client.hgetall(self.stats_key)

            if not all_stats:
                return []

            result = []
            for symbol in all_stats.keys():
                symbol_str = symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol
                symbol_history = self.get_symbol_history(symbol_str, days)

                # 过滤掉出现次数过少的
                if symbol_history['total_appearances'] >= min_appearances:
                    result.append(symbol_history)

            # 按出现次数降序排序
            result.sort(key=lambda x: x['total_appearances'], reverse=True)

            return result

        except Exception as e:
            logger.error(f"获取所有币种历史失败: {e}")
            return []

    def clear_old_data(self, keep_days: int = 30):
        """
        清理过期数据

        Args:
            keep_days: 保留最近多少天的数据
        """
        if not self.redis_client:
            return

        try:
            # 这个方法会在Redis自动过期时自然清理
            # 主要是清理统计中已经很久没有出现的币种
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")

            all_stats = self.redis_client.hgetall(self.stats_key)

            for symbol, count in all_stats.items():
                # 检查最近是否出现过
                recent_days = self.get_symbol_appearance_days(
                    symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol,
                    days=keep_days
                )

                if not recent_days:
                    # 很久没出现,从统计中移除
                    self.redis_client.hdel(self.stats_key, symbol)
                    logger.debug(f"清理币种 {symbol} 的统计数据")

        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")


# 全局实例
_tracker = None


def get_gainer_tracker():
    """获取全局跟踪器实例"""
    global _tracker
    if _tracker is None:
        try:
            from app import get_redis_client
            redis_client = get_redis_client()
            _tracker = GainerAppearanceTracker(redis_client)
        except Exception as e:
            logger.warning(f"无法获取Redis客户端,涨幅榜统计将不可用: {e}")
            _tracker = GainerAppearanceTracker(None)
    return _tracker


def record_gainer_appearance(gainer_data: List[Dict], date: str = None):
    """
    批量记录币种在涨幅榜中的出现（包含完整信息）

    Args:
        gainer_data: 币种数据列表，每个元素包含:
            {
                'symbol': 'BTCUSDT',
                'price': 42500.50,
                'change_percentage': 5.2,
                'volume': 1000000,
                'rank': 1
            }
        date: 日期字符串
    """
    tracker = get_gainer_tracker()
    if not tracker:
        return

    for data in gainer_data:
        symbol = data.get('symbol')
        if not symbol:
            continue

        tracker.record_appearance(
            symbol=symbol,
            date=date,
            price=data.get('price'),
            change_percentage=data.get('change_percentage'),
            volume=data.get('volume'),
            rank=data.get('rank')
        )

    logger.info(f"已记录 {len(gainer_data)} 个币种在涨幅榜中的出现")
