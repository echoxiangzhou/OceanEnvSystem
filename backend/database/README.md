# 海洋环境系统 MySQL 数据库部署指南

## 文件说明

- `mysql_import.sql` - 完整的数据库导入脚本（包含用户、视图、存储过程等）
- `quick_setup.sql` - 快速部署脚本（仅包含基本表结构）
- `docker-compose.yml` - Docker Compose 配置文件
- `my.cnf` - MySQL 配置文件
- `README.md` - 本说明文档

## 部署方式

### 方式一：使用 Docker Compose（推荐）

1. **启动 MySQL 服务**
   ```bash
   cd backend/database
   docker-compose up -d
   ```

2. **访问 phpMyAdmin**
   - 地址：http://localhost:8080
   - 用户名：root
   - 密码：root_password_2024

3. **应用连接配置**
   ```python
   # 在 backend/app/core/config.py 中设置
   MYSQL_SERVER = "localhost"
   MYSQL_PORT = 3306
   MYSQL_USER = "oceanenv_user"
   MYSQL_PASSWORD = "oceanenv_password_2024"
   MYSQL_DB = "oceanenv_metadata"
   ```

### 方式二：手动安装 MySQL

1. **安装 MySQL 8.0**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install mysql-server-8.0
   
   # CentOS/RHEL
   sudo yum install mysql-server
   
   # macOS
   brew install mysql
   ```

2. **执行导入脚本**
   ```bash
   # 使用完整脚本
   mysql -u root -p < mysql_import.sql
   
   # 或使用快速脚本
   mysql -u root -p < quick_setup.sql
   ```

## 数据库结构

### 主表：netcdf_metadata

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | int(11) | 主键ID |
| file_path | varchar(500) | 文件路径（唯一） |
| file_name | varchar(255) | 文件名 |
| file_size | bigint(20) | 文件大小（字节） |
| file_hash | varchar(64) | 文件MD5哈希值 |
| cf_version | varchar(20) | CF规范版本 |
| is_cf_compliant | tinyint(1) | 是否符合CF规范 |
| title | varchar(500) | 数据集标题 |
| summary | text | 数据集摘要 |
| institution | varchar(255) | 机构 |
| source | varchar(255) | 数据来源 |
| variables | json | 变量信息 |
| dimensions | json | 维度信息 |
| processing_status | varchar(50) | 处理状态 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### 处理状态说明

- `raw` - 原始数据
- `processing` - 处理中
- `standard` - 标准数据（CF-1.8规范）

## 性能优化

### 索引策略

- `file_path` - 唯一索引（快速文件查找）
- `file_name` - 普通索引（文件名搜索）
- `institution` - 普通索引（机构过滤）
- `processing_status` - 普通索引（状态过滤）
- `time_coverage` - 复合索引（时间范围查询）
- `geospatial` - 复合索引（空间范围查询）

### 查询优化建议

1. **使用分页查询**
   ```sql
   SELECT * FROM netcdf_metadata 
   ORDER BY updated_at DESC 
   LIMIT 20 OFFSET 0;
   ```

2. **使用索引字段过滤**
   ```sql
   SELECT * FROM netcdf_metadata 
   WHERE processing_status = 'standard' 
   AND institution LIKE '%海洋%';
   ```

3. **JSON字段查询**
   ```sql
   SELECT * FROM netcdf_metadata 
   WHERE JSON_EXTRACT(variables, '$.temperature') IS NOT NULL;
   ```

## 维护操作

### 备份数据库

```bash
# 完整备份
mysqldump -u oceanenv_user -p oceanenv_metadata > backup_$(date +%Y%m%d).sql

# 仅备份结构
mysqldump -u oceanenv_user -p --no-data oceanenv_metadata > structure.sql

# 仅备份数据
mysqldump -u oceanenv_user -p --no-create-info oceanenv_metadata > data.sql
```

### 恢复数据库

```bash
# 恢复完整备份
mysql -u oceanenv_user -p oceanenv_metadata < backup_20241220.sql

