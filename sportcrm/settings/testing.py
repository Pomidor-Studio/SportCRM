import tempfile

import dj_database_url

from .base import *  # noqa

DEBUG = False

# Temporary file storage
TEMP_DIR = tempfile.mkdtemp(prefix='rdc')
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEMP_DIR  # noqa: F405

DATABASE_POOL_ARGS = {
    'max_overflow': 20,
    'pool_size': 20,
    'recycle': 100
}

DATABASES['default'] = dj_database_url.config(
    conn_max_age=600,
    engine='django_postgrespool'
)

# Disables whitenoise on testing cases

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

CELERY_TASK_ALWAYS_EAGER = True  # Emulate async work of celery
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
