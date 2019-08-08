import os
from celery import Celery
import django

os.environ.setdefault('CELERY_CONFIG_MODULE', 'sportcrm.settings.celery_config')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportcrm.settings.gcp_test')
django.setup()

# set the default Django settings module for the 'celery' program.
app = Celery('sportcrm', )
app.config_from_envvar('CELERY_CONFIG_MODULE')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
