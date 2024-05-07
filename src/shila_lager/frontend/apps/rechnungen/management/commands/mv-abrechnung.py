from django.core.management import BaseCommand

from shila_lager.frontend.apps.rechnungen.mv_abrechnung import mv_abrechnung_main


class Command(BaseCommand):
    help = 'Analyze PDFs'

    def handle(self, *args, **options):
        mv_abrechnung_main()
