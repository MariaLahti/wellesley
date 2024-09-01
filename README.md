# Wellesley - 多平台活动数据采集服务

## 快速开始

### 环境准备

1. **创建虚拟环境并安装依赖**:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. **配置环境变量**:
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的配置参数
```

### 运行应用

#### CLI 抓取器（定时数据收集）

**Tiga 平台抓取**:
```bash
# 使用默认配置运行 Tiga 抓取器（定时执行）
python -m src.cli tiga

# 自定义参数运行
python -m src.cli tiga --interval-minutes 30 --max-pages 10
```

**Gaia 平台抓取**:
```bash
# 单次执行 Gaia 抓取器
python -m src.cli gaia

# 指定分类运行
python -m src.cli gaia --catalogs E L SW

# 定时执行
python -m src.cli gaia --interval-minutes 60 --max-pages 5
```

#### Web 仪表板

```bash
python -m src.web
# 访问 http://localhost:8000
```

### Docker 部署

```bash
# 构建并启动所有服务（Web、抓取器、PostgreSQL）
docker compose up -d --build

# 服务访问地址：
# - Web 界面: http://localhost:8000
# - PostgreSQL: localhost:5432
```

## 配置说明

### 通用配置
- **DATABASE_URL**: PostgreSQL 连接字符串
- **TIMEOUT_SECONDS**, **RETRY_TOTAL**, **RETRY_BACKOFF**: HTTP 客户端设置
- **DELAY_MIN_SECONDS**, **DELAY_MAX_SECONDS**: 请求间随机延时
- **WEB_USERNAME**, **WEB_PASSWORD**, **SECRET_KEY**: Web 界面认证

### Tiga 平台配置 (TIGA_ 前缀)
- **TIGA_BASE_URL**: 目标 API 主机地址（必需）
- **TIGA_TOKEN**: API 认证令牌（必需）
- **TIGA_USER_AGENT**, **TIGA_ACCEPT_LANGUAGE**: 请求头设置
- **TIGA_CITY_ID**, **TIGA_DEVICE**, **TIGA_CHANNEL** 等: 平台特定参数
- **TIGA_DOMESTIC_CATEGORY_ID**, **TIGA_OVERSEAS_CATEGORY_ID**: 分类设置
- **TIGA_SCHEDULE_INTERVAL_MINUTES**, **TIGA_MAX_PAGES**: 调度设置

### Gaia 平台配置 (GAIA_ 前缀)
- **GAIA_BASE_URL**: 目标 API 主机地址
- **GAIA_USER_AGENT**, **GAIA_ACCEPT_LANGUAGE**: 请求头设置
- **GAIA_CATALOGS**: 逗号分隔的分类列表 (E,L,SW,S,WE,SY)
- **GAIA_SCHEDULE_INTERVAL_MINUTES**, **GAIA_MAX_PAGES**: 调度设置
