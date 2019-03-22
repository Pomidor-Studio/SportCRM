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
        'HOST': '/cloudsql/sport-srm-test:us-east1:sport-crm-test',
        'USER': 'sport-test',
        'PASSWORD': 'sport-test',
        'NAME': 'sport-test-db',
    }
}

USE_GOOGLE_TASKS: bool = True

SOCIAL_AUTH_VK_OAUTH2_KEY = '6910281'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'e8dd6e2ae8dd6e2ae8dd6e2ae8e8b41f63ee8dde8dd6e2ab4484ba9ce75ec7c412f4127'
