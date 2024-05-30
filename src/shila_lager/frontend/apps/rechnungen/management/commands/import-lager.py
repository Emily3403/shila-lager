from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.lager_parser import import_lager


class Command(BaseCommand):
    help = 'Import Lagerzählungen'

    def handle(self, *args: Any, **options: Any) -> None:
        import_lager()
