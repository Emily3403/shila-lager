from django.urls import path
from django.views.generic import RedirectView

from shila_lager.frontend.apps.bestellung import views

urlpatterns = [
    path("", RedirectView.as_view(url="grihed/"), name="bestellungen_index"),
    path("grihed/", views.grihed_order, name="grihed_orders"),
    path("bringmeister/", views.bringmeister_order, name="bringmeister_orders"),
    path("gepa/", views.gepa_order, name="gepa_orders"),
    path("hygienelager/", views.hygienelager_order, name="hygienelager_orders"),
]
