from collections import defaultdict
from decimal import Decimal
from itertools import pairwise
from math import isclose
from typing import Iterable, DefaultDict

from shila_lager.frontend.apps.bestellung.crud import get_beverage_crates
from shila_lager.frontend.apps.rechnungen.analyze import analyze_beverage_crates
from shila_lager.frontend.apps.rechnungen.crud import get_inventory_counts, get_shila_account_bookings, get_grihed_invoices
from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount, ShilaAccountBooking, ShilaBookingCategory, GrihedInvoice
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.data import analyze_invoices
from shila_lager.frontend.apps.rechnungen.beverage_facts import digest_categories
from shila_lager.settings import bright_color, reset_color, underline_color
from shila_lager.utils import parse_numeric, reverse_dict, filter_by_date


def output_value(old: ShilaInventoryCount, new: ShilaInventoryCount, bookings: Iterable[ShilaAccountBooking]) -> Decimal:
    old_balance = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), None, old.date))
    new_balance = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), None, new.date))

    old_inventory_value = sum(detail.count * detail.crate.current_sale_price() for detail in old.details.all())
    new_inventory_value = sum(detail.count * detail.crate.current_sale_price() for detail in new.details.all())
    profit = new_balance + new_inventory_value - old_balance - old_inventory_value
    profit_with_extra_expenses = profit + sum(parse_numeric(it) for it in new.extra_expenses.values())

    print(f"\n{bright_color}{underline_color}Auswertung vom {old.date.strftime('%Y-%m-%d')} bis {new.date.strftime('%Y-%m-%d')}:{reset_color}")
    print(f"Vorheriger Kontostand:\t{old_balance:.2f}€")
    print(f"Vorheriger Lagerwert:\t{old_inventory_value:.2f}€")
    print()
    print(f"Aktueller Kontostand:\t{new_balance:.2f}€")
    print(f"Aktueller Lagerwert:\t{new_inventory_value:.2f}€")
    print()
    print(f"Vorheriger Wert:\t{old_balance + old_inventory_value:.2f}€")
    print(f"Aktueller Wert:\t\t{new_balance + new_inventory_value:.2f}€")
    print("─" * 33)
    print(f"Profit:\t\t\t{profit:.2f}€")
    print(f"Profit ohne Extras:\t{profit_with_extra_expenses:.2f}€")
    print()

    if new.extra_expenses:
        print("Extra Ausgaben, die gemacht wurden:")
        for name, value in new.extra_expenses.items():
            print(f"  - {name}: {f'{value.strip()} = ' if isinstance(value, str) else ''}{parse_numeric(value):.2f}€")

    return Decimal(profit_with_extra_expenses)


def output_beverage_consumption_and_expected_profit(old: ShilaInventoryCount, new: ShilaInventoryCount, invoices: Iterable[GrihedInvoice], actual_profit: Decimal) -> None:
    filtered_invoices = [invoice for invoice in invoices if filter_by_date(invoice.date, old.date, new.date)]
    analyzed_beverage_crates = analyze_beverage_crates(get_beverage_crates(), old.date, new.date, (old, new))
    # analyzed_beverage_crates = analyze_invoices(filtered_invoices, (old, new))
    reversed_digest_categories = reverse_dict(digest_categories)
    expected_category_profits: DefaultDict[str, Decimal] = defaultdict(Decimal)
    expected_profit, total_payed = Decimal(0), Decimal(0)

    for invoice in sorted(analyzed_beverage_crates, key=lambda it: it.num_ordered, reverse=True):
        if invoice.beverage.id.startswith("R"):
            continue

        expected_profit += invoice.total_profit
        total_payed += invoice.total_payed
        expected_category_profits[reversed_digest_categories.get(invoice.beverage.id, "Anderes")] += invoice.total_profit

    print(f"\n{bright_color}{underline_color}Getränke:{reset_color}")
    print(f"Erwarteter Profit:\t{expected_profit:.2f}€")
    print(f"Diff:\t\t\t{expected_profit - actual_profit:.2f}€")
    print()
    print(f"{bright_color}Erwarteter Profit pro Kategorie:{reset_color}")
    for category, profit in expected_category_profits.items():
        print(f"{category}: {profit:.2f}€")

    print()
    for crate in sorted(analyzed_beverage_crates, key=lambda it: it.num_ordered, reverse=True):
        print(f"{bright_color}{(crate.beverage.name + ':').ljust(45, ' ')}{reset_color}{crate.num_ordered:.2f}× verkauft, \t{crate.num_returned:.2f}× zurück, \t{crate.total_profit:.2f}€\t({crate.total_theoretical_profit:.2f}€) profit")
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


def weekly_digest() -> None:
    invoices, bookings, inventory_counts = get_grihed_invoices(), get_shila_account_bookings(), get_inventory_counts()

    for old, new in pairwise(sorted(inventory_counts, key=lambda x: x.date)):
        # TODO: Actual booking date does not take into account when multiple invoices are booked at the same time
        profit = output_value(old, new, bookings)
        output_beverage_consumption_and_expected_profit(old, new, invoices, profit)
        output_income_and_expenses(old, new, bookings)
        print("\n\n")