# 恢复到新数据库
mysql -u oceanenv_user -p -e "CREATE DATABASE oceanenv_metadata_restore;"
mysql -u oceanenv_user -p oceanenv_metadata_restore < backup_20241220.sql
```

### 清理操作

```sql
-- 删除处理中状态超过7天的记录
DELETE FROM netcdf_metadata 
WHERE processing_status = 'processing' 
AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 清理孤立记录（文件不存在）
DELETE FROM netcdf_metadata 
WHERE file_path NOT IN (
    SELECT file_path FROM actual_files_table
);
```

### 监控查询

```sql
-- 查看表状态
SHOW TABLE STATUS LIKE 'netcdf_metadata';

-- 查看索引使用情况
SHOW INDEX FROM netcdf_metadata;

-- 分析表性能
ANALYZE TABLE netcdf_metadata;

-- 查看慢查询
SELECT * FROM mysql.slow_log 
WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 DAY);
```

## 常见问题

### 1. 连接失败

**问题**：Cannot connect to MySQL server
**解决**：
- 检查MySQL服务是否启动
- 验证用户名密码
- 确认端口3306是否开放

### 2. 字符编码问题

**问题**：中文显示乱码
**解决**：
```sql
ALTER DATABASE oceanenv_metadata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE netcdf_metadata CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. JSON字段查询慢

**问题**：JSON字段查询性能差
**解决**：
```sql
-- 创建生成列索引
ALTER TABLE netcdf_metadata 
ADD COLUMN variable_names JSON GENERATED ALWAYS AS (JSON_KEYS(variables)) STORED;
CREATE INDEX idx_variable_names ON netcdf_metadata(variable_names);
```

### 4. 磁盘空间不足

**问题**：InnoDB表空间满
**解决**：
```sql
-- 优化表
OPTIMIZE TABLE netcdf_metadata;

-- 清理二进制日志
PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);
```

## 开发环境设置

### 环境变量配置

```bash
# .env文件
MYSQL_SERVER=localhost
MYSQL_PORT=3306
MYSQL_USER=oceanenv_user
MYSQL_PASSWORD=oceanenv_password_2024
MYSQL_DB=oceanenv_metadata
MYSQL_CHARSET=utf8mb4
```

### 测试数据生成

```python
# 生成测试数据的Python脚本
import mysql.connector
import json
from datetime import datetime

conn = mysql.connector.connect(
    host='localhost',
    user='oceanenv_user',
    password='oceanenv_password_2024',
    database='oceanenv_metadata'
)

cursor = conn.cursor()

# 插入测试数据
test_data = {
    'file_path': '/test/sample.nc',
    'file_name': 'sample.nc',
    'file_size': 1024000,
    'processing_status': 'standard',
    'variables': json.dumps({
        'temperature': {'dtype': 'float32', 'shape': [100, 200]},
        'salinity': {'dtype': 'float32', 'shape': [100, 200]}
    })
}

cursor.execute("""
    INSERT INTO netcdf_metadata (file_path, file_name, file_size, processing_status, variables)
    VALUES (%(file_path)s, %(file_name)s, %(file_size)s, %(processing_status)s, %(variables)s)
""", test_data)

conn.commit()
conn.close()
```

## 生产环境建议

1. **安全设置**
   - 修改默认密码
   - 限制远程访问
   - 启用SSL连接
   - 定期更新MySQL版本

2. **性能优化**
   - 根据服务器内存调整缓冲池大小
   - 监控慢查询日志
   - 定期分析表统计信息
   - 使用读写分离（如需要）

3. **备份策略**
   - 每日自动备份
   - 增量备份和全量备份结合
   - 异地备份存储
   - 定期测试备份恢复

4. **监控告警**
   - 磁盘空间监控
   - 连接数监控
   - 慢查询告警
   - 复制延迟监控（如使用主从复制） 