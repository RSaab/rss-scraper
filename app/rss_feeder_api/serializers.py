from rest_framework import serializers
from rss_feeder_api.models import Feed, Entry, Notification

from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    feeds = serializers.PrimaryKeyRelatedField(many=True, queryset=Feed.objects.all())

    class Meta:
        model = User
        fields = '__all__'

class FeedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Feed
        fields = '__all__'
        ordering = ['-created_at']

class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = '__all__'
        ordering = ['-date']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        ordering = ['-created_at']
