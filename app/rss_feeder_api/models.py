from django.db import models


from django.utils.encoding import smart_text as smart_unicode
from django.utils.translation import ugettext_lazy as _

from django.core.validators import URLValidator
import feedparser
    
# Exceptions #################################################   

class FeedError(Exception):
    """
    An error occurred when fetching the feed
    
    If it was parsed despite the error, the feed and entries will be available:
        e.feed      None if not parsed
        e.entries   Empty list if not parsed
    """
    def __init__(self, *args, **kwargs):
        self.feed = kwargs.pop('feed', None)
        self.entries = kwargs.pop('entries', [])
        super(FeedError, self).__init__(*args, **kwargs)

class InactiveFeedError(FeedError):
    pass
    
class EntryError(Exception):
    """
    An error occurred when processing an entry
    """
    pass

# End: Exceptions #################################################   


class Feed(models.Model):
    '''
    The feeds model describes a registered field. 
    Its contains feed related information
    as well as user related info and other meta data
    '''
    link = models.URLField(max_length = 200)
    title = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)
    language = models.CharField(max_length=5, null=True)
    copyright = models.CharField(max_length=50, null=True)
    ttl = models.PositiveIntegerField(null=True)
    atomLogo = models.URLField(max_length = 200, null=True)
    lastbuilddate = models.DateField(null=True)
    pubdate = models.DateField(null=True)
    nickname = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    following = models.BooleanField(default=True)

    class Meta: 
        verbose_name = ("Feed")
        verbose_name_plural = ("Feeds")
        

    def __str__(self):
        return f'Nickname: {self.nickname}'


    def save(self, *args, **kwargs):
        """
        Use the `pygments` library to create a highlighted HTML
        representation of the code snippet.
        """
        self.register()
        super(Feed, self).save(*args, **kwargs)

    def _fetch_feed(self, url_history=None):
        '''
        internal method to get feed details
        '''
        # Request and parse the feed
        d = feedparser.parse(self.link)
        status  = d.get('status', 200)
        feed    = d.get('feed', None)

        if status in (200, 302, 304, 307):
            if (
                feed is None
                or 'title' not in feed
                or 'link' not in feed
            ):
                raise FeedError('Feed parsed but with invalid contents')
            
            return feed

        if status in (404, 500, 502, 503, 504):
            raise FeedError('Temporary error %s' % status)

        if status == 410:
            raise InactiveFeedError('Feed has gone')

        # Unknown status
        raise FeedError('Unrecognised HTTP status %s' % status)

    # def registerFeed(self, nickname, link, user):
    def register(self):
        print(f'registered {self.nickname} - {self.link}')
        return
