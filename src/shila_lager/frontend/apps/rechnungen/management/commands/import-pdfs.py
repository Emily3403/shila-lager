from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.grihed_pdf_analyzer import import_all_grihed_pdfs


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def handle(self, *args, **options):
        import_all_grihed_pdfs()

