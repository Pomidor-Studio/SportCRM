import dj_database_url

from .base import *  # noqa

DEBUG = True

# SECURITY WARNING: App Engine's security features ensure that it is safe to
# have ALLOWED_HOSTS = ['*'] when the app is deployed. If you deploy a Django
# app not on App Engine, make sure to set an appropriate host here.
# See https://docs.djangoproject.com/en/2.1/ref/settings/
ALLOWED_HOSTS = ['*']

# django-multitenant db engine for foreign keys is broken, use default
# TODO: hide secrets
#  https://www.andreafortuna.org/programming/google-app-engine-and-python-a-correct-way-to-store-configuration-variables/
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '/cloudsql/sportadmin:europe-west1:sa-prod1',
        'USER': 'sport-prod',
        'PASSWORD': 'Y88c5ZwJ6a8qZge',
        'NAME': 'sport-prod',
    }
}

# redislabs.com redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://:B8UBQa36iTJ9ys1NOcJYZnDEd4VLRh6q@redis-17157.c1.us-east1-2.gce.cloud.redislabs.com:17157/django-cache',
        "TIMEOUT": 600,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        }
    }
}

QR_CODE_CACHE_ALIAS = 'default'

USE_GOOGLE_TASKS: bool = True
GCP_TASK_PROJECT = 'sportadmin'
GCP_TASK_QUEUE = 'sa-prod-queue'
GCP_TASK_LOCATION = 'europe-west1'

SOCIAL_AUTH_VK_OAUTH2_KEY = '6910281'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'FlahTFK72JyNibzjWXhE'
VK_GROUP_TOKEN = 'e8dd6e2ae8dd6e2ae8dd6e2ae8e8b41f63ee8dde8dd6e2ab4484ba9ce75ec7c412f4127'



YANDEX_METRICA_COUNTER_ID = '53063764' # sportadmin.ru metrika
YANDEX_METRICA_WEBVISOR = True

GOOGLE_ANALYTICS_JS_PROPERTY_ID = 'UA-136374884-2'
GOOGLE_ANALYTICS_SITE_SPEED_SAMPLE_RATE = 100

DISABLE_MANAGER_PERMISSION_FOR_COMPANIES = (4,)

MAIL_FROM = 'support@yoursport.club'
MAIL_MANAGER = 'support@yoursport.club'
