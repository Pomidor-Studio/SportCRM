import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('CELERY_CONFIG_MODULE', 'sportcrm.settings.celery_config')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportcrm.settings.gcp_test')

# set the default Django settings module for the 'celery' program.
app = Celery('sportcrm',
             include=["bot.api.cron.manager_events",
                      "bot.background_views"
                      ])
app.config_from_envvar('CELERY_CONFIG_MODULE')

app.conf.beat_schedule = {

    # - description: "daily birthday job"
    "birthday": {
        "task": "bot.background_views.birthday",
        "schedule": crontab(minute="0", hour="3")
    },

    # - description: "daily birthday job"
    "receivables": {
        "task": "bot.background_views.receivables",
        "schedule": crontab(minute="0", hour="8")
    },

    # - description: "daily future event job"
    "future_event": {
        "task": "bot.background_views.future_event",
        "schedule": crontab(minute="0", hour="10")
    },

    # - description: "check every ten minutes for finished events"
    "event_closing": {
        "task": "bot.api.cron.manager_events.event_closing",
        "schedule": crontab(minute="10", hour="*")
    },
}

