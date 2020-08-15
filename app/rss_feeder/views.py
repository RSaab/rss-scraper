from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, Sendcloud. You're at the RSS Scraper test index.")
