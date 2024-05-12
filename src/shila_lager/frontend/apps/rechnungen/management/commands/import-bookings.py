from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.sparkasse_csv_parser import import_bookings


class Command(BaseCommand):
    help = 'Import sale prices'

    def handle(self, *args: Any, **options: Any) -> None:
        import_bookings()
