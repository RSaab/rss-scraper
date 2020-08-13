from rss_feeder_api.models import Feed, Entry
from rss_feeder_api.serializers import FeedSerializer, UserSerializer, EntrySerializer
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework import permissions
from rest_framework.response import Response
from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ, ENTRY_SAVED


# Users
class UserList(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Entries
class EntryList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        feed_id = self.request.GET.get('feed_id', None)
        read = self.request.GET.get('read', None)

        filter_kwargs ={"feed__owner": self.request.user}
        if feed_id:
            print("filtering feed_id")
            filter_kwargs['feed__id'] = feed_id
        
        if read:
            if read == 'true' or read=='True':
                filter_kwargs['state'] = ENTRY_READ
            else:
                filter_kwargs['state'] = ENTRY_UNREAD

        return Entry.objects.filter(**filter_kwargs)
        

    queryset = Entry.objects.all()
    serializer_class = EntrySerializer


class EntryDetail(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Entry.objects.filter(feed__owner=self.request.user)

    def put(self, request, *args, **kwargs):
        read = self.request.GET.get('read', None)
        
        feed = self.get_object()

        if read:
            if read == 'true' or read=='True':
                feed.state = ENTRY_READ
            else:
                feed.state = ENTRY_UNREAD

        serializer = FeedSerializer(Entry, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
       return self.put(self, request, args, kwargs)

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer

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

    def put(self, request, *args, **kwargs):
        force_update = self.request.GET.get('force_update', None)
        follow = self.request.GET.get('follow', None)
        
        feed = self.get_object()

        if force_update == 'true' or force_update=='True':
            feed.force_pdate()

        if follow:
            if follow == 'true' or follow=='True':
                feed.following = True
            else:
                feed.following = False

        serializer = FeedSerializer(feed, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
       return self.put(self, request, args, kwargs)

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer