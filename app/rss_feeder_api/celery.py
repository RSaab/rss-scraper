import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rss_feeder.settings')
 
app = Celery('rss_feeder')
app.config_from_object('django.conf:settings')
 
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'auto-update-feeds': {
        'task': 'rss_feeder_api.tasks.my_scheduled_job',
        'schedule': crontab(minute=0, hour=0), # run daily at midnight
    },
}


