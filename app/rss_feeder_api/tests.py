from django.test import TestCase

from rss_feeder_api.models import Feed, Entry, FeedError, Notification
from django.shortcuts import get_object_or_404

from rest_framework import status


import pytest
import time
import uuid

# Create your tests here.
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.authtoken.models import Token

import dramatiq
import pytest
import json 

from dramatiq import Worker
from rss_feeder_api import broker

from rest_framework.test import APIClient


import logging
logging.basicConfig(level=logging.DEBUG)

########################
## Fixtures ############
########################

@pytest.fixture
def broker():
    broker = dramatiq.get_broker()
    broker.flush_all()
    return broker

@pytest.fixture
def worker(broker):
    worker = dramatiq.Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()

@pytest.fixture
def test_password():
   return 'strong-test-pass'
  
@pytest.fixture
def create_user(db, django_user_model, test_password):
   def make_user(**kwargs):
       kwargs['password'] = test_password
       if 'username' not in kwargs:
           kwargs['username'] = str(uuid.uuid4())
       return django_user_model.objects.create_user(**kwargs)
   return make_user

@pytest.fixture
def auto_login_user(db, client, create_user, test_password):
   def make_auto_login(user=None):
       if user is None:
           user = create_user()
       client.login(username=user.username, password=test_password)
       return client, user
   return make_auto_login

@pytest.fixture
def api_client():
   from rest_framework.test import APIClient
   return APIClient()

@pytest.fixture
def create_user_with_updated_feed(auto_login_user):
  def make__user_with_updated_feed():
    client, user = auto_login_user()
    feed = Feed.objects.create(link="https://www.nu.nl/rss/Algemeen", owner=user, nickname="test")
    feed._updateFeed(feed.id)
    return user, feed, client
  return make__user_with_updated_feed


########################
## API Tests ###########
########################


@pytest.mark.django_db(transaction=True)
def test_post_feed_twice(auto_login_user):
  client, user = auto_login_user()
  url = reverse('all-feeds-list')
  data = {
      "link": "https://www.nu.nl/rss/Algemeen",
      "nickname": "test2"
  }

  response = client.post(url, data, format='json')

  assert Feed.objects.count() == 1
  assert response.status_code == 201 , "not created"

  response = client.post(url, data, format='json')

  assert Feed.objects.count() == 1
  assert response.status_code == 400 , 'not bad request'

def test_unauthorized_request(api_client):
   url = reverse('all-feeds-list')
   response = api_client.get(url)
   assert response.status_code == 403, "all-feeds"

   url = reverse('all-users-list')
   response = api_client.get(url)
   assert response.status_code == 403, "all-users"

   url = reverse('all-notifications-list')
   response = api_client.get(url)
   assert response.status_code == 403, "all-notifications"


   url = reverse('all-entries-list')
   response = api_client.get(url)
   assert response.status_code == 403, "all-entries"


   url = reverse('feeds-detail-detail',  kwargs={'pk':1})
   response = api_client.get(url)
   assert response.status_code == 403, "feed-detail"

   url = reverse('user-detail', kwargs={'pk':1})
   response = api_client.get(url)
   assert response.status_code == 403, "user-detail"

   url = reverse('notification-detail-detail', kwargs={'pk':1})
   response = api_client.get(url)
   assert response.status_code == 403, "notification-detail"

   url = reverse('entry-detail-detail', kwargs={'pk':1})
   response = api_client.get(url)
   assert response.status_code == 403, "entry-detail"

@pytest.mark.django_db(transaction=True)
def test_auth_view(auto_login_user):
   client, user = auto_login_user()
   url = reverse('all-feeds-list')
   response = client.get(url)
   assert response.status_code == 200

@pytest.mark.django_db(transaction=True)
def test_post_feed(auto_login_user):
  client, user = auto_login_user()
  url = reverse('all-feeds-list')
  data = {
      "link": "https://www.nu.nl/rsss/Algemeen",
      "nickname": "test"
  }

  response = client.post(url, data, format='json')

  assert Feed.objects.count() == 1
  assert response.status_code == 201


