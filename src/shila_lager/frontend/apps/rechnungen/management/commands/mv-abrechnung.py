from typing import Any

from dateutil.parser import parse as parse_datetime
from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.mv_abrechnung.main import mv_abrechnung_main


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def add_arguments(self, parser: Any) -> None:
        # Add --start and --end with datetime objects
        parser.add_argument('--start', type=parse_datetime, help='Start date (inclusive)')
        parser.add_argument('--end', type=parse_datetime, help='End date (exclusive)')

    def handle(self, *args: Any, **options: Any) -> None:
        mv_abrechnung_main(options.get("start"), options.get("end"))
