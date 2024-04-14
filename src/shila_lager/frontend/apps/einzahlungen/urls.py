from django.urls import path

from shila_lager.frontend.apps.einzahlungen import views

urlpatterns = [
    path("", views.index, name="einzahlungen_index"),
]
