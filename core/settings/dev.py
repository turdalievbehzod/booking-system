from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '*']

# Any local frontend (Vite, CRA...) may call the API in development.
CORS_ALLOW_ALL_ORIGINS = True
