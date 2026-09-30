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
    print("⚠️  Warning: .env file not found!")

# DJANGO CORE SETTINGS
DJANGO_SETTINGS_MODULE = env.str('DJANGO_SETTINGS_MODULE', default='core.settings.dev')
SECRET_KEY = env.str('SECRET_KEY', default='unsafe-secret-key')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[]
)

CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[]
)

# DATABASE SETTINGS
DB_NAME = env.str('DB_NAME', default='myproject')
DB_USER = env.str('DB_USER', default='myuser')
DB_PASSWORD = env.str('DB_PASSWORD', default='mypassword')
DB_HOST = env.str('DB_HOST', default='127.0.0.1')
DB_PORT = env.str('DB_PORT', default='5432')  # 5432 local / 6432 for PgBouncer

# Optional for PgBouncer if you want SSL
DB_SSLMODE = env.str('DB_SSLMODE', default='prefer')

# telegram bot
TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = env.str('TELEGRAM_CHANNEL_ID')

# Email verification via Resend
RESEND_API_KEY = env.str('RESEND_API_KEY', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='PetCare <noreply@petcare.com>')
DEBUG_EMAIL = env.bool('DEBUG_EMAIL', default=True)