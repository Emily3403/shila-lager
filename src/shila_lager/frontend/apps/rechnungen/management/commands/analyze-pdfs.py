from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.grihed_pdf_analyzer import analyze_all_grihed_pdfs


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def handle(self, *args, **options):
        analyze_all_grihed_pdfs()

