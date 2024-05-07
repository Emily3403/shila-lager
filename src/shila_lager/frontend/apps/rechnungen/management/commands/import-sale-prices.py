from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.grihed_pdf_analyzer import import_sale_prices


class Command(BaseCommand):
    help = 'Import sale prices'

    def handle(self, *args, **options):
        import_sale_prices()
