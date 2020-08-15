from django.test import TestCase

from rss_feeder_api.models import Feed, Entry, FeedError
from django.shortcuts import get_object_or_404


import pytest
import time
import uuid

# Create your tests here.
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.authtoken.models import Token

import dramatiq
import pytest

from dramatiq import Worker
from rss_feeder_api import broker

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


@pytest.mark.django_db
def test_unauthorized_request(api_client):
   url = reverse('all-feeds')
   response = api_client.get(url)
   assert response.status_code == 403

@pytest.mark.django_db
def test_auth_view(auto_login_user):
   client, user = auto_login_user()
   url = reverse('all-feeds')
   response = client.get(url)
   print(response)
   assert response.status_code == 200

@pytest.mark.django_db
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

    feed.force_pdate()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0

@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_with_redirect(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="http://www.nu.nl/rss/Algemeen", owner=user, nickname="test")

    feed.force_pdate()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0


@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_2(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user, nickname="test")

    feed.force_pdate()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0

@pytest.mark.django_db(transaction=True)
def test_register_and_update_feed_twice(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/tweakers/mixed", owner=user, nickname="test")

    feed.force_pdate()
    feed.force_pdate()

    broker.join("default")
    worker.join()

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.xfail(raises=FeedError)
def test_register_and_update_invalid_feed(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/WootWoot/mixed", owner=user, nickname="test")

    feed.force_pdate()

    broker.join("default")
    worker.join()

    time.sleep(2)
    print("updating again")
    feed.force_pdate()

    broker.join("default")
    worker.join()


    assert Feed.objects.count() == 1
    assert Entry.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.xfail(raises=FeedError)
def test_register_and_update_invalid_feed_with_retry(broker, worker):
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    assert User.objects.count() == 1

    feed = Feed.objects.create(link="https://feeds.feedburner.com/WootWoot/mixed", owner=user, nickname="test")

    try:
      feed._updateFeed(feed.id)
    except:
      print("exception caught, user should be notified")
      feed.link = "https://feeds.feedburner.com/tweakers/mixed"
      feed.save()
      feed._updateFeed(feed.id)

    assert Feed.objects.count() == 1
    assert Entry.objects.count() > 0
