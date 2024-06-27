from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from typing import Iterable, DefaultDict

import numpy as np
from math import isclose

from shila_lager.frontend.apps.bestellung.crud import get_beverage_crates
from shila_lager.frontend.apps.rechnungen.analyze import analyze_beverage_crates, pfand_scale_factor
from shila_lager.frontend.apps.rechnungen.beverage_facts import digest_categories
from shila_lager.frontend.apps.rechnungen.crud import get_inventory_counts, get_shila_account_bookings, get_grihed_invoices
from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount, ShilaAccountBooking, ShilaBookingCategory, AnalyzedBeverageCrate, ShilaBookingKind
from shila_lager.settings import bright_color, reset_color, underline_color
from shila_lager.utils import parse_numeric, reverse_dict, filter_by_date, BeverageID


def output_value(old: ShilaInventoryCount, new: ShilaInventoryCount, bookings: Iterable[ShilaAccountBooking], analyzed_crates: dict[BeverageID, AnalyzedBeverageCrate]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    old_balance = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), None, old.date))
    new_balance = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), None, new.date))

    old_inventory_value = sum(detail.count * detail.crate.current_purchase_price() for detail in old.details.all())
    new_inventory_value = sum(detail.count * detail.crate.current_purchase_price() for detail in new.details.all())

    profit = new_balance + new_inventory_value + new.other_monetary_value - old_balance - old_inventory_value - old.other_monetary_value
    profit_with_extra_expenses = profit + sum(parse_numeric(it) for it in new.extra_expenses.values())
    expected_profit = sum(crate.total_profit for crate in analyzed_crates.values())
    expected_profit_without_deposits = sum(crate.total_profit_without_deposits for crate in analyzed_crates.values())
    expected_profit_with_payed_but_not_returned_deposits = sum(crate.total_profit_with_payed_but_not_returned_deposits for crate in analyzed_crates.values())

    expected_income = sum(crate.num_sold * crate.beverage.current_sale_price() + crate.total_deposit_returned for crate in analyzed_crates.values())
    actual_income = new.money_in_safe + new.other_monetary_value - old.other_monetary_value

    has_extra_expenses = new.extra_expenses

    print(f"\n{bright_color}{underline_color}Auswertung vom {old.date.strftime('%Y-%m-%d')} bis {new.date.strftime('%Y-%m-%d')}:{reset_color}")
    # print(f"Vorheriger Kontostand:\t{old_balance:.2f}€")
    # print(f"Vorheriger Lagerwert:\t{old_inventory_value:.2f}€")
    # print()
    # print(f"Aktueller Kontostand:\t{new_balance:.2f}€")
    # print(f"Aktueller Lagerwert:\t{new_inventory_value:.2f}€")
    # print()
    print(f"Vorheriger Wert:\t{old_balance + old_inventory_value:.2f}€")
    print(f"Aktueller Wert:\t\t{new_balance + new_inventory_value:.2f}€")
    print("─" * 33)
    print(f"{'Eigentlicher ' if has_extra_expenses else ''}Profit:{chr(9) * 2 if not has_extra_expenses else ''}\t{profit_with_extra_expenses:.2f}€")
    print(f"Erwarteter Profit:\t{expected_profit:.2f}€")
    print(f"(ohne Pfand):\t\t{expected_profit_without_deposits:.2f}€")
    print(f"(Faktor {pfand_scale_factor}):\t\t{expected_profit_with_payed_but_not_returned_deposits:.2f}€")

    # TODO: Diese Darstellung ist ein wenig verwirrend, da erwarteter profit mit profit ähnlich sein sollten
    print(f"\nSchwund:          \t{expected_profit - profit_with_extra_expenses:.2f}€")

    print(f"\nErwartete Einnahmen:\t{expected_income:.2f}€")
    print(f"Tatsächliche Einnahmen:\t{actual_income:.2f}€")

    if has_extra_expenses:
        print(f"\nSonderausgaben:\t\t{profit_with_extra_expenses - profit:.2f}€")
        for name, value in new.extra_expenses.items():
            print(f"  - {name}: {f'{value.strip()} = ' if isinstance(value, str) else ''}{parse_numeric(value):.2f}€")

    return Decimal(profit_with_extra_expenses), Decimal(expected_profit_without_deposits - profit_with_extra_expenses), Decimal(expected_profit - profit_with_extra_expenses), Decimal(expected_profit_with_payed_but_not_returned_deposits - profit_with_extra_expenses)


