## 通用活动抓取服务

支持抓取（按配置的 host 与参数）：
- 定时抓取两个列表所有页，并逐条抓取活动详情（仅入库详情数据）

数据持久化到 PostgreSQL。

### 准备
1. 安装依赖
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量
复制 `.env.example` 为 `.env` 并填写必要字段（如 `TOKEN`）。

### 使用（抓取）
定时全量抓取：
```bash
# 默认每30分钟执行一次，读取环境变量中的分类ID
python -m src.cli run

# 通过参数覆盖
python -m src.cli run --interval-minutes 30 --domestic-id 232 --overseas-id 836 --max-pages 10
```

### 使用（网页）
```bash
python -m src.web
# 打开 http://localhost:8000
```

可通过环境变量自定义公共参数与 UA、重试、超时等。

### 备注
- 所有请求都使用 `application/x-www-form-urlencoded` 编码，默认携带 `User-Agent`、`Accept-Language` 等头。
- host 从环境变量 `BASE_URL` 读取。
- 数据库仅存储活动详情数据（表：`activity_detail`）。

### Docker 部署
1. 构建并启动：
```bash
docker compose up -d --build
```
2. 服务：
- Web: `http://localhost:8000`
- PostgreSQL: `localhost:5432`（账号密码参见 compose 文件）

### 可配置环境变量（.env）
- BASE_URL：目标服务 host
- TOKEN、USER_AGENT、ACCEPT_LANGUAGE 等请求头与鉴权
- DOMESTIC_CATEGORY_ID、OVERSEAS_CATEGORY_ID：列表分类ID
- SCHEDULE_INTERVAL_MINUTES：抓取间隔分钟
- MAX_PAGES：每轮抓取最大页数（可选）
- DELAY_MIN_SECONDS / DELAY_MAX_SECONDS：每次请求前的随机延迟（秒）

