from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from math import isclose
from typing import DefaultDict

from shila_lager.frontend.apps.bestellung.models import BottleType
from shila_lager.frontend.apps.rechnungen.crud import get_shila_account_bookings
from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, GrihedInvoice
from shila_lager.settings import empty_crate_price


@dataclass
class AnalyzedBeverageCrate:
    id: str
    name: str

    total_purchased: int
    total_profit: Decimal
    total_theoretical_profit: Decimal
    total_turnover: Decimal

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


def analyze_invoices(invoices: list[GrihedInvoice]) -> list[AnalyzedBeverageCrate]:
    crates: DefaultDict[tuple[str, str], list[tuple[int, Decimal, Decimal]]] = defaultdict(list)
    crate_deposit: dict[str, Decimal] = {}
    returns: DefaultDict[Decimal, int] = defaultdict(int)
    payed_deposits: DefaultDict[Decimal, int] = defaultdict(int)
    booked_deposits: DefaultDict[Decimal, Decimal] = defaultdict(Decimal)

    # TODO: Make this faster
    # TODO: Sondergutschrift

    for invoice in invoices:
        for item in invoice.items.all():
            if item.beverage.bottle_type == BottleType.crate_return:
                returns[-item.purchase_price.price] += item.quantity
            else:
                total_profit = item.sale_price.price * item.quantity - item.total_price
                crates[item.beverage.id, item.beverage.name].append((item.quantity, total_profit, item.total_price))
                payed_deposits[item.purchase_price.deposit] += item.quantity
                crate_deposit[item.beverage.name] = item.purchase_price.deposit

    analyzed_crates = []

    for (id, name), items in crates.items():
        quantities, profits, turnovers = zip(*items)
        total_ordered = sum(quantities)

        return_value = crate_deposit[name]
        return_frac = Decimal(total_ordered) / Decimal(payed_deposits[return_value])
        total_full_crates_back = return_frac * Decimal(returns[return_value])

        returns_value = total_full_crates_back * (return_value - empty_crate_price)
        empty_crates_value = int(total_ordered - total_full_crates_back) * empty_crate_price

        # assert total_full_crates_back <= total_ordered, f"More crates returned than ordered: {total_full_crates_back} > {total_ordered}"

        total_profit = sum(profits) + returns_value + empty_crates_value
        total_theoretical_profit = sum(profits) + Decimal(total_ordered) * return_value
        total_turnover = sum(turnovers)

        # if name == 'Pilsator 0,50l':
        #     print(f"{name}: {total_ordered}, {total_profit:.2f}, {total_theoretical_profit:.2f}, {total_turnover:.2f}")

        booked_deposits[return_value] += total_full_crates_back
        analyzed_crates.append(AnalyzedBeverageCrate(id, name, total_ordered, total_profit, total_theoretical_profit, total_turnover))

    missing_sum = 0
    for value, booked in booked_deposits.items():
        assert isclose(booked, returns[value]), f"Booked {booked} crates, but payed {payed_deposits[value]} deposits for {value}"
        missing_sum += payed_deposits[value] - returns[value]

    # print(returns[Decimal(1.5)], missing_sum)

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
