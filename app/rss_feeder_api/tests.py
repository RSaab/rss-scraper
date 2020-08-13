from django.test import TestCase

from rss_feeder_api.models import Feed, Entry


import pytest

# Create your tests here.
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_user_create():
    User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

@pytest.mark.django_db
def test_feed():
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user)
    
    assert feed.title
    print(feed.title)
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 40

@pytest.mark.django_db
def test_feed_2():
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://www.nu.nl/rss/Algemeen", owner=user)
    
    assert feed.title
    print(feed.title)
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 10
