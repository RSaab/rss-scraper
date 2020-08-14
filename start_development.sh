docker-compose up -d --build
docker-compose exec rss-scraper python manage.py migrate --noinput
