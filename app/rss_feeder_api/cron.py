from rss_feeder_api.models import Feed

def my_scheduled_job():
	print ("cron job")
	updateAllFeeds()

def updateAllFeeds():
	feeds = Feed.objects.all(flagged=False)
	for feed in feeds:
		feed.force_update()