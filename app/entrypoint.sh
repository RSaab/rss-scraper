#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# python manage.py flush --no-input
# python manage.py migrate
python manage.py rundramatiq --reload &

sleep 1

celery -A rss_feeder_api beat &

sleep 1

celery -A rss_feeder_api worker &

sleep 1

exec "$@"