@pytest.mark.django_db(transaction=True)
def test_post_and_update_feed(auto_login_user, broker, worker):
  client, user = auto_login_user()
  url = reverse('all-feeds-list')

  data = {
      "link": "https://feeds.feedburner.com/tweakers/mixed",
      "nickname": "test"
  }

  response = client.post(url, data, format='json')

  feed_id = response.data['id']
  assert Entry.objects.count() == 0

  response = client.get(url)
  assert response.data['count'] == 1
  name = 'test2'
  data = {
      "nickname": name
  }

  content_type = 'application/json'
  response = client.patch(f'/api/v1/feed/{feed_id}/?force_update=true', data, content_type=content_type)


  assert response.status_code == status.HTTP_200_OK
  assert response.data['nickname'] == name 

  broker.join("default")
  worker.join()

  assert Entry.objects.count() > 0 
  

@pytest.mark.django_db(transaction=True)
def test_get_feed(auto_login_user):
  client, user = auto_login_user()
  url = reverse('all-feeds-list')

  data = {
      "link": "https://www.nu.nl/rsss/Algemeen",
      "nickname": "test"
  }

  response = client.post(url, data, format='json')

  response = client.get(url)
  assert response.data['count'] == 1


@pytest.mark.django_db(transaction=True)
def test_get_read_unread_entries(create_user_with_updated_feed):
  user, feed, client = create_user_with_updated_feed()
  url = reverse('all-entries-list')
  response = client.get(url+"?read=true")
  assert response.data['count'] == 0, "read entries exist, they shldnt"

  response = client.get(url+"?read=false")
  assert response.data['count'] > 0, "entries arent unread"

  response = client.get(url+"?feed_id=2456532&read=false")
  assert response.data['count'] == 0, "unread entries not filtered by feed id"

  response = client.get(url+"?feed_id=24213211&read=true")
  assert response.data['count'] == 0, "read entries not filtered by feed id"

  response = client.get(url+f'?feed_id={feed.id}&read=true')
  assert response.data['count'] == 0, "entries filtered by correct feed id but not by read status"
  
  response = client.get(url+f'?feed_id={feed.id}&read=false')
  assert response.data['count'] > 0, "entries filtered by correct feed id but not by unread status"


@pytest.mark.django_db(transaction=True)
def test_patch_entry_state(create_user_with_updated_feed):
  user, feed, client = create_user_with_updated_feed()
  url = reverse('all-entries-list')
  response = client.get(url+"?read=false")
  assert response.data['count'] > 0, "read entries exist, they shldnt"

  url_detail = reverse('entry-detail-detail', kwargs={'pk':response.data['results'][0]['id']})
  response = client.patch(url_detail+f'?read=true')

  response = client.get(url_detail)
  assert response.data['state']==1, "state not read"

  response = client.get(url+"?read=true")
  print(response.data)
  assert response.data['count'] == 1, "entry not patched "

@pytest.mark.django_db(transaction=True)
def test_patch_feed_follow(create_user_with_updated_feed):
  user, feed, client = create_user_with_updated_feed()
  url = reverse('all-feeds-list')
  response = client.get(url+"?follow=false")
  assert response.data['count'] > 0, "unfollowed feeds exist, they shldnt"

  url_detail = reverse('feeds-detail-detail', kwargs={'pk':response.data['results'][0]['id']})
  response = client.patch(url_detail+f'?follow=false')

  response = client.get(url_detail)
  assert response.data['following']==0, "feed not unfollowed"

  response = client.get(url+"?follow=false")
  print(response.data)
  assert response.data['count'] == 1, "no unfollowed feeds "
  
########################
## Unit Tests ##########
########################

