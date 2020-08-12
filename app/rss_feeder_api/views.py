from rss_feeder_api.models import Feed
from rss_feeder_api.serializers import FeedSerializer, UserSerializer
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework import permissions



# Users
class UserList(generics.ListAPIView):
    queryset = User.objects.filter()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Feeds
class FeedList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return Feed.objects.filter(owner=self.request.user)

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


class FeedDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Feed.objects.filter(owner=self.request.user)

    queryset = Feed.objects.all()

    serializer_class = FeedSerializer