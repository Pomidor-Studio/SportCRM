import dj_database_url

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'sportcrm.herokuapp.com',
    'sportcrm-test.herokuapp.com',
    'sportcrm-usa.herokuapp.com'
]

DATABASES['default'] = dj_database_url.config(
    conn_max_age=600, ssl_require=True,
    # django-multitenant db engine for foreign keys is broken
    engine='django.db.backends.postgresql_psycopg2'
)

