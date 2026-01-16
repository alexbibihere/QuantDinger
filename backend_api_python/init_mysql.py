"""
初始化 MySQL 数据库脚本

创建数据库和所有需要的表结构
"""
import pymysql
import os
import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_database():
    """创建 MySQL 数据库"""
    print("="*80)
    print("开始创建 MySQL 数据库")
    print("="*80)

    # 从环境变量读取配置
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', 3306))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'quantdinger')
    mysql_charset = os.getenv('MYSQL_CHARSET', 'utf8mb4')

    print(f"\n配置信息:")
    print(f"  主机: {mysql_host}:{mysql_port}")
    print(f"  用户: {mysql_user}")
    print(f"  数据库: {mysql_database}")
    print(f"  字符集: {mysql_charset}")

    try:
        # 连接到 MySQL 服务器
        print(f"\n正在连接到 MySQL 服务器...")
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            charset=mysql_charset
        )
        cursor = connection.cursor()

        # 创建数据库
        print(f"正在创建数据库: {mysql_database}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_database}` CHARACTER SET {mysql_charset} COLLATE {mysql_charset}_unicode_ci")
        print(f"✅ 数据库 '{mysql_database}' 创建成功")

        # 切换到该数据库
        cursor.execute(f"USE `{mysql_database}`")

        # 创建用户表
        print("\n正在创建表: qd_users")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_users` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `username` VARCHAR(50) NOT NULL UNIQUE,
                `password_hash` VARCHAR(255) NOT NULL,
                `email` VARCHAR(100),
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_users 表创建成功")

        # 创建指标表
        print("\n正在创建表: qd_indicators")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_indicators` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `name` VARCHAR(100) NOT NULL,
                `description` TEXT,
                `code` TEXT NOT NULL,
                `language` VARCHAR(20) DEFAULT 'python',
                `is_builtin` BOOLEAN DEFAULT FALSE,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_indicators 表创建成功")

        # 创建策略表
        print("\n正在创建表: qd_strategies_trading")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_strategies_trading` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `name` VARCHAR(100) NOT NULL,
                `description` TEXT,
                `indicator_id` INTEGER,
                `symbol` VARCHAR(50) NOT NULL,
                `exchange` VARCHAR(50) DEFAULT 'binance',
                `status` VARCHAR(20) DEFAULT 'stopped',
                `mode` VARCHAR(20) DEFAULT 'signal',
                `config` JSON,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`indicator_id`) REFERENCES `qd_indicators`(`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_strategies_trading 表创建成功")

        # 创建回测结果表
        print("\n正在创建表: qd_backtest_results")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_backtest_results` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `strategy_id` INTEGER,
                `symbol` VARCHAR(50) NOT NULL,
                `start_date` DATE,
                `end_date` DATE,
                `initial_capital` DECIMAL(18, 8),
                `final_capital` DECIMAL(18, 8),
                `total_return` DECIMAL(10, 4),
                `max_drawdown` DECIMAL(10, 4),
                `win_rate` DECIMAL(5, 4),
                `total_trades` INTEGER,
                `profit_trades` INTEGER,
                `loss_trades` INTEGER,
                `sharpe_ratio` DECIMAL(10, 4),
                `results` JSON,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`strategy_id`) REFERENCES `qd_strategies_trading`(`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_backtest_results 表创建成功")

        # 创建交易所凭证表
        print("\n正在创建表: qd_exchange_credentials")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_exchange_credentials` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `exchange` VARCHAR(50) NOT NULL,
                `api_key` TEXT NOT NULL,
                `api_secret` TEXT NOT NULL,
                `passphrase` TEXT,
                `is_testnet` BOOLEAN DEFAULT FALSE,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE,
                UNIQUE KEY `unique_exchange` (`user_id`, `exchange`)
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_exchange_credentials 表创建成功")

        # 创建待执行订单表
        print("\n正在创建表: pending_orders")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `pending_orders` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `strategy_id` INTEGER NOT NULL,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `symbol` VARCHAR(50) NOT NULL,
                `exchange` VARCHAR(50) DEFAULT 'binance',
                `order_type` VARCHAR(20) NOT NULL,
                `side` VARCHAR(10) NOT NULL,
                `amount` DECIMAL(18, 8) NOT NULL,
                `price` DECIMAL(18, 8),
                `status` VARCHAR(20) DEFAULT 'pending',
                `error_message` TEXT,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ pending_orders 表创建成功")

        # 创建自选列表表
        print("\n正在创建表: qd_watchlist")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_watchlist` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `market` VARCHAR(50) NOT NULL,
                `symbol` VARCHAR(50) NOT NULL,
                `name` VARCHAR(100),
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE,
                UNIQUE KEY `unique_symbol` (`user_id`, `market`, `symbol`)
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_watchlist 表创建成功")

        # 创建HAMA信号表
        print("\n正在创建表: qd_hama_signals")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_hama_signals` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `symbol` VARCHAR(50) NOT NULL,
                `signal_type` VARCHAR(20) NOT NULL,
                `price` DECIMAL(18, 8),
                `ma100` DECIMAL(18, 8),
                `ema20` DECIMAL(18, 8),
                `detected_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX `idx_symbol` (`symbol`),
                INDEX `idx_detected_at` (`detected_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_hama_signals 表创建成功")

        # 创建涨幅榜统计表
        print("\n正在创建表: qd_gainer_stats")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_gainer_stats` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `symbol` VARCHAR(50) NOT NULL,
                `date` DATE NOT NULL,
                `rank` INTEGER,
                `change_percentage` DECIMAL(10, 4),
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY `unique_symbol_date` (`symbol`, `date`),
                INDEX `idx_date` (`date`),
                INDEX `idx_symbol` (`symbol`)
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_gainer_stats 表创建成功")

        # 创建交易记录表
        print("\n正在创建表: qd_trade_records")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `qd_trade_records` (
                `id` INTEGER PRIMARY KEY AUTO_INCREMENT,
                `user_id` INTEGER NOT NULL DEFAULT 1,
                `strategy_id` INTEGER,
                `symbol` VARCHAR(50) NOT NULL,
                `exchange` VARCHAR(50) DEFAULT 'binance',
                `side` VARCHAR(10) NOT NULL,
                `order_type` VARCHAR(20) NOT NULL,
                `amount` DECIMAL(18, 8) NOT NULL,
                `price` DECIMAL(18, 8),
                `fee` DECIMAL(18, 8) DEFAULT 0,
                `order_id` VARCHAR(100),
                `status` VARCHAR(20) DEFAULT 'filled',
                `executed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `qd_users`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`strategy_id`) REFERENCES `qd_strategies_trading`(`id`) ON DELETE SET NULL,
                INDEX `idx_symbol` (`symbol`),
                INDEX `idx_executed_at` (`executed_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
        """.format(charset=mysql_charset))
        print("✅ qd_trade_records 表创建成功")

        # 提交所有更改
        connection.commit()

        print("\n" + "="*80)
        print("✅ 数据库初始化完成！")
        print("="*80)

        # 显示表信息
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n已创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")

        print("\n下一步:")
        print("1. 确保 .env 文件中设置了:")
        print("   DB_TYPE=mysql")
        print("   MYSQL_HOST=localhost")
        print("   MYSQL_PORT=3306")
        print("   MYSQL_USER=quantdinger")
        print("   MYSQL_PASSWORD=quantdinger123")
        print("   MYSQL_DATABASE=quantdinger")
        print("2. 重启后端服务")
        print("3. 系统将自动使用 MySQL 数据库")

        cursor.close()
        connection.close()

        return True

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)

    create_database()
