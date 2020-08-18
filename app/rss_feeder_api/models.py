from django.db import models

from django.db import transaction
from django.shortcuts import get_object_or_404

import datetime
import time

from django.utils import timezone

import backoff
import dramatiq

from django.utils.encoding import smart_text as smart_unicode
from django.utils.translation import ugettext_lazy as _

from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ

from rss_feeder_api import managers

from django.core.validators import URLValidator
import feedparser

from rss_feeder.settings import MAX_FEED_UPDATE_RETRIES

import json

def backoff_hdlr(details):
    print(details)
    print ("Backing off {wait:0.1f} seconds afters {tries} tries "
           "calling function {target} with args {args} and kwargs "
           "{kwargs}".format(**details))
    feed = details['args'][0]
    wait = details['wait']
    notification = Notification(feed=feed, owner=feed.owner, title='BackOff', message=f'Feed: {feed.id}, {feed.link} failed to update, retrying in {wait:0.1f}', is_error=True)
    notification.save()

@dramatiq.actor
def feed_update_failure(message_data, exception_data):
    """
    A dramatiq callback on each failed attempt for a feed update
    the user will notified by inserting a notification in the db 
    only on the final failure

    TODO: log all errors to somewhere for metrics and analysis
    """
    feed_id = message_data['args'][0]
    feed = Feed.objects.get(pk=feed_id)

    # mark feed as failed to update and stop updateing it automatically
    feed.flagged = True
    feed.save()

    notification = Notification(feed=feed, owner=feed.owner, title=exception_data['type'], message=exception_data['message']+f'[Feed: {feed.id}, {feed.link}]', is_error=True)
    notification.save()
    print("dramatiq callback: feed update error")


@dramatiq.actor
def feed_update_success(message_data, result):
    """
    A dramatiq callback on successful attempt for a feed update
    the user will notified by inserting a notification in the db 

    TODO ??maybe log this also for checking failure/success rates?
    """

    feed_id = message_data['args'][0]
    feed = Feed.objects.get(pk=feed_id)

    notification = Notification(feed=feed, owner=feed.owner, title='FeedUpdated', message=f'Feed: {feed.id}, {feed.link}, {feed.updated_at}]', is_error=False)
    notification.save()
    print("dramatiq callback: : feed update success")

    
# Exceptions #################################################   
class FeedError(Exception):
    """
    An error occurred when fetching the feed
    
    If it was parsed despite the error, the feed and entries will be available:
        e.feed      None if not parsed
        e.entries   Empty list if not parsed
    """
    def __init__(self, *args, **kwargs):
        super(FeedError, self).__init__(*args, **kwargs)


# End: Exceptions #################################################   

