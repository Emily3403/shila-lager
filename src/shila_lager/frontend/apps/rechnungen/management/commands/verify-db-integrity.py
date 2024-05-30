from typing import Any

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Verify the integrity of the database'

    def handle(self, *args: Any, **options: Any) -> None:
        print("TODO: This command")
