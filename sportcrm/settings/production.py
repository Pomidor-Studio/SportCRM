import dj_database_url

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    '9170cfd8.ngrok.io'
]

DATABASES['default'] = dj_database_url.config(
    conn_max_age=600, ssl_require=True)
