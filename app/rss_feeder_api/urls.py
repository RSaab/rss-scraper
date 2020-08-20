from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rss_feeder_api import views

from rest_framework import routers

router = routers.DefaultRouter()


router.register('feed', views.FeedList, basename='all-feeds')
router.register('feed', views.FeedDetail, basename='feeds-detail')
router.register('entry', views.EntryList, basename='all-entries')
router.register('entry', views.EntryDetail, basename='entry-detail')
router.register('user', views.UserList, basename='all-users')
router.register('user', views.UserDetail, basename='user')
router.register('notification', views.NotificationList, basename='all-notifications')
router.register('notification', views.NotificationUpdateState, basename='notification-detail')

urlpatterns = [
     path('', include((router.urls))),
]
