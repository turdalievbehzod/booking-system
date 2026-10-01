from core import config

from .base import *
from .base import DATABASES

DEBUG = False
ALLOWED_HOSTS = config.ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = config.CSRF_TRUSTED_ORIGINS

DATABASES['default']['CONN_MAX_AGE'] = 0  # PgBouncer handles pooling
DATABASES['default']['OPTIONS'] = {'sslmode': config.DB_SSLMODE}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
