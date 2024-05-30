from pathlib import Path

import yaml

from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount
from shila_lager.settings import manual_upload_dir


def import_lager_file(file: Path) -> ShilaInventoryCount | None:
    if file.name == "default.yaml":
        return None

    with open(file) as f:
        _ = yaml.safe_load(f)
        pass

    return None


def import_lager() -> None:
    files = []
    for file in (manual_upload_dir / "Lagerzählungen").iterdir():
        files.append(import_lager_file(file))
