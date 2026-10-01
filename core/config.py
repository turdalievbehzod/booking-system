import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment manager
env = environ.Env()

# Try to find .env file in multiple possible locations
env_path = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(BASE_DIR.parent, '.env')

# Read the .env file from the found location
if os.path.exists(env_path):
    environ.Env.read_env(env_path)
else:
    print("Warning: .env file not found, using environment variables only.")

# DJANGO CORE SETTINGS
DJANGO_SETTINGS_MODULE = env.str('DJANGO_SETTINGS_MODULE', default='core.settings.dev')
SECRET_KEY = env.str('SECRET_KEY', default='unsafe-secret-key')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# Business timezone: availability hours are entered in this timezone.
TIME_ZONE = env.str('TIME_ZONE', default='Asia/Tashkent')

# DATABASE SETTINGS
DB_NAME = env.str('DB_NAME', default='booking')
DB_USER = env.str('DB_USER', default='booking')
DB_PASSWORD = env.str('DB_PASSWORD', default='booking')
DB_HOST = env.str('DB_HOST', default='127.0.0.1')
DB_PORT = env.str('DB_PORT', default='5432')  # 5432 local / 6432 for PgBouncer
DB_SSLMODE = env.str('DB_SSLMODE', default='prefer')

# CELERY / REDIS
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/2')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)

# EMAIL (console backend prints emails to the terminal in development)
EMAIL_BACKEND = env.str('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env.str('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='Booking <noreply@example.com>')