def output_beverage_consumption_and_expected_profit(analyzed_beverage_crates: dict[BeverageID, AnalyzedBeverageCrate]) -> None:
    reversed_digest_categories = reverse_dict(digest_categories)
    expected_category_profits: DefaultDict[str, Decimal] = defaultdict(Decimal)
    expected_profit, total_payed = Decimal(0), Decimal(0)

    for invoice in sorted(analyzed_beverage_crates.values(), key=lambda it: it.num_ordered, reverse=True):
        if invoice.beverage.id.startswith("R"):
            continue

        expected_profit += invoice.total_profit
        total_payed += invoice.total_payed
        expected_category_profits[reversed_digest_categories.get(invoice.beverage.id, "Anderes")] += invoice.total_profit

    # print(f"\n{bright_color}{underline_color}Getränke:{reset_color}")
    # print(f"Erwarteter Profit:\t{expected_profit:.2f}€")
    # print(f"Diff:\t\t\t{expected_profit - actual_profit:.2f}€")
    # print()
    print(f"\n{bright_color}Erwarteter Profit pro Getränke-Kategorie:{reset_color}")
    for category, profit in expected_category_profits.items():
        print(f"{category}: {profit:.2f}€")

    print()
    for crate in sorted(analyzed_beverage_crates.values(), key=lambda it: it.num_sold, reverse=True):
        if all(isclose(it, 0) for it in [crate.total_profit, crate.num_sold, crate.num_returned]):
            continue
        print(f"{bright_color}{(crate.beverage.name + ':').ljust(45, ' ')}{reset_color}{crate.num_sold:.2f} verkauft, \t{crate.num_ordered:.2f} gekauft, \t{crate.num_returned:.2f} zurück, \t{crate.total_profit:.2f}€\tprofit")
    pass
    # Expected profit

    # Beverage consumption

    # Gewinn / Umsatz pro Getränkeart

    # Flaschenschwund

    pass


def output_income_and_expenses(old: ShilaInventoryCount, new: ShilaInventoryCount, bookings: Iterable[ShilaAccountBooking]) -> None:
    total_profit = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), old.date, new.date))
    total_expenses = -sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), old.date, new.date) and booking.amount < 0)
    total_money_in = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), old.date, new.date) and booking.amount > 0)
    total_einzahlungen = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), old.date, new.date) and booking.category == ShilaBookingCategory.sparkasse_income)

    total_expense_per_category: DefaultDict[ShilaBookingCategory, Decimal] = defaultdict(Decimal)
    for booking in bookings:
        if filter_by_date(booking.actual_booking_date(), old.date, new.date):
            total_expense_per_category[booking.category] -= booking.amount

    print(f"\n{bright_color}{underline_color}Ausgaben:{reset_color}")
    category_sequence = sorted(ShilaBookingCategory, key=lambda cat: total_expense_per_category[cat], reverse=True)
    cat_strs, val_strs = [f"{cat.value}:" for cat in category_sequence], [f"{total_expense_per_category[cat]:.2f}€" for cat in category_sequence]
    max_len_cat, max_len_val = max(len(cat_str) for cat_str in cat_strs), max(len(it) for it in val_strs)
    for category, cat_str, val_str in zip(category_sequence, cat_strs, val_strs):
        if category != ShilaBookingCategory.sparkasse_income and total_expense_per_category[category] > 0:
            print(f"{cat_str.ljust(max_len_cat)} {val_str.rjust(max_len_val)}\t")

    print("─" * 33)
    print(f"Epirische Ausgaben:\t{total_expenses:.2f}€")
    print(f"Eingezahltes Geld:\t{total_einzahlungen:.2f}€")
    if not isclose(total_money_in, total_einzahlungen):
        print(f"Ingesamt Plus:\t\t{total_money_in:.2f}€")
    print(f"Tatsächlicher Profit:\t {total_profit:.2f}€")


def weekly_digest(start: datetime | None = None, end: datetime | None = None) -> None:
    bookings, inventory_counts = get_shila_account_bookings(), get_inventory_counts()
    filtered_inventory_counts = [it for it in inventory_counts if filter_by_date(it.date, start, end)]

    all_profits = []
    all_analyzed_beverage_crates = []
    for old, new in pairwise(sorted(filtered_inventory_counts, key=lambda x: x.date)):
        # TODO: Actual booking date does not take into account when multiple invoices are booked at the same time
        analyzed_beverage_crates = analyze_beverage_crates(get_beverage_crates(), old.date, new.date, (old, new))

        profits = output_value(old, new, bookings, analyzed_beverage_crates)
        # output_beverage_consumption_and_expected_profit(analyzed_beverage_crates)

        all_profits.append(profits[1:])
        all_analyzed_beverage_crates.append(analyzed_beverage_crates)
        print("\n\n")

    nd_all_profits = np.array(all_profits, dtype=object)
    averages = np.average(nd_all_profits, axis=0)
    print(f"\n{bright_color}{underline_color}Durchschnittlicher Schwund:{reset_color}")
    print(f"100% Pfand zurück: \t{averages[0]:.2f}€")
    print(f"\"Echter\" Pfand zurück: \t{averages[1]:.2f}€")
    print(f"{pfand_scale_factor * 100}% Pfand zurück: \t{averages[2]:.2f}€")
    print()
    print(f"Standardabweichung: \t{np.std(nd_all_profits, axis=0)[1]:.2f}")
