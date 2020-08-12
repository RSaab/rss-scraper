from rss_feeder_api.models import Feed
from rss_feeder_api.serializers import FeedSerializer
from rest_framework import generics

# Feeds
class FeedList(generics.ListCreateAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


class FeedDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer