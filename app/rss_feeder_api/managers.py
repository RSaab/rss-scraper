from django.db import models

import bleach
import datetime
import time

from django.utils import timezone

from rss_feeder import settings
from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ

class FeedManager(models.Manager):
    pass

class EntryManager(models.Manager):   
    def parseFromFeed(self, raw):
        """
        Create an Entry object from a raw feedparser entry
        
        Arguments:
            raw         The raw feed entry (aka item)
        
        Returns:
            entry       An Entry instance (not saved)
        """

        entry = self.model()
        
        entry.title = raw.get('title', '')
        content = raw.get('content', [{'value': ''}])[0]['value']
        if not content:
            content = raw.get('description', '')
        
        # Sanitise the content
        entry.content = bleach.clean(
            content,
            tags=settings.ALLOWED_TAGS,
            attributes=settings.ALLOWED_ATTRIBUTES,
            styles=settings.ALLOWED_STYLES,
            strip=True,
        )
        
        # Order: updated, published, created
        # If not provided, needs to be None for update comparison
        # Will default to current time when saved
        date = raw.get(
            'updated_parsed', raw.get(
                'published_parsed', raw.get(
                    'created_parsed', None
                )
            )
        )
        
        # TODO handle timezone warnings
        if date is not None:
            entry.date = datetime.datetime.fromtimestamp(
                time.mktime(date)
            )
        
        entry.url = raw.get('link', '')
        entry.guid = raw.get('guid', entry.url)
        
        entry.author = raw.get('author', '')
        entry.comments_url = raw.get('comments', '')

        entry.last_updated = timezone.now()
        
        return entry
        
    def get_query_set(self):
        """
        Return an EntryQuerySet
        """
        return EntryQuerySet(self.model)