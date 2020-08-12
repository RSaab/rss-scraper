from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rss_feeder_api import views
from rest_framework import routers

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('feeds/', views.FeedList.as_view()),
    path('feeds/<int:pk>/', views.FeedDetail.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)
