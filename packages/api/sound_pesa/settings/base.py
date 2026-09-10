"""
Django settings for Sound Pesa project.
Base settings shared across all environments.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_extensions',
    'django_celery_beat',
    'django_prometheus',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.wallets',
    'apps.transactions',
    'apps.blockchain',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'sound_pesa.middleware.StructuredLoggingMiddleware',
    'sound_pesa.middleware.SecurityAuditMiddleware',
    'sound_pesa.middleware.TransactionAuditMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'sound_pesa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'sound_pesa.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='soundpesa'),
        'USER': config('POSTGRES_USER', default='soundpesa'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='devpassword'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
    }
}

# Cache configuration
REDIS_URL = config('REDIS_URL', default='redis://redis:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': '1.0',
    'ALLOWED_VERSIONS': ['1.0'],
    'EXCEPTION_HANDLER': 'sound_pesa.exceptions.custom_exception_handler',
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': config('JWT_ALGORITHM', default='HS256'),
    'SIGNING_KEY': config('JWT_SECRET_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Vault Configuration
VAULT_URL = config('VAULT_URL', default='http://vault:8200')
VAULT_TOKEN = config('VAULT_TOKEN', default='dev-token')

# Blockchain Configuration
BLOCKCHAIN_NETWORKS = {
    'bitcoin': {
        'network': config('BITCOIN_NETWORK', default='testnet'),
        'rpc_url': config('BITCOIN_RPC_URL', default='http://bitcoin-core:8332'),
        'rpc_user': config('BITCOIN_RPC_USER', default='bitcoin'),
        'rpc_password': config('BITCOIN_RPC_PASSWORD', default='password'),
    },
    'ethereum': {
        'network': config('ETHEREUM_NETWORK', default='goerli'),
        'rpc_url': config('ETHEREUM_RPC_URL', default='http://geth:8545'),
        'ws_url': config('ETHEREUM_WS_URL', default='ws://geth:8546'),
    },
    'cardano': {
        'network': config('CARDANO_NETWORK', default='testnet'),
        'node_socket': config('CARDANO_NODE_SOCKET', default='/opt/cardano/db/socket'),
    },
    'polkadot': {
        'network': config('POLKADOT_NETWORK', default='westend'),
        'ws_url': config('POLKADOT_WS_URL', default='ws://polkadot:9944'),
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Logging configuration
# Only wire the file handler when the target directory exists so the app can
# run outside its container (e.g. on a developer machine) without crashing.
_LOG_DIR_EXISTS = os.path.isdir('/app/logs')

_file_handlers = {}
_file_log_handlers = []
if _LOG_DIR_EXISTS:
    _file_handlers['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': '/app/logs/django.log',
        'formatter': 'verbose',
    }
    _file_log_handlers = ['file']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'sound_pesa.logging_formatters.JSONFormatter',
        },
        'transaction_json': {
            '()': 'sound_pesa.logging_formatters.TransactionLogFormatter',
        },
        'security_json': {
            '()': 'sound_pesa.logging_formatters.SecurityLogFormatter',
        },
        'blockchain_json': {
            '()': 'sound_pesa.logging_formatters.BlockchainLogFormatter',
        },
    },
    'handlers': {
        **_file_handlers,
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
        'transaction_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'transaction_json' if not DEBUG else 'verbose',
        },
        'security_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'security_json' if not DEBUG else 'verbose',
        },
        'blockchain_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'blockchain_json' if not DEBUG else 'verbose',
        },
    },
    'root': {
        'handlers': ['console'] + _file_log_handlers,
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'] + _file_log_handlers,
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'sound_pesa': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'sound_pesa.transactions': {
            'handlers': ['transaction_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sound_pesa.security': {
            'handlers': ['security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'sound_pesa.blockchain': {
            'handlers': ['blockchain_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.transactions': {
            'handlers': ['transaction_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.blockchain': {
            'handlers': ['blockchain_console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}