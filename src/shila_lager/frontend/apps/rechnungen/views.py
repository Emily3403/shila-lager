from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest, **kwargs: str) -> HttpResponse:
    return HttpResponse("Hello, world. You're at the rechnungen index.")
