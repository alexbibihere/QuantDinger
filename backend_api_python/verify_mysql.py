"""
验证 MySQL 数据库连接和表结构
"""
import pymysql
import os
import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def verify_mysql():
    """验证 MySQL 数据库"""
    print("="*80)
    print("验证 MySQL 数据库")
    print("="*80)

    # 从环境变量读取配置
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', 3306))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'quantdinger')

    try:
        # 连接到数据库
        print(f"\n正在连接到 MySQL: {mysql_user}@{mysql_host}:{mysql_port}")
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4'
        )
        cursor = connection.cursor()

        print("✅ 连接成功")

        # 查看数据库版本
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"MySQL 版本: {version}")

        # 查看所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\n数据库 '{mysql_database}' 中的表 ({len(tables)} 个):")
        print("-"*80)

        for table in tables:
            table_name = table[0]

            # 获取表的行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]

            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()

            print(f"\n📋 {table_name}")
            print(f"   行数: {count}")
            print(f"   字段数: {len(columns)}")

            # 显示前3个字段
            print("   字段 (前5个):")
            for col in columns[:5]:
                print(f"     - {col[0]}: {col[1]}")
            if len(columns) > 5:
                print(f"     ... 还有 {len(columns) - 5} 个字段")

        # 测试插入一条用户数据
        print("\n" + "="*80)
        print("测试插入用户数据...")

        try:
            cursor.execute("""
                INSERT IGNORE INTO qd_users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, ('admin', 'test_hash', 'admin@quantdinger.com'))
            connection.commit()

            cursor.execute("SELECT COUNT(*) FROM qd_users")
            user_count = cursor.fetchone()[0]

            print(f"✅ 用户表测试成功，当前用户数: {user_count}")

        except Exception as e:
            print(f"⚠️  用户表测试失败: {str(e)}")

        print("\n" + "="*80)
        print("✅ 数据库验证完成")
        print("="*80)

        cursor.close()
        connection.close()

        return True

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    verify_mysql()
