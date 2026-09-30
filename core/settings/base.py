"""
Base Django settings for core project.

This file contains shared configuration for all environments.
Environment-specific overrides (local/production) live in:
- core/settings/dev.py
- core/settings/prod.py
"""
from datetime import timedelta
from pathlib import Path


# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / 'petcare-master'

# -------------------------------------------------------------------
# APPLICATIONS
# -------------------------------------------------------------------

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_celery_beat',
    'django_celery_results',
]

MY_APPS = [
    'apps.shared',
    'apps.users',
    'apps.about',
    'apps.blogs',
    'apps.contact',
    'apps.services',
]

INSTALLED_APPS += THIRD_PARTY_APPS
INSTALLED_APPS += MY_APPS
INSTALLED_APPS += ['corsheaders']

# -------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.shared.middlewares.permission.EndpointPermissionMiddleware',

    # "corsheaders.middleware.CorsMiddleware",
]

# -------------------------------------------------------------------
# URLS / WSGI
# -------------------------------------------------------------------

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# -------------------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR],
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

# -------------------------------------------------------------------
# AUTH / PASSWORDS
# -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
    ('ru', 'Russian'),
    ('uz', 'Uzbek'),
)

LOCALE_PATHS = (BASE_DIR / 'locale',)

TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent.parent / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent.parent / 'media'

# -------------------------------------------------------------------
# DEFAULT PRIMARY KEY TYPE
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'apps.users.utils.custom_backend.MultiFieldBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# -------------------------------------------------------------------
# DJANGO REST FRAMEWORK CONFIG
# -------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # 'DEFAULT_FILTER_BACKENDS': [
    #     'django_filters.rest_framework.DjangoFilterBackend',
    # ],
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.shared.exceptions.handler.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'apps.shared.utils.custom_pagination.CustomPageNumberPagination',
}

# -------------------------------------------------------------------
# DRF SPECTACULAR CONFIG
# -------------------------------------------------------------------


SPECTACULAR_SETTINGS = {
    'TITLE': 'PetCare API',
    'DESCRIPTION': 'Veterinary service backend',
    'VERSION': '1.0.0',
}

# -------------------------------------------------------------------
# SIMPLEJWT CONFIG
# -------------------------------------------------------------------


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
}

# -------------------------------------------------------------------
# CELERY CONFIG
# -------------------------------------------------------------------

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/2'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {}

# -------------------------------------------------------------------
# LANGUAGES CONFIG
# -------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True

# -------------------------------------------------------------------
# EMAIL CONFIG — Resend API (no SMTP)
# -------------------------------------------------------------------

RESEND_API_KEY = ""
DEFAULT_FROM_EMAIL = "PetCare <noreply@petcare.com>"

# -------------------------------------------------------------------
# VERIFICATION CODE SETTINGS
# -------------------------------------------------------------------

# Seconds before a resend is allowed after the previous code was issued
VERIFICATION_CODE_RESEND_COOLDOWN = 60
# Max wrong-code attempts before the code is invalidated
VERIFICATION_CODE_MAX_ATTEMPTS = 5
