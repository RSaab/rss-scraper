from rss_feeder_api.models import Feed, Entry, Notification
from rss_feeder_api.serializers import FeedSerializer, UserSerializer, EntrySerializer, NotificationSerializer
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework import permissions, status
from rest_framework.response import Response

from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ, ENTRY_SAVED

from django.shortcuts import get_object_or_404


from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema

from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from inflection import camelize
from rest_framework.parsers import FileUploadParser, FormParser


# from django.views import View

from rest_framework import viewsets

from rest_framework import mixins

# Users
class UserList(generics.ListAPIView):
    """
    get:
        View all users
    """
    allowed_methods = ('GET')

    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter()
    serializer_class = UserSerializer


class UserDetail(generics.ListAPIView):
    """
    get:
        view a single user by id
    """
    allowed_methods = ('GET')

    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Entries
class EntryList(generics.ListAPIView):
    """
    get:
        View all entries.

        parameters:
            - name: feed_id
              in: path
              type: integer
              description: filter based on feed id
              required: false
            - name: read
              in: path
              type: boolean
              description: filter based on read status
              required: false
    """
    allowed_methods = ('GET')
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

class EntryDetail(generics.RetrieveUpdateAPIView):
    """
    Entry Details
    
    get:
        View a single entry
    
    patch:
        patch an entry with read/unread

        parameters:
            - name: read
              in: path
              type: boolean
              description: the desired read status of the entry (true/false)
              required: false
    """
    allowed_methods = ('PATCH')
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Entry.objects.filter(feed__owner=self.request.user)

    def patch(self, request, *args, **kwargs):
        read = self.request.GET.get('read', None)
        
        entry = self.get_object()

        if read:
            if read == 'true' or read=='True':
                entry.state = ENTRY_READ
            else:
                entry.state = ENTRY_UNREAD

        entry.save()
        return Response(EntrySerializer(entry).data)

    queryset = Entry.objects.all()
    serializer_class = EntrySerializer

# Feeds
class FeedList(generics.ListCreateAPIView):
    """
    Feed API

    get:
        View all feeds

    post:
        Create a new feed item. The feed is not updated until the next async update job is run or a separate force update is called
    """
    permission_classes = [permissions.IsAuthenticated]
    allowed_methods = ('GET','POST')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return Feed.objects.filter(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


class FeedDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Feed Detail API

    get:
        View a single feed item

    put:
        Update a feed item in the database, you can modify any field except the created_at
        and modified_at fields. The nickname and link are required

    patch:
        This endpoint allows the update of a feed's follow status

        Query Parameters:
            - name: follow
              in: path
              type: boolean
              description: Describes whether a user wantes to follow the feed or not (true/false)
              required: false
            - name: force_update
              in: path
              type: boolean
              description: If set to true, will force an async update on the feed, default is false (true/false)
              required: false
    delete:
        Delete a feed entry. This action will also delete all referencing entries and notifications
    """
    allowed_methods = ('GET','PUT', 'PATCH', "DELETE")
    
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Feed.objects.filter(owner=self.request.user)

    def put(self, request, *args, **kwargs):
        feed = self.get_object()
        serializer = FeedSerializer(feed, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        force_update = self.request.GET.get('force_update', None)
        follow = self.request.GET.get('follow', None)
        
        feed = self.get_object()


        if follow:
            if follow == 'true' or follow=='True':
                feed.following = True
            else:
                feed.following = False

        feed.save()

        if force_update == 'true' or force_update=='True':
            feed.force_pdate()

        return Response(FeedSerializer(feed).data)

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


# Notifications
class NotificationList(generics.ListAPIView):
    """
    get:
        View all notifications
    """
    allowed_methods = ('GET')
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(owner=self.request.user)

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class NotificationUpdateState(generics.RetrieveUpdateAPIView):
    """
    Notification Details
    
    get:
        View a single entry
    
    patch:
        patch an notification with read/unread

        parameters:
            - name: read
              in: path
              type: boolean
              description: the desired read status of the entry (true/false)
              required: false
    """
    allowed_methods = ('GET','PATCH')

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        return Notification.objects.filter(owner=self.request.user)
        
    def patch(self, request, *args, **kwargs):     
        read = self.request.GET.get('read', None)
        
        notification =  self.get_object()

        if read:
            if read == 'true' or read=='True':
                notification.state = ENTRY_READ
            else:
                notification.state = ENTRY_UNREAD

        notification.save()
        return Response(NotificationSerializer(notification).data)

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer