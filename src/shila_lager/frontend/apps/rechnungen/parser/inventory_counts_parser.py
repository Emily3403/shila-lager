from pathlib import Path

import yaml
from dateutil.parser import parse
from pytz import UTC

from shila_lager.frontend.apps.bestellung.crud import get_beverage_crates
from shila_lager.frontend.apps.bestellung.models import BeverageCrate
from shila_lager.frontend.apps.rechnungen.crud import get_inventory_counts
from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount, ShilaInventoryCountDetail
from shila_lager.settings import manual_upload_dir, logger
from shila_lager.utils import parse_numeric


def import_lager_file(file: Path, inventory_counts: set[ShilaInventoryCount], beverages: dict[str, BeverageCrate]) -> ShilaInventoryCount | None:
    if file.name == "default.yaml":
        return None

    with open(file) as f:
        data = yaml.safe_load(f)
        money_data: dict[str, str | int | float] = data["Geld"]
        lager_data: dict[str, str | int | float] = data["Grihed"]
        extra_expenses: dict[str, str | int | float] = data.get("Sonderausgaben") or {}
        money_in_safe: float = data["Tresor"]

        assert isinstance(lager_data, dict)
        assert isinstance(money_data, dict)
        assert isinstance(extra_expenses, dict)

        inventory_count = ShilaInventoryCount(
            date=UTC.localize(parse(file.stem)),
            other_monetary_value=sum(parse_numeric(money) for money in money_data.values()),
            money_in_safe=parse_numeric(money_in_safe),
            extra_expenses=extra_expenses
        )

        if inventory_count in inventory_counts:
            # Updating is not supported.
            return None

        inventory_count.save()
        details = []

        for _name, count in lager_data.items():
            crate_id = _name.split(" ")[0]

            if crate_id not in beverages:
                logger.error(f"Unknown crate_id: {crate_id}")
                continue

            crate = beverages[crate_id]
            num = parse_numeric(count)
            details.append(ShilaInventoryCountDetail(crate=crate, count=num, date=inventory_count))

        ShilaInventoryCountDetail.objects.bulk_create(details)
        inventory_count.save()

    return None


def import_lager_counts() -> None:
    files, beverages, inventory_counts = [], get_beverage_crates(), get_inventory_counts()
    for file in (manual_upload_dir / "Lagerzählungen").iterdir():
        files.append(import_lager_file(file, inventory_counts, beverages))
