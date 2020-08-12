from rest_framework import serializers
from rss_feeder_api.models import Feed

from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    feeds = serializers.PrimaryKeyRelatedField(many=True, queryset=Feed.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'feeds']


class FeedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Feed
        fields = ['id', 'title', 'link', 'following', 'description', 
        'language', 'copyright', 'ttl', 'atomLogo', 'lastbuilddate', 
        'pubdate', 'nickname', 'created_at', 'updated_at', 'following',
        'owner'] 
        ordering = ['created_at']