from django.contrib import admin

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, CrateInventory

admin.site.register(BeverageCrate)
admin.site.register(CrateInventory)

