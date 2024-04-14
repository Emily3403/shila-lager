from django.urls import path

from shila_lager.frontend.apps.stats import views

urlpatterns = [
    path("", views.index, name="stats_index"),
]
