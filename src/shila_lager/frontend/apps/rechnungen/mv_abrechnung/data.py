from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import DefaultDict

from math import isclose

from shila_lager.frontend.apps.bestellung.models import BottleType, BeverageCrate
from shila_lager.frontend.apps.rechnungen.beverage_facts import collapse_categories
from shila_lager.frontend.apps.rechnungen.crud import get_shila_account_bookings
from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, GrihedInvoice, ShilaInventoryCount
from shila_lager.settings import empty_crate_price
from shila_lager.utils import reverse_dict


@dataclass
class AnalyzedBeverageCrate:
    id: str
    name: str

    total_purchased: int
    total_returned: Decimal
    total_profit: Decimal
    total_theoretical_profit: Decimal  # Ohne Flaschenschwund
    total_payed: Decimal

    def __str__(self) -> str:
        return f"{self.name}: {self.total_purchased}× ordered, {self.total_profit:.2f}€ profit"

    def __repr__(self) -> str:
        return self.__str__()


def get_data(start: datetime | None, end: datetime | None) -> tuple[list[ShilaAccountBooking], list[GrihedInvoice]]:
    def filter_it(it: ShilaAccountBooking | GrihedInvoice) -> bool:
        attr = it.booking_date if isinstance(it, ShilaAccountBooking) else it.date
        res = True

        if start is not None:
            res &= start.date() <= attr
        if end is not None:
            res &= attr <= end.date()

        return res

    return (
        sorted(get_shila_account_bookings(), key=lambda it: it.booking_date),
        sorted(filter(filter_it, GrihedInvoice.objects.all()), key=lambda it: it.date)
    )


def analyze_invoices(invoices: list[GrihedInvoice], inventory: tuple[ShilaInventoryCount, ShilaInventoryCount] | None = None) -> list[AnalyzedBeverageCrate]:
    old_inventory, new_inventory = inventory or (None, None)
    crates: DefaultDict[tuple[str, str], list[tuple[Decimal, Decimal, Decimal]]] = defaultdict(list)
    crate_deposit: dict[str, Decimal] = {}
    returns: DefaultDict[Decimal, int] = defaultdict(int)
    payed_deposits: DefaultDict[Decimal, int] = defaultdict(int)
    booked_deposits: DefaultDict[Decimal, Decimal] = defaultdict(Decimal)
    reversed_collapse_categories = reverse_dict(collapse_categories)
    beverage_id_to_name = {beverage.id: beverage.name for beverage in BeverageCrate.objects.all()}

    # TODO: Make this faster

    for invoice in invoices:
        for item in invoice.items.all():
            if item.beverage.bottle_type == BottleType.crate_return:
                returns[-item.purchase_price.price] += item.quantity
            else:
                beverage_id, beverage_name = item.beverage.id, item.beverage.name
                if beverage_id in reversed_collapse_categories:
                    beverage_id = reversed_collapse_categories[beverage_id]
                    beverage_name = beverage_id_to_name[beverage_id]

                total_profit = item.sale_price.price * item.quantity - item.total_price
                crates[beverage_id, beverage_name].append((Decimal(item.quantity), total_profit, item.total_price))
                payed_deposits[item.purchase_price.deposit] += item.quantity
                crate_deposit[beverage_name] = item.purchase_price.deposit

    if old_inventory is not None and new_inventory is not None:
        old_inventory_ids, new_inventory_ids = {detail.crate.id: (detail.count, detail.crate) for detail in old_inventory.details.all()}, {detail.crate.id: (detail.count, detail.crate) for detail in new_inventory.details.all()}
        all_ids = set(old_inventory_ids.keys()) | set(new_inventory_ids.keys())
        if old_inventory is not None and new_inventory is not None:
            for beverage_id in all_ids:
                if beverage_id.startswith("L") or beverage_id.startswith("R"):
                    continue

                old_quantity, old_crate = old_inventory_ids.get(beverage_id, (0, None))
                new_quantity, new_crate = new_inventory_ids.get(beverage_id, (0, None))

                if old_crate is not None:
                    beverage_name = old_crate.name
                    if beverage_id in reversed_collapse_categories:
                        beverage_id = reversed_collapse_categories[beverage_id]
                        beverage_name = beverage_id_to_name[beverage_id]

                    purchase_price = old_crate._current_purchase_price()
                    old_price = purchase_price.price * old_quantity
                    old_profit = old_crate.current_sale_price() * old_quantity - old_price
                    crates[beverage_id, beverage_name].append((Decimal(old_quantity), old_profit, old_price))

                if new_crate is not None:
                    beverage_name = new_crate.name
                    if beverage_id in reversed_collapse_categories:
                        beverage_id = reversed_collapse_categories[beverage_id]
                        beverage_name = beverage_id_to_name[beverage_id]

                    purchase_price = new_crate._current_purchase_price()
                    new_price = purchase_price.price * new_quantity
                    new_profit = new_crate.current_sale_price() * new_quantity - new_price
                    crates[beverage_id, beverage_name].append((-Decimal(new_quantity), -new_profit, -new_price))

    analyzed_crates = []

    for (beverage_id, beverage_name), items in crates.items():
        if beverage_id in reversed_collapse_categories:
            beverage_id = reversed_collapse_categories[beverage_id]
            beverage_name = beverage_id_to_name[beverage_id]

        quantities, profits, total_costs = zip(*items)
        total_ordered = sum(quantities)

        return_value = crate_deposit[beverage_name]
        return_frac = Decimal(total_ordered) / Decimal(payed_deposits[return_value])
        total_full_crates_back = return_frac * Decimal(returns[return_value])

        returns_value = total_full_crates_back * (return_value - empty_crate_price)
        empty_crates_value = int(total_ordered - total_full_crates_back) * empty_crate_price

        # assert total_full_crates_back <= total_ordered, f"More crates returned than ordered: {total_full_crates_back} > {total_ordered}"

        total_profit = sum(profits) + (returns_value + empty_crates_value if not isclose(return_value, 0) else 0)
        total_theoretical_profit = sum(profits) + Decimal(total_ordered) * return_value
        # assert total_profit <= total_theoretical_profit or total_ordered < 0
        total_turnover = sum(total_costs)

        booked_deposits[return_value] += total_full_crates_back
        analyzed_crates.append(AnalyzedBeverageCrate(beverage_id, beverage_name, total_ordered, total_full_crates_back, total_profit, total_theoretical_profit, total_turnover))

    missing_sum = 0
    for value, booked in booked_deposits.items():
        assert isclose(booked, returns[value]), f"Booked {booked} crates, but payed {payed_deposits[value]} deposits for {value}"
        missing_sum += payed_deposits[value] - returns[value]

    return analyzed_crates


def group_invoices_by_time_interval(invoices: list[GrihedInvoice], days: int) -> dict[date, list[AnalyzedBeverageCrate]]:
    grouped_invoices: DefaultDict[int, list[GrihedInvoice]] = defaultdict(list)

    min_date = min(invoice.date for invoice in invoices)
    for invoice in sorted(invoices, key=lambda it: it.date):
        bucket = (invoice.date - min_date) // days
        grouped_invoices[bucket.days].append(invoice)

    res = {}
    for invoices in grouped_invoices.values():
        res[invoices[-1].date] = analyze_invoices(invoices)

    return res
