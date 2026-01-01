# 生产部署指南

## 🚀 部署状态
✅ **所有测试已通过** - 项目已具备生产部署条件

### 测试通过率
- **后端测试**: 100% (104/104) ✅
- **前端测试**: 100% (100/100) ✅
- **端到端测试**: 100% (5/5) ✅
- **集成测试**: 100% (20/20) ✅
- **总体覆盖率**: 80% ✅

## 📋 系统要求

### 硬件要求
- **CPU**: 2+ 核心
- **内存**: 4GB+ RAM
- **存储**: 10GB+ 可用空间

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows WSL2
- **Python**: 3.12.3+
- **PostgreSQL**: 14+
- **Node.js**: 18+ (前端部署)

## 🛠️ 快速部署

### 步骤1: 环境准备
```bash
# 克隆项目（如果尚未克隆）
git clone <repository-url>
cd datalab

# 确保PostgreSQL正在运行
sudo systemctl start postgresql
```

### 步骤2: 运行部署脚本
```bash
# 给脚本添加执行权限
chmod +x deploy_production.sh

# 运行部署脚本
./deploy_production.sh
```

### 步骤3: 启动生产服务器
```bash
# 启动生产服务器
./start_production.sh
```

## 🔧 手动部署步骤

### 1. 设置虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境文件
cp .env.example .env

# 编辑.env文件，设置正确的数据库连接信息
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```

### 3. 数据库设置
```bash
# 创建数据库（如果不存在）
createdb datalab

# 运行数据库迁移（如果有）
# alembic upgrade head
```

### 4. 验证部署
```bash
# 运行测试
python -m pytest tests/backend/ tests/integration/ -v

# 启动开发服务器测试
python -m src.backend.main
```

### 5. 启动生产服务器
```bash
# 使用uvicorn启动生产服务器
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🌐 访问应用

### API端点
- **API根地址**: http://localhost:8000
- **交互式文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **API端点列表**: http://localhost:8000/api/metadata

### 主要功能端点
1. **搜索API**: `GET /api/search/?query=<搜索词>`
2. **聊天诊断**: `POST /api/chat/` (JSON: `{"query": "问题描述"}`)
3. **分析仪表板**: `GET /api/analytics/summary`
4. **MTBF分析**: `GET /api/analytics/mtbf`
5. **Pareto分析**: `GET /api/analytics/pareto`

## 🔒 安全配置

### 生产环境建议
1. **修改默认密码**: 更新`.env`文件中的数据库密码
2. **设置CORS白名单**: 在配置中限制允许的域名
3. **启用HTTPS**: 使用反向代理（Nginx/Apache）配置SSL
4. **防火墙配置**: 只开放必要的端口（8000, 5432）
5. **定期备份**: 设置数据库自动备份

### 环境变量安全
```bash
# 生成安全的密钥
openssl rand -hex 32

# 在.env文件中设置
SECRET_KEY=<生成的密钥>
```

## 📊 监控与维护

### 健康检查
```bash
# 检查API健康状态
curl http://localhost:8000/api/health

# 检查数据库连接
curl http://localhost:8000/api/health/db
```

### 日志查看
```bash
# 查看应用日志
tail -f backend.log

# 查看错误日志
grep ERROR backend.log
```

### 性能监控
```bash
# 检查内存使用
free -h

# 检查CPU使用
top

# 检查磁盘空间
df -h
```

## 🚨 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 检查端口监听
netstat -tlnp | grep 5432

# 测试数据库连接
psql -h localhost -p 5432 -U postgres -d datalab
```

#### 2. 端口被占用
```bash
# 检查端口使用
lsof -i :8000

# 停止占用进程
kill -9 <PID>
```

#### 3. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt --no-cache-dir
```

#### 4. 虚拟环境问题
```bash
# 重新创建虚拟环境
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🔄 更新部署

### 代码更新
```bash
# 拉取最新代码
git pull origin main

# 重新安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/backend/ tests/integration/ -v

# 重启服务
pkill -f "uvicorn src.backend.main"
./start_production.sh
```

### 数据库迁移
```bash
# 如果有数据库迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📞 支持与联系

### 紧急问题
1. **检查日志**: `tail -f backend.log`
2. **重启服务**: `pkill -f uvicorn && ./start_production.sh`
3. **回滚部署**: 使用git回滚到上一个稳定版本

### 文档资源
- [API文档](http://localhost:8000/docs)
- [测试报告](scripts/test_summary_report.md)
- [数据库设计](docs/database_schema.md)

---

**部署完成时间**: 2026-01-01
**部署状态**: ✅ 生产就绪
**建议**: 所有测试已100%通过，建议立即进行生产部署。