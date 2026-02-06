# Binance_resender（升级版）

Binance_resender 是一个 Binance HTTP API 转发服务，适合把策略服务部署在内地/内网机器，通过境外轻量转发节点访问 Binance。

本仓库已升级为支持新版本 Python 与新依赖，并修复了旧版的关键兼容问题：
- 升级到现代 Django / Uvicorn / Requests 版本
- 不再要求手改 Django 源码来替换 `sqlite3`
- 修复旧版转发器对 POST 参数和签名请求的改写问题
- 补齐并规范 Binance 端点映射（`api/sapi/fapi/dapi/eapi/papi`）

## 1. 环境要求

- Python: 3.12+（建议 3.12 或 3.13）
- 系统: Linux（Debian/Ubuntu/CentOS 均可）

> 如果系统自带 sqlite 版本过低，项目会自动尝试使用 `pysqlite3-binary`，无需修改 Django 安装目录源码。

## 2. 安装

```bash
cd /root
git clone https://github.com/pyted/binance_resender
cd binance_resender
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 3. 初始化与启动

### 3.1 执行迁移

```bash
python manage.py migrate
```

### 3.2 创建管理员（首次）

```bash
python manage.py createsuperuser
```

### 3.3 启动服务

```bash
python -m uvicorn binance_resender.asgi:application --host 0.0.0.0 --port 80
```

## 4. 端点映射（最新版）

默认映射（可通过环境变量覆盖）：

- `api/*` -> `https://api.binance.com/api/*`
- `sapi/*` -> `https://api.binance.com/sapi/*`
- `fapi/*` -> `https://fapi.binance.com/fapi/*`
- `dapi/*` -> `https://dapi.binance.com/dapi/*`
- `eapi/*` -> `https://eapi.binance.com/eapi/*`
- `papi/*` -> `https://papi.binance.com/papi/*`
- `vapi/*` -> 兼容旧插件，默认转发到 `https://eapi.binance.com/vapi/*`

可选环境变量：

```bash
export BINANCE_API_BASE_URL="https://api.binance.com"
export BINANCE_SAPI_BASE_URL="https://api.binance.com"
export BINANCE_FAPI_BASE_URL="https://fapi.binance.com"
export BINANCE_DAPI_BASE_URL="https://dapi.binance.com"
export BINANCE_EAPI_BASE_URL="https://eapi.binance.com"
export BINANCE_PAPI_BASE_URL="https://papi.binance.com"
export BINANCE_VAPI_BASE_URL="https://eapi.binance.com"
```

## 5. 白名单与日志

后台地址：`/admin`

- `1. 白名单`：允许访问转发服务的客户端 IP
- `2. 日志管理`：是否开启转发日志
- `3. 日志信息`：查看转发记录与错误

## 6. 关键升级说明

### 6.1 不再修改 Django 源码

旧文档中的做法：

```python
# from sqlite3 import dbapi2 as Database
from pysqlite3 import dbapi2 as Database
```

该方式已废弃。现在项目内置 sqlite 兼容补丁，自动处理低版本 sqlite 场景，不污染站点包目录。

### 6.2 签名请求兼容

转发层现在会保留原始 query string 和 body，避免签名参数顺序或编码在转发中被破坏。

### 6.3 上游状态码透传

Binance 返回的 4xx/5xx（包括限流码）会原样透传给客户端，便于策略端准确处理重试和风控。

## 7. 兼容示例（binance_interface）

```python
from binance_interface.api import API

proxy_host = "http://your-resender-host"
api = API(proxy_host=proxy_host)
result = api.spot.market.get_ticker_bookTicker(symbol="BTCUSDT")
print(result)
```
