# MySQL 数据库配置指南

## 概述

QuantDinger 支持两种数据库:
- **SQLite** (默认): 本地文件数据库，无需额外配置
- **MySQL**: 生产级关系数据库，支持并发访问和网络部署

## 配置步骤

### 1. 安装 MySQL

#### Windows:
```bash
# 下载并安装 MySQL 8.0+
# https://dev.mysql.com/downloads/mysql/

# 或使用 Chocolatey
choco install mysql
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

#### macOS:
```bash
brew install mysql
```

### 2. 创建数据库和用户

#### 方法1: 使用初始化脚本 (推荐)

```bash
cd backend_api_python
python init_mysql.py
```

脚本会自动:
- 创建数据库 `quantdinger`
- 创建所有需要的表结构
- 设置正确的字符集和索引

#### 方法2: 手动创建

```sql
-- 连接到 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE quantdinger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'quantdinger'@'localhost' IDENTIFIED BY 'quantdinger123';

-- 授权
GRANT ALL PRIVILEGES ON quantdinger.* TO 'quantdinger'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量

编辑 `backend_api_python/.env` 文件:

```bash
# 数据库类型: sqlite 或 mysql
DB_TYPE=mysql

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=quantdinger
MYSQL_PASSWORD=quantdinger123
MYSQL_DATABASE=quantdinger
MYSQL_CHARSET=utf8mb4
```

### 4. 安装 Python 依赖

```bash
cd backend_api_python
pip install pymysql
```

### 5. 重启服务

```bash
# Docker 部署
docker-compose restart backend

# 本地开发
python run.py
```

## 数据库表结构

系统会自动创建以下表:

| 表名 | 说明 |
|------|------|
| `qd_users` | 用户表 |
| `qd_indicators` | 技术指标代码 |
| `qd_strategies_trading` | 交易策略配置 |
| `qd_backtest_results` | 回测结果 |
| `qd_exchange_credentials` | 交易所 API 密钥 |
| `pending_orders` | 待执行订单队列 |
| `qd_watchlist` | 自选列表 |
| `qd_hama_signals` | HAMA 信号记录 |
| `qd_gainer_stats` | 涨幅榜统计 |
| `qd_trade_records` | 交易记录 |

## 数据备份

### 备份 MySQL 数据库

```bash
# 备份整个数据库
mysqldump -u quantdinger -p quantdinger > quantdinger_backup.sql

# 只备份表结构
mysqldump -u quantdinger -p --no-data quantdinger > quantdinger_schema.sql

# 只备份数据
mysqldump -u quantdinger -p --no-create-info quantdinger > quantdinger_data.sql
```

### 恢复 MySQL 数据库

```bash
# 恢复数据库
mysql -u quantdinger -p quantdinger < quantdinger_backup.sql
```

## 性能优化

### MySQL 配置优化 (my.cnf / my.ini)

```ini
[mysqld]
# 连接数
max_connections = 200

# 缓冲池大小 (物理内存的 70-80%)
innodb_buffer_pool_size = 1G

# 日志文件大小
innodb_log_file_size = 256M

# 刷新策略
innodb_flush_log_at_trx_commit = 2

# 查询缓存 (MySQL 5.7 及以下)
query_cache_size = 128M
query_cache_type = 1
```

### 索引优化

系统已自动创建关键索引:

```sql
-- 查看索引
SHOW INDEX FROM qd_hama_signals;
SHOW INDEX FROM qd_gainer_stats;
SHOW INDEX FROM qd_trade_records;

-- 添加自定义索引 (如需要)
CREATE INDEX idx_custom ON qd_trade_records(symbol, executed_at);
```

## 故障排查

### 连接失败

```bash
# 检查 MySQL 是否运行
# Windows
net start MySQL

# Linux
sudo systemctl status mysql

# 检查端口
netstat -an | findstr 3306  # Windows
netstat -tlnp | grep 3306   # Linux
```

### 权限错误

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON quantdinger.* TO 'quantdinger'@'localhost';
FLUSH PRIVILEGES;
```

### 字符集问题

```sql
-- 检查数据库字符集
SHOW VARIABLES LIKE 'character_set%';

-- 修改表字符集
ALTER TABLE qd_users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 从 SQLite 迁移到 MySQL

如果你之前使用 SQLite，可以迁移数据:

```bash
# 使用 SQLite 导出数据
sqlite3 data/quantdinger.db .dump > sqlite_dump.sql

# 手动调整 SQL 语法后导入 MySQL
# - 将 INTEGER PRIMARY KEY -> INTEGER PRIMARY KEY AUTO_INCREMENT
# - 将 AUTOINCREMENT -> AUTO_INCREMENT
# - 调整日期时间格式

mysql -u quantdinger -p quantdinger < sqlite_dump.sql
```

## Docker 部署 MySQL

如果使用 Docker，可以添加 MySQL 服务:

```yaml
# docker-compose.yml
services:
  mysql:
    image: mysql:8.0
    container_name: quantdinger-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: quantdinger
      MYSQL_USER: quantdinger
      MYSQL_PASSWORD: quantdinger123
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

volumes:
  mysql_data:
```

启动:

```bash
docker-compose up -d mysql
python backend_api_python/init_mysql.py
```

## 监控和维护

### 查看数据库大小

```sql
SELECT
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'quantdinger'
GROUP BY table_schema;
```

### 查看表大小

```sql
SELECT
    table_name AS 'Table',
    table_rows AS 'Rows',
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'quantdinger'
ORDER BY (data_length + index_length) DESC;
```

### 优化表

```sql
OPTIMIZE TABLE qd_trade_records;
OPTIMIZE TABLE qd_hama_signals;
```

## 安全建议

1. **使用强密码**: 修改默认密码
2. **限制访问**: 只允许本地连接或使用 VPN
3. **定期备份**: 设置自动备份任务
4. **更新软件**: 保持 MySQL 和驱动程序最新
5. **监控日志**: 定期检查 MySQL 错误日志

## 常见问题

### Q: 如何切换回 SQLite?

A: 修改 `.env` 文件:
```bash
DB_TYPE=sqlite
```

### Q: 可以同时使用 SQLite 和 MySQL 吗?

A: 不可以，系统根据 `DB_TYPE` 配置选择其中一种。

### Q: 如何查看当前使用的数据库?

A: 查看后端日志:
```
Database type: mysql
```

或访问健康检查 API:
```
GET /api/health
```

## 技术支持

如有问题，请查看:
- 项目文档: [README.md](../README.md)
- 问题反馈: [GitHub Issues](https://github.com/alexbibihere/QuantDinger/issues)
