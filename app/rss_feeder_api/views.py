from rss_feeder_api.models import Feed, Entry, Notification
from rss_feeder_api.serializers import FeedSerializer, UserSerializer, EntrySerializer, NotificationSerializer
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework import permissions, status
from rest_framework.response import Response

from rss_feeder_api.constants import ENTRY_UNREAD, ENTRY_READ


from django.shortcuts import get_object_or_404

from django.utils.decorators import method_decorator

from rest_framework import viewsets

from rest_framework import mixins
from rest_framework.decorators import action

####################################################
####################################################

class UserList(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter()
    serializer_class = UserSerializer

class UserDetail(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    
    def get_queryset(self):
        return Feed.objects.filter(id=self.request.user)

    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

####################################################
####################################################

class EntryList(mixins.ListModelMixin,viewsets.GenericViewSet):
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

class EntryDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Entry.objects.filter(feed__owner=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response("method not allowed", status=status.HTTP_401_UNAUTHORIZED)

    def partial_update(self, request, *args, **kwargs):
        read = self.request.GET.get('read', None)
        
        entry = self.get_object()

        if read:
            if read == 'true' or read=='True':
                entry.state = ENTRY_READ
            else:
                entry.state = ENTRY_UNREAD

        try:
            entry.save()
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(EntrySerializer(entry).data)

    queryset = Entry.objects.all()
    serializer_class = EntrySerializer

####################################################
####################################################

class FeedList(mixins.CreateModelMixin,mixins.ListModelMixin,viewsets.GenericViewSet):
    """
    Feed API
    get:
        View all feeds
    post:
        Create a new feed item. The feed is not updated until the next async update job is run or a separate force update is called
    """
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = FeedSerializer(data=request.data)

        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        following = self.request.GET.get('following', None)

        filter_kwargs ={"owner": self.request.user}
 
        if following:
            if following == 'true' or following=='True':
                filter_kwargs['following'] = True
            else:
                filter_kwargs['following'] = False

        return Feed.objects.filter(**filter_kwargs)

class FeedDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
        Feed Detail API
        
        get:
            View a single feed item
        patch:
            This endpoint allows the update of a feed's follow status

            Parameters:
                - name: follow
                  in: query
                  type: boolean
                  description: Describes whether a user wantes to follow the feed or not (true/false)
                  required: false
                - name: force_update
                  in: query
                  type: boolean
                  description: If set to true, will force an async update on the feed, default is false (true/false)
                  required: false
        delete:
            Delete a feed entry. This action will also delete all referencing entries and notifications
            parameter: force
    """
    permission_classes = [permissions.IsAuthenticated]

    queryset = Feed.objects.all()
    serializer_class = FeedSerializer

    def get_queryset(self):
        return Feed.objects.filter(owner=self.request.user)
    

    def update(self, request, pk=None):
        """
        Feed Put 
        """
        # feed = self.get_object()
        serializer = FeedSerializer(feed, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        force_update = self.request.GET.get('force_update', None)
        follow = self.request.GET.get('follow', None)
        

        feed = self.get_object()
        
        link = request.data.get('link', None)
        nickname = request.data.get('nickname', None)
        if link:
            feed.link = link

        if nickname:
            feed.nickname = nickname

        if follow:
            if follow == 'true' or follow=='True':
                feed.following = True
            else:
                feed.following = False


        try:
            feed.save()
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        if force_update == 'true' or force_update=='True':
            feed.force_update()

        return Response(FeedSerializer(feed).data)

####################################################
####################################################

class NotificationList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    get:
        View all notifications
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        read = self.request.GET.get('read', None)

        filter_kwargs ={"feed__owner": self.request.user}
        
        if read:
            if read == 'true' or read=='True':
                filter_kwargs['state'] = ENTRY_READ
            else:
                filter_kwargs['state'] = ENTRY_UNREAD

        return Notification.objects.filter(**filter_kwargs)

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class NotificationUpdateState(viewsets.ModelViewSet):
    """
    Notification Details
    
    get:
        View a single notification
    
    patch:
        patch an notification with read/unread

        parameters:
            - name: read
              in: path
              type: boolean
              description: the desired read status of the notification (true/false)
              required: false
    """

    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        return Response("method not allowed", status=status.HTTP_401_UNAUTHORIZED)

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

        try:
            notification.save()
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(NotificationSerializer(notification).data)

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

####################################################
####################################################
