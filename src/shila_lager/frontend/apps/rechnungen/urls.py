from django.urls import path

from shila_lager.frontend.apps.rechnungen import views

urlpatterns = [
    path("", views.index, name="rechnungen_index"),
]
