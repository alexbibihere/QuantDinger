"""
检查 Redis 中保存的涨幅榜数据
"""
import redis
import os
import sys
import io
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
env_path = Path(__file__).parent / 'backend_api_python' / '.env'
load_dotenv(env_path)

def check_gainer_data():
    """检查 Redis 中的涨幅榜数据"""
    print("="*80)
    print("检查 Redis 中的涨幅榜数据")
    print("="*80)

    # 连接 Redis
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_db = int(os.getenv('REDIS_DB', 0))

    try:
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        r.ping()
        print(f"✅ Redis 连接成功: {redis_host}:{redis_port}\n")

        # 1. 查看今天的涨幅榜
        today = datetime.now().strftime("%Y-%m-%d")
        today_key = f"gainer_appearance:daily:{today}"
        today_count = r.scard(today_key)
        today_symbols = r.smembers(today_key)

        print(f"📅 今天的涨幅榜 ({today})")
        print(f"   币种数: {today_count}")
        if today_count > 0:
            print(f"   前10个: {list(today_symbols)[:10]}")
        print()

        # 2. 查看总统计
        stats_key = "gainer_appearance:stats"
        all_stats = r.hgetall(stats_key)

        print(f"📊 总统计 (所有币种出现次数)")
        print(f"   总币种数: {len(all_stats)}")

        # 排序并显示前10
        sorted_stats = sorted(all_stats.items(), key=lambda x: int(x[1]), reverse=True)
        print(f"   前10名:")
        for i, (symbol, count) in enumerate(sorted_stats[:10], 1):
            print(f"     {i:2d}. {symbol:15} - {count}次")
        print()

        # 3. 查看历史记录
        print(f"📜 历史记录 (最近7天)")
        daily_count = 0
        symbol_count = 0

        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            key = f"gainer_appearance:daily:{date}"
            count = r.scard(key)
            if count > 0:
                print(f"   {date}: {count} 个币种")
                daily_count += 1
                symbol_count += count

        print(f"\n   总计: {daily_count} 天有记录, 共 {symbol_count} 条记录")
        print()

        # 4. 分析特定币种
        if sorted_stats:
            top_symbol = sorted_stats[0][0]
            print(f"🔍 分析币种: {top_symbol}")

            appearance_days = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                key = f"gainer_appearance:daily:{date}"
                if r.sismember(key, top_symbol):
                    appearance_days.append(date)

            print(f"   最近7天出现: {len(appearance_days)} 次")
            print(f"   出现日期: {appearance_days}")
        print()

        print("="*80)
        print("✅ 数据检查完成")
        print("="*80)

        # 数据保存说明
        print("\n📌 数据保存说明:")
        print("   - 每日涨幅榜: Redis Set, 自动过期30天")
        print("   - 总统计: Redis Hash, 永久保存")
        print("   - 格式: gainer_appearance:daily:YYYY-MM-DD")
        print("   - 记录方式: 每次调用涨幅榜API时自动记录")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_gainer_data()
