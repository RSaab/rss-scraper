docker-compose -f docker-compose.prod.yml down -v
docker-compose up -d --build
docker-compose exec rss-scraper python manage.py migrate --noinput
