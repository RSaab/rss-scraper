from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rss_feeder_api import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('feed/', views.FeedList.as_view(), name='all-feeds'),
    path('feed/<int:pk>/', views.FeedDetail.as_view(), name='feed-detail'),

    path('user/', views.UserList.as_view(), name="all-users"),
	path('user/<int:pk>/', views.UserDetail.as_view(), name="user-detail"),

    path('entry/', views.EntryList.as_view(), name="all-entries"),
	path('entry/<int:pk>/', views.EntryDetail.as_view(), name="entry-detail"),

	path('notification/', views.NotificationList.as_view(), name="all-notifications"),
	path('notification/<int:pk>/', views.NotificationUpdateState.as_view(), name="notification-detail"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
