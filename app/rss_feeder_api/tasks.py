from rss_feeder_api.celery import app

from rss_feeder_api.models import Feed

@app.task
def my_scheduled_job():
    print("cron job")
    updateAllFeeds()

def updateAllFeeds():
    feeds = Feed.objects.filter(flagged=False)
    for feed in feeds:
        feed.force_update()
    print("Done!")