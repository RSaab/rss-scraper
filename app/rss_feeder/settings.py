"""
Django settings for rss_feeder project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

import os

from django.conf import settings

import bleach

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# number of retries when trying to fetch a feed for update
MAX_FEED_UPDATE_RETRIES = 3

SWAGGER_SETTINGS = {
    'PERSIST_AUTH': True,
    # 'REFETCH_SCHEMA_WITH_AUTH': True,
    'REFETCH_SCHEMA_ON_LOGOUT': True,

    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        }
    }
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'w^gc9@^i19$8yrjj6@dc96m-s+s)a@jt%8-@qn6*0$1!lib9ql'
SECRET_KEY = os.environ.get("SECRET_KEY", "NOTSOSECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get("DEBUG", default=1))

# ALLOWED_HOSTS = []
# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost 127.0.0.1").split(" ")

# Application definition

INSTALLED_APPS = [
    'drf_yasg',
    'django_dramatiq',
    'rss_feeder_api.apps.RssFeederApiConfig',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rss_feeder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rss_feeder.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'


#
# Bleach settings for rss_feeder_api
#

# HTML whitelist for bleach
# This default list is roughly the same as the WHATWG sanitization rules
# <http://wiki.whatwg.org/wiki/Sanitization_rules>, but without form elements.
# A few common HTML 5 elements have been added as well.
ALLOWED_TAGS = getattr(
    settings, 'RSS_FEEDER_ALLOWED_TAGS',
    [
        'a',
        'abbr',
        'acronym',
        'aside',
        'b',
        'bdi',
        'bdo',
        'blockquote',
        'br',
        'code',
        'data',
        'dd',
        'del',
        'dfn',
        'div',  # Why not?
        'dl',
        'dt',
        'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'hr',
        'i',
        'img',
        'ins',
        'kbd',
        'li',
        'ol',
        'p',
        'pre',
        'q',
        's',
        'samp',
        'small',  # Now a semantic tag in HTML5!
        'span',
        'strike',
        'strong',
        'sub', 'sup',
        'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr',
        'time',
        'tt',  # Obsolete, but docutils likes to generate these.
        'u',
        'var',
        'wbr',
        'ul',
    ]
)

ALLOWED_ATTRIBUTES = getattr(
    settings, 'RSS_FEEDER_ALLOWED_ATTRIBUTES',
    {
        '*':        ['lang', 'dir'],  # lang is necessary for hyphentation.
        'a':        ['href', 'title'],
        'abbr':     ['title'],
        'acronym':  ['title'],
        'data':     ['value'],
        'dfn':      ['title'],
        'img':      ['src', 'alt', 'width', 'height', 'title'],
        'li':       ['value'],
        'ol':       ['reversed', 'start', 'type'],
        'td':       ['align', 'valign', 'width', 'colspan', 'rowspan'],
        'th':       ['align', 'valign', 'width', 'colspan', 'rowspan'],
        'time':     ['datetime'],
    }
)

ALLOWED_STYLES = getattr(
    settings, 'RSS_FEEDER_ALLOWED_STYLES', bleach.ALLOWED_STYLES,
)



DRAMATIQ_BROKER = {
    "BROKER": os.environ.get("DRAMATIQ_BROKER", "dramatiq.brokers.stub.StubBroker"),
    # "OPTIONS": {
    #     "url": os.environ.get("DRAMATIQ_BROKER_URL", "amqp://localhost:5672"),
    # },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

if not DRAMATIQ_BROKER['BROKER'] == 'dramatiq.brokers.stub.StubBroker':
    DRAMATIQ_BROKER['OPTIONS'] = {"url": os.environ.get("DRAMATIQ_BROKER_URL", "amqp://localhost:5672")}

BROKER_URL = os.environ.get("DRAMATIQ_BROKER_URL", "amqp://localhost:5672")
CELERY_RESULT_BACKEND = os.environ.get("DRAMATIQ_BROKER_URL", "amqp://localhost:5672")


# Defines which database should be used to persist Task objects when the
# AdminMiddleware is enabled.  The default value is "default".
DRAMATIQ_TASKS_DATABASE = "default"

APPEND_SLASH=False