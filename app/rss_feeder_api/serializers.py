from rest_framework import serializers
from rss_feeder_api.models import Feed

class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ['id', 'title', 'link', 'following', 'description', 
        'language', 'copyright', 'ttl', 'atomLogo', 'lastbuilddate', 
        'pubdate', 'nickname', 'created_at', 'updated_at', 'following'] 
        ordering = ['created_at']