"""Django settings for binance_resender project."""

from binance_resender.sqlite_compat import patch_sqlite_for_django
from pathlib import Path
import os

patch_sqlite_for_django()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$v+#@1cz%*9%31nu#-cj_5^)_q387yrtcfn#5xzcg%zm6#zz66'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'appSite.apps.AppsiteConfig',
    'appSender.apps.AppsenderConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'binance_resender.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'binance_resender.wsgi.application'
ASGI_APPLICATION = 'binance_resender.asgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'statics')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


def _endpoint_env(name: str, default: str) -> str:
    return os.getenv(name, default).rstrip('/')


BINANCE_ENDPOINTS = {
    # Spot + Margin
    'api': _endpoint_env('BINANCE_API_BASE_URL', 'https://api.binance.com'),
    'sapi': _endpoint_env('BINANCE_SAPI_BASE_URL', 'https://api.binance.com'),
    # USD-M Futures
    'fapi': _endpoint_env('BINANCE_FAPI_BASE_URL', 'https://fapi.binance.com'),
    # COIN-M Futures
    'dapi': _endpoint_env('BINANCE_DAPI_BASE_URL', 'https://dapi.binance.com'),
    # Vanilla Options
    'eapi': _endpoint_env('BINANCE_EAPI_BASE_URL', 'https://eapi.binance.com'),
    # Portfolio Margin
    'papi': _endpoint_env('BINANCE_PAPI_BASE_URL', 'https://papi.binance.com'),
    # Legacy options prefix compatibility
    'vapi': _endpoint_env('BINANCE_VAPI_BASE_URL', 'https://eapi.binance.com'),
}

BINANCE_WS_ENDPOINTS = {
    # Spot market and user-data streams
    'spot': _endpoint_env('BINANCE_WS_SPOT_URL', 'wss://stream.binance.com:9443'),
    # USD-M futures market and user-data streams
    'usdm': _endpoint_env('BINANCE_WS_USDM_URL', 'wss://fstream.binance.com'),
    # COIN-M futures market and user-data streams
    'coinm': _endpoint_env('BINANCE_WS_COINM_URL', 'wss://dstream.binance.com'),
    # Vanilla options streams
    'options': _endpoint_env('BINANCE_WS_OPTIONS_URL', 'wss://nbstream.binance.com/eoptions'),
    # Portfolio margin streams
    'pm': _endpoint_env('BINANCE_WS_PM_URL', 'wss://fstream.binance.com/pm'),
    # Cross margin risk stream
    'margin': _endpoint_env('BINANCE_WS_MARGIN_URL', 'wss://margin-stream.binance.com'),
}
