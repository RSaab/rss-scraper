from django.db import models

import datetime
import time


from django.utils.encoding import smart_text as smart_unicode
from django.utils.translation import ugettext_lazy as _

from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ, ENTRY_SAVED

from rss_feeder_api import managers

from django.core.validators import URLValidator
import feedparser

import json
    
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

class InactiveFeedError(FeedError):
    pass
    
class EntryError(Exception):
    """
    An error occurred when processing an entry
    """
    pass
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
    lastbuilddate = models.DateTimeField(null=True)
    pubdate = models.DateTimeField(null=True)
    nickname = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    following = models.BooleanField(default=True)

    owner = models.ForeignKey('auth.User', related_name='feeds', on_delete=models.CASCADE)

    class Meta: 
        verbose_name = ("Feed")
        verbose_name_plural = ("Feeds")
        ordering = ('-pubdate',)
        unique_together = ('link', 'owner')

    
    objects = managers.FeedManager()


    def __str__(self):
        return f'Nickname: {self.nickname}'

    def save(self, *args, **kwargs):
        feed, entries = self.fetchFeed()
        super(Feed, self).save(*args, **kwargs)

        if entries:
            for raw_entry in entries:
                entry = Entry.objects.parseFromFeed(raw_entry)
                entry.feed = self
                entry.save()

        return

    def force_pdate(self, *args, **kwargs):
        print("Forcing update...")
        raise NotImplementedError

    def _fetch_feed(self):
        '''
        internal method to get feed details
        '''
        # Request and parse the feed
        d = feedparser.parse(self.link)
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

        if status == 410:
            raise InactiveFeedError('Feed has gone')

        # Unknown status
        raise FeedError('Unrecognised HTTP status %s' % status)

    def fetchFeed(self, *args, **kwargs):
        
        # make sure link exists
        assert self.link
        
        feed, entries = self._fetch_feed()
        
        self.title = feed.get('title', None)
        self.subtitle = feed.get('subtitle', None)
        self.copyright = feed.get('rights', None)
        self.link = feed.get('link', None)
        self.ttl = feed.get('ttl', None)
        self.atomLogo = feed.get('logo', None)


        # Try to find the updated time
        updated = feed.get(
            'updated_parsed',
            feed.get('published_parsed', None),
        )

        if updated:
            updated = datetime.datetime.fromtimestamp(
                time.mktime(updated)
            )

        self.pubdate = updated
        return feed, entries

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

    expires = models.DateTimeField(
        blank=True, null=True, help_text="When the entry should expire",
    )
    
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
        ordering = ('-date',)
        verbose_name_plural = 'entries'