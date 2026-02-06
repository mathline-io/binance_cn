"""ASGI config for binance_resender project."""

import os

from django.core.asgi import get_asgi_application

from binance_resender.asgi_router import BinanceProtocolRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binance_resender.settings')

django_asgi_app = get_asgi_application()
application = BinanceProtocolRouter(django_asgi_app)