# Feed #################################################   
class Feed(models.Model):
    '''
    The feeds model describes a registered field. 
    Its contains feed related information
    as well as user related info and other meta data
    '''
    link = models.URLField(max_length = 200)
    title = models.CharField(max_length=200, null=True)
    subtitle = models.CharField(max_length=200, null=True)

    description = models.TextField(null=True)
    language = models.CharField(max_length=5, null=True)
    copyright = models.CharField(max_length=50, null=True)
    ttl = models.PositiveIntegerField(null=True)
    atomLogo = models.URLField(max_length = 200, null=True)
    pubdate = models.DateTimeField(null=True)
    nickname = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    following = models.BooleanField(default=True)

    flagged = models.BooleanField(default=False) 

    owner = models.ForeignKey('auth.User', related_name='feeds', on_delete=models.CASCADE)

    class Meta: 
        verbose_name = ("Feed")
        verbose_name_plural = ("Feeds")
        ordering = ('-updated_at',)
        unique_together = ('link', 'owner')

    
    objects = managers.FeedManager()


    def __str__(self):
        return f'Nickname: {self.nickname}'


    def save(self, *args, **kwargs):

        # assure minimum required fields   
        assert self.link
        assert self.nickname

        super(Feed, self).save(*args, **kwargs)

        assert self.id > 0

        return

    def force_update(self, *args, **kwargs):
        print("Forcing update...")
        self._updateFeed.send_with_options(args=(self.id,), on_failure=feed_update_failure, on_success=feed_update_success)
        return

    @backoff.on_exception(backoff.expo, FeedError, max_tries=MAX_FEED_UPDATE_RETRIES, on_backoff=backoff_hdlr)
    def _fetch_feed(self):
        '''
        internal method to get feed details from the link provided in self

        returns raw feed and entry details as returned by the feedparser library
        '''
        # Request and parse the feed
        link = self.link
        d = feedparser.parse(link)
        status  = d.get('status', 200)
        feed    = d.get('feed', None)
        entries = d.get('entries', None)
        if status in (200, 302, 304, 307):
            if (
                feed is None
                or 'title' not in feed
                or 'link' not in feed
            ):
                raise FeedError('Feed parsed but with invalid contents')
            
            return feed, entries

        if status in (404, 500, 502, 503, 504):
            raise FeedError('Temporary error %s' % status)

        # Follow permanent redirection
        if status == 301:
            # Avoid circular redirection
            self.link = d.get('href', self.link)
            return self._fetch_feed()

        if status == 410:
            raise FeedError('Feed has gone')

        # Unknown status
        raise FeedError('Unrecognised HTTP status %s' % status)


    @dramatiq.actor(max_retries=0, max_age=10000)#, throws=FeedError)
    @transaction.atomic
    def _updateFeed(pk):
        """
        An internal function that fetches a feed and parses it into the 
        Feed object for the DB
        """
        feed = get_object_or_404(Feed, pk=pk)

        rawFeed, entries = feed._fetch_feed() 

        feed.title = rawFeed.get('title', None)
        feed.subtitle = rawFeed.get('subtitle', None)
        feed.copyright = rawFeed.get('rights', None)
        feed.link = rawFeed.get('link', None)
        feed.ttl = rawFeed.get('ttl', None)
        feed.atomLogo = rawFeed.get('logo', None)

        # Try to find the updated time
        updated = rawFeed.get(
            'updated_parsed',
            rawFeed.get('published_parsed', None),
        )

        if updated:
            updated = datetime.datetime.fromtimestamp(
                time.mktime(updated)
            )

        feed.pubdate = updated

        super(Feed, feed).save()

        # print(f'THE FEED: {feed}')

        if entries:
            # print(f'THE ENTRIES: {entries}')
            dbEntriesCreate = []
            dbEntriesupdate = []
            for raw_entry in entries:
                entry = Entry.objects.parseFromFeed(raw_entry)
                entry.feed = feed
                # newEntry, created = Entry.objects.get_or_create(feed_id=feed.id, guid=entry.guid)

                try:
                    newEntry = Entry.objects.get(guid=entry.guid)
                except:
                    newEntry = None

                
                if newEntry:
                    # if it was updated, then mark it as unread, otherwise no need to do anything
                    if newEntry.date > entry.date:
                        entry.state = ENTRY_UNREAD
                        id = newEntry.id
                        newEntry =  entry
                        newEntry.id = id
                        print(f'OLD ENTRY: {newEntry}')
                        dbEntriesupdate.append(newEntry)
                else:
                    dbEntriesCreate.append(entry)

            with transaction.atomic():
                if len(dbEntriesCreate)>0:
                    Entry.objects.bulk_create(dbEntriesCreate)
                if len(dbEntriesupdate)>0:
                    fields = ['feed', 'state', 'title' , 'content', 'date', 'author', 'url' ,'comments_url']
                    Entry.objects.bulk_update(dbEntriesupdate, fields)

        return

# Enrty #################################################   
class Entry(models.Model):
    """
    If creating from a feedparser entry, use Entry.objects.parseFromFeed()
    """

    feed = models.ForeignKey(Feed, related_name='feed', on_delete=models.CASCADE)
    
    state = models.IntegerField(default=ENTRY_UNREAD, choices=(
        (ENTRY_UNREAD,  'Unread'),
        (ENTRY_READ,    'Read'),
    ))

    # Compulsory data fields
    title = models.TextField(blank=True)
    content = models.TextField(blank=True)
    date = models.DateTimeField(
        help_text="When this entry says it was published",
    )
    
    # Optional data fields
    author = models.TextField(blank=True)
    url = models.TextField(
        blank=True,
        validators=[URLValidator()],
        help_text="URL for the HTML for this entry",
    )
    
    comments_url = models.TextField(
        blank=True,
        validators=[URLValidator()],
        help_text="URL for HTML comment submission page",
    )
    guid = models.TextField(
        blank=True,
        help_text="GUID for the entry, according to the feed",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.EntryManager()
    
    def __unicode__(self):
        return self.title
        
    def save(self, *args, **kwargs):
        # Default the date
        if self.date is None:
            self.date = datetime.datetime.now()
        
        # Save
        super(Entry, self).save(*args, **kwargs)
        
    class Meta:
        ordering = ('-updated_at',)
        verbose_name_plural = 'entries'
        unique_together = ['guid']


# Notification
class Notification(models.Model):
    '''
    Notifications for users regarding feed updates
    '''
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    
    state = models.IntegerField(default=ENTRY_UNREAD, choices=(
        (ENTRY_UNREAD,  'Unread'),
        (ENTRY_READ,    'Read'),
    ))

    title = models.CharField(max_length=200, null=True)
    message = models.CharField(max_length=200, null=True)
    is_error = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        verbose_name = ("Notification")
        verbose_name_plural = ("Notifications")
        ordering = ('-updated_at',)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return f'feed: {self.feed}, owner: {self.owner}'