release: python manage.py migrate --noinput
web: gunicorn sportcrm.wsgi --env DJANGO_SETTINGS_MODULE=sportcrm.settings.production --log-file -
