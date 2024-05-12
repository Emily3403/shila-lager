from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.mv_abrechnung import mv_abrechnung_main


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def handle(self, *args: Any, **options: Any) -> None:
        mv_abrechnung_main()
