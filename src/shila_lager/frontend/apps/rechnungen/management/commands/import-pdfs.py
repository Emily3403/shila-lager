from typing import Any

from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.parser.grihed_pdf_parser import import_all_grihed_pdfs


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def handle(self, *args: Any, **options: Any) -> None:
        import_all_grihed_pdfs()
