from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.grihed_pdf_parser import import_all_grihed_pdfs
from shila_lager.frontend.apps.rechnungen.parser.inventory_counts_parser import import_lager_counts
from shila_lager.frontend.apps.rechnungen.parser.sparkasse_csv_parser import import_bookings
from shila_lager.frontend.apps.rechnungen.weekly_digest import weekly_digest
from shila_lager.settings import logger
from shila_lager.utils import parse_and_localize_date


class Command(BaseCommand):
    help = 'Weekly digest'

    def add_arguments(self, parser: Any) -> None:
        # Add --start and --end with datetime objects
        parser.add_argument('--start', type=parse_and_localize_date, help='Start date (inclusive)')
        parser.add_argument('--end', type=parse_and_localize_date, help='End date (exclusive)')

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting to import pdfs...")
        # import_all_grihed_pdfs()
        logger.info("Starting to import bookings...")
        import_bookings()
        logger.info("Starting to import lager counts...")
        import_lager_counts()

        weekly_digest(options.get("start"), options.get("end"))
