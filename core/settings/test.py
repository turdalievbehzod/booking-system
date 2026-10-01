from .base import *

# Run Celery tasks inline and keep emails in memory (django.core.mail.outbox).
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Fast password hashing for tests only.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Tests fire many requests quickly.
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}  # noqa: F405