@pytest.mark.django_db(transaction=True)
def test_user_create():
    User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_register_feed(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user, nickname="test")
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://www.nu.nl/rss/Algemeen", owner=user, nickname="test")

    feed.force_update()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0


@pytest.mark.django_db(transaction=True)
def test_2_users_same_feed_same_nickname(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    user2 = User.objects.create_user('john2', 'lennon2@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 2

    feed = Feed.objects.create(link="https://www.nu.nl/rss/Algemeen", owner=user, nickname="test")
    feed2 = Feed.objects.create(link="https://www.nu.nl/rss/Algemeen", owner=user2, nickname="test")

    feed._updateFeed(feed.id)    

    count1 = Entry.objects.count()

    feed2._updateFeed(feed2.id)
    
    assert Feed.objects.count() == 2

    assert Entry.objects.count() > count1, "new count not greater than after second update"
    assert Entry.objects.filter(feed=feed).count() + Entry.objects.filter(feed=feed2).count() == Entry.objects.count(), "sum not equal to total" 
    assert Entry.objects.filter(feed=feed).count() == Entry.objects.filter(feed=feed2).count(), "non equal entries for feeds"
    assert Entry.objects.filter(feed=feed).count() < Entry.objects.count(), "feed 1 entries less than total"
    assert Entry.objects.filter(feed=feed2).count() < Entry.objects.count(), "feed 2 entries less than total"

@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_with_redirect(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="http://www.nu.nl/rss/Algemeen", owner=user, nickname="test")

    feed.force_update()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0


@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_2(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user, nickname="test")

    feed.force_update()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0

@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_twice(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user, nickname="test")

    feed.force_update()
    feed.force_update()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    # this is not very good cuz the feed might have more than 40 at some point
    # need a better way to check for double entries
    assert Entry.objects.count() < 50


@pytest.mark.django_db(transaction=True)
@pytest.mark.xfail(raises=FeedError)
def test_register_and_update_invalid_feed(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/WootWoot/mixed", owner=user, nickname="test")

    feed.force_update()

    broker.join("default")
    worker.join()

    time.sleep(2)
    print("updating again")
    feed.force_update()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0

@pytest.mark.django_db(transaction=True)
def test_backoff(broker, worker):
    print()
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://www.nu.nl/rss/AAAAAlgemeen", owner=user, nickname="test")

    try:
      feed._fetch_feed()
    except:
      pass
    
    assert Notification.objects.count() == 2, f'notification count error  {Notification.objects.count()}'
    notification = Notification.objects.all()
    assert notification[0].title == "BackOff" 
    assert notification[1].title == "BackOff" 
    
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0

@pytest.mark.django_db(transaction=True)
def test_async_fetch_with_failed_notification(broker, worker):
    print()
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://www.nu.nl/rss/AAAAAlgemeen", owner=user, nickname="test")

    feed.force_update()
    
    broker.join("default")
    worker.join()

    # only one notification per attempts of the same call
    assert Notification.objects.count() == 1, f'notification count error  {Notification.objects.count()}'
    notification = Notification.objects.get()
    assert notification.title == "FeedError" 
    
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0

@pytest.mark.django_db(transaction=True)
def test_async_fetch_with_failed_notification_and_retry_with_success(broker, worker):
    print()
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://www.nu.nl/rss/AAAAAlgemeen", owner=user, nickname="test")

    feed.force_update()
    
    broker.join("default")
    worker.join()

    # only one notification per attempts of the same call
    assert Notification.objects.count() == 1, f'notification count error  {Notification.objects.count()}'
    notification = Notification.objects.get()
    assert notification.title == "FeedError" 
    
    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0

    # retry
    feed.link = "https://www.nu.nl/rss/Algemeen"

    feed.save()
    
    feed.force_update()
    
    broker.join("default")
    worker.join()

    count = Notification.objects.count()
    assert  count == 2, f'notification count {count}'
    notification = Notification.objects.all()
    assert notification[0].title == "FeedUpdated" 