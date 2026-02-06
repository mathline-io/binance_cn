# Binance_resender（升级版）

Binance_resender 是一个 Binance HTTP API 转发服务，适合把策略服务部署在内地/内网机器，通过境外轻量转发节点访问 Binance。

本仓库已升级为支持新版本 Python 与新依赖，并修复了旧版的关键兼容问题：
- 升级到现代 Django / Uvicorn / Requests 版本
- 不再要求手改 Django 源码来替换 `sqlite3`
- 修复旧版转发器对 POST 参数和签名请求的改写问题
- 补齐并规范 Binance 端点映射（`api/sapi/fapi/dapi/eapi/papi`）
- 新增 Binance WebSocket 转发（`/ws/spot|usdm|coinm|options|pm|margin`）

## 1. 环境要求

- Python: 3.9+（建议 3.12 或 3.13）
- 系统: Linux（Debian/Ubuntu/CentOS 均可）

> 如果系统自带 sqlite 版本过低，项目会自动尝试使用 `pysqlite3-binary`，无需修改 Django 安装目录源码。
>
> 依赖会按 Python 版本自动选择 Django：
> - Python 3.12+ -> Django 6
> - Python 3.10/3.11 -> Django 5.2 LTS
> - Python 3.9 -> Django 4.2 LTS

## 2. 安装

下面分别提供 Ubuntu 和 CentOS 9 的完整安装流程。两套流程都会安装到项目本地虚拟环境，不污染系统 Python。

### 2.1 Ubuntu（22.04/24.04）

#### 2.1.1 安装系统依赖

```bash
sudo apt update
sudo apt install -y git curl ca-certificates \
  python3 python3-venv python3-pip \
  build-essential libssl-dev libffi-dev zlib1g-dev
```

#### 2.1.2 下载项目

```bash
cd /opt
sudo git clone https://github.com/pyted/binance_resender.git
sudo chown -R $USER:$USER /opt/binance_resender
cd /opt/binance_resender
```

#### 2.1.3 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
```

#### 2.1.4 初始化数据库与管理员

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 2.1.5 启动服务

```bash
python -m uvicorn binance_resender.asgi:application --host 0.0.0.0 --port 80
```

可选放行防火墙端口（如果开启了 UFW）：

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 2.2 CentOS Stream 9

#### 2.2.1 安装系统依赖

```bash
sudo dnf -y update
sudo dnf -y install git curl ca-certificates \
  python3 python3-pip python3-devel \
  gcc gcc-c++ make openssl-devel libffi-devel
```

#### 2.2.2 下载项目

```bash
cd /opt
sudo git clone https://github.com/pyted/binance_resender.git
sudo chown -R $USER:$USER /opt/binance_resender
cd /opt/binance_resender
```

#### 2.2.3 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
```

#### 2.2.4 初始化数据库与管理员

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 2.2.5 启动服务

```bash
python -m uvicorn binance_resender.asgi:application --host 0.0.0.0 --port 80
```

可选放行防火墙端口（如果开启 firewalld）：

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

> CentOS Stream 9 默认 Python 多为 3.9，会自动安装 Django 4.2 LTS；这是预期行为。

### 2.3 可选：配置 systemd 常驻运行（Ubuntu/CentOS 通用）

创建服务文件：

```bash
sudo tee /etc/systemd/system/binance-resender.service >/dev/null <<'EOF'
[Unit]
Description=Binance Resender
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/binance_resender
ExecStart=/opt/binance_resender/.venv/bin/python -m uvicorn binance_resender.asgi:application --host 0.0.0.0 --port 80
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now binance-resender
sudo systemctl status binance-resender
```

查看日志：

```bash
sudo journalctl -u binance-resender -f
```

### 2.4 快速安装（通用）

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

## 4. HTTP 端点映射（最新版）

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

## 5. WebSocket 端点映射（新增）

默认 WebSocket 路由：

- `/ws/spot/*` -> `wss://stream.binance.com:9443/*`
- `/ws/usdm/*` -> `wss://fstream.binance.com/*`
- `/ws/coinm/*` -> `wss://dstream.binance.com/*`
- `/ws/options/*` -> `wss://nbstream.binance.com/eoptions/*`
- `/ws/pm/*` -> `wss://fstream.binance.com/pm/*`
- `/ws/margin/*` -> `wss://margin-stream.binance.com/*`

示例：

- Spot 单流：`ws://IP/ws/spot/ws/btcusdt@trade`
- Spot 组合流：`ws://IP/ws/spot/stream?streams=btcusdt@trade/ethusdt@trade`
- U 本位：`ws://IP/ws/usdm/ws/btcusdt@aggTrade`
- 币本位：`ws://IP/ws/coinm/ws/btcusd_perp@ticker`

可选环境变量：

```bash
export BINANCE_WS_SPOT_URL="wss://stream.binance.com:9443"
export BINANCE_WS_USDM_URL="wss://fstream.binance.com"
export BINANCE_WS_COINM_URL="wss://dstream.binance.com"
export BINANCE_WS_OPTIONS_URL="wss://nbstream.binance.com/eoptions"
export BINANCE_WS_PM_URL="wss://fstream.binance.com/pm"
export BINANCE_WS_MARGIN_URL="wss://margin-stream.binance.com"
```

## 6. 白名单与日志

后台地址：`/admin`

- `1. 白名单`：允许访问转发服务的客户端 IP
- `2. 日志管理`：是否开启转发日志
- `3. 日志信息`：查看转发记录与错误

## 7. 关键升级说明

### 7.1 不再修改 Django 源码

旧文档中的做法：

```python
# from sqlite3 import dbapi2 as Database
from pysqlite3 import dbapi2 as Database
```

该方式已废弃。现在项目内置 sqlite 兼容补丁，自动处理低版本 sqlite 场景，不污染站点包目录。

### 7.2 签名请求兼容

转发层现在会保留原始 query string 和 body，避免签名参数顺序或编码在转发中被破坏。

### 7.3 上游状态码透传

Binance 返回的 4xx/5xx（包括限流码）会原样透传给客户端，便于策略端准确处理重试和风控。

## 8. 兼容示例（python-binance REST + WS）

```python
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.ws.streams import BinanceSocketManager

proxy_host = "http://your-resender-host"
client = Client(api_key="", api_secret="", ping=False)

# 把 python-binance 的各类 REST URL 指向 Binance_resender
client.API_URL = f"{proxy_host}/api"
client.MARGIN_API_URL = f"{proxy_host}/sapi"
client.FUTURES_URL = f"{proxy_host}/fapi"
client.FUTURES_COIN_URL = f"{proxy_host}/dapi"
client.OPTIONS_URL = f"{proxy_host}/eapi"

# WS 走转发器（需在创建 WS manager 前设置）
ws_scheme = "ws" if proxy_host.startswith("http://") else "wss"
ws_host = proxy_host.split("://", 1)[-1]
BinanceSocketManager.STREAM_URL = f"{ws_scheme}://{ws_host}/ws/spot/"
BinanceSocketManager.FSTREAM_URL = f"{ws_scheme}://{ws_host}/ws/usdm/"
BinanceSocketManager.DSTREAM_URL = f"{ws_scheme}://{ws_host}/ws/coinm/"
BinanceSocketManager.OPTIONS_URL = f"{ws_scheme}://{ws_host}/ws/options/"

try:
    result = client.get_orderbook_ticker(symbol="BTCUSDT")
    print(result)
except BinanceAPIException as exc:
    print(f"Binance API error: {exc}")
```
