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
        "task": "bot.api.cron.cron_client_events.birthday",
        "schedule": crontab(minute="0", hour="13")
    },

    # - description: "daily birthday job"
    "receivables": {
        "task": "bot.api.cron.cron_client_events.receivables",
        "schedule": crontab(minute="0", hour="18")
    },

    # - description: "daily future event job"
    "future_event": {
        "task": "bot.api.cron.cron_client_events.future_event",
        "schedule": crontab(minute="0", hour="20")
    },

    # - description: "check every ten minutes for finished events"
    "event_closing": {
        "task": "bot.api.cron.manager_events.event_closing",
        "schedule": crontab(minute="10", hour="*")
    },
}

