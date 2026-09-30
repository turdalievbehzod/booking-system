from core import config
from core.log_config import get_logging_config
from .base import *

# Development logging
LOGGING = get_logging_config(environment='development')

# Show SQL queries in console (optional)
LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

DEBUG = True
SECRET_KEY = config.SECRET_KEY
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Local DB directly via psycopg2
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config.DB_NAME,
        'USER': config.DB_USER,
        'PASSWORD': config.DB_PASSWORD,
        'HOST': config.DB_HOST,
        'PORT': config.DB_PORT,
    }
}

# Optional: local-specific logging or debug toolbar
INSTALLED_APPS += [
    # 'debug_toolbar',
]

DEBUG_EMAIL = config.DEBUG_EMAIL
RESEND_API_KEY = config.RESEND_API_KEY
DEFAULT_FROM_EMAIL = config.DEFAULT_FROM_EMAIL

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}