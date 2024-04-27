#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from shila_lager.utils import startup


def main() -> None:
    """Run administrative tasks."""
    startup()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shila_lager.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
