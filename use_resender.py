from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.ws.streams import BinanceSocketManager


def create_resender_client(proxy_host: str, api_key: str = "", api_secret: str = "") -> Client:
    host = proxy_host.rstrip("/")
    client = Client(api_key=api_key, api_secret=api_secret, ping=False)
    # Point all REST groups to Binance_resender routes.
    client.API_URL = f"{host}/api"
    client.MARGIN_API_URL = f"{host}/sapi"
    client.FUTURES_URL = f"{host}/fapi"
    client.FUTURES_COIN_URL = f"{host}/dapi"
    client.OPTIONS_URL = f"{host}/eapi"
    return client


def patch_python_binance_ws_base(proxy_host: str):
    host = proxy_host.rstrip("/")
    ws_scheme = "wss" if host.startswith("https://") else "ws"
    host_no_scheme = host.split("://", 1)[-1]
    ws_base = f"{ws_scheme}://{host_no_scheme}"
    BinanceSocketManager.STREAM_URL = f"{ws_base}/ws/spot/"
    BinanceSocketManager.FSTREAM_URL = f"{ws_base}/ws/usdm/"
    BinanceSocketManager.DSTREAM_URL = f"{ws_base}/ws/coinm/"
    BinanceSocketManager.OPTIONS_URL = f"{ws_base}/ws/options/"


if __name__ == "__main__":
    proxy_host = "http://43.156.53.213"  # Binance_resender 地址
    client = create_resender_client(proxy_host=proxy_host)
    patch_python_binance_ws_base(proxy_host=proxy_host)
    try:
        ticker_result = client.get_orderbook_ticker(symbol="BTCUSDT")
        print(ticker_result)
    except BinanceAPIException as exc:
        print(f"Binance API error: {exc}")
