from django.db.models import QuerySet
from django.http import HttpResponse, HttpRequest
from django.template import loader

from shila_lager.frontend.apps.bestellung.models import BeverageCrate


def grihed_order(request: HttpRequest, **kwargs: str) -> HttpResponse:
    beverages: QuerySet[BeverageCrate] = BeverageCrate.objects.all()

    template = loader.get_template("bestellung/grihed.html")
    context = {
        "beverages": beverages,
    }

    return HttpResponse(template.render(context, request))


def bringmeister_order(request: HttpRequest, **kwargs: str) -> HttpResponse:
    beverages = BeverageCrate.objects.all()

    template = loader.get_template("bestellung/grihed.html")
    context = {
        "beverages": beverages
    }

    return HttpResponse(template.render(context, request))


def gepa_order(request: HttpRequest, **kwargs: str) -> HttpResponse:
    beverages = BeverageCrate.objects.all()

    template = loader.get_template("bestellung/grihed.html")
    context = {
        "beverages": beverages
    }

    return HttpResponse(template.render(context, request))


def hygienelager_order(request: HttpRequest, **kwargs: str) -> HttpResponse:
    beverages = BeverageCrate.objects.all()

    template = loader.get_template("bestellung/grihed.html")
    context = {
        "beverages": beverages
    }

    return HttpResponse(template.render(context, request))
