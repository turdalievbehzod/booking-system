import os

from core import config

from .base import *
from .base import DATABASES, MIDDLEWARE

DEBUG = False

# No silent fallback in production: a missing key must stop the app from starting.
SECRET_KEY = config.env.str('SECRET_KEY')

ALLOWED_HOSTS = config.ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = config.CSRF_TRUSTED_ORIGINS

# Render sets this to the service's public hostname (e.g. booking-api.onrender.com).
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f'https://{RENDER_EXTERNAL_HOSTNAME}']

# Managed hosts (Render) give a single DATABASE_URL; otherwise use the DB_* variables.
if os.environ.get('DATABASE_URL'):
    DATABASES = {'default': config.env.db_url('DATABASE_URL')}
else:
    DATABASES['default']['CONN_MAX_AGE'] = 0  # PgBouncer handles pooling
    DATABASES['default']['OPTIONS'] = {'sslmode': config.DB_SSLMODE}

# Static files (admin, API docs) are served by gunicorn through WhiteNoise.
MIDDLEWARE = [*MIDDLEWARE]
MIDDLEWARE.insert(MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
                  'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600

# With DEBUG=False Django logs nothing to the console by default;
# send errors to stdout so they show up in the host's logs.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}},
}
