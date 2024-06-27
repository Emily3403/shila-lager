from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.grihed_pdf_parser import import_all_grihed_pdfs
from shila_lager.frontend.apps.rechnungen.parser.inventory_counts_parser import import_lager_counts
from shila_lager.frontend.apps.rechnungen.parser.sparkasse_csv_parser import import_bookings
from shila_lager.frontend.apps.rechnungen.weekly_digest import weekly_digest
from shila_lager.settings import logger


class Command(BaseCommand):
    help = 'Weekly digest'

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting to import pdfs...")
        # import_all_grihed_pdfs()
        logger.info("Starting to import bookings...")
        import_bookings()
        logger.info("Starting to import lager counts...")
        import_lager_counts()

        weekly_digest()
