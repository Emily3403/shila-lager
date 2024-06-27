from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.inventory_counts_parser import import_lager_counts


class Command(BaseCommand):
    help = 'Import Lagerzählungen'

    def handle(self, *args: Any, **options: Any) -> None:
        import_lager_counts()
