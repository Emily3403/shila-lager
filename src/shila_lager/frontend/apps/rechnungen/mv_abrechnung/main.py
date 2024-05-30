import re
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import DefaultDict

from shila_lager.frontend.apps.bestellung.crud import get_beverage_crates
from shila_lager.frontend.apps.bestellung.models import BeverageCrate
from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, GrihedInvoice, ShilaBookingKind, ShilaBookingCategory
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.data import get_data, analyze_invoices, AnalyzedBeverageCrate
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.plots import plot_shila_value, plot_bookings, plot_beverage_profit_and_turnover_piecharts, plot_turnover_categories
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.static_data import current_inventory
from shila_lager.settings import logger
from shila_lager.utils import filter_by_datetime, filter_by_date


def calculate_inventory_value(beverages: dict[str, BeverageCrate]) -> tuple[Decimal, Decimal]:
    inventory_value_when_sold, inventory_value_to_purchase = Decimal(0), Decimal(0)
    for (id, _), amount in current_inventory.items():
        inventory_value_when_sold += beverages[id].current_sale_price() * Decimal(amount)
        inventory_value_to_purchase += beverages[id].current_purchase_price() * Decimal(amount)

    return inventory_value_when_sold, inventory_value_to_purchase


def calculate_account_balance(bookings: list[ShilaAccountBooking], invoices: list[GrihedInvoice], start: datetime | None = None, end: datetime | None = None) -> Decimal:
    invoices_by_id = {invoice.invoice_number: invoice for invoice in invoices}
    current_account_balance = Decimal(sum(booking.amount for booking in bookings))

    already_booked: set[str] = set()
    for booking in bookings:
        if booking.beneficiary_or_payer == "GRIHED Service GmbH":
            booking_numbers = re.findall(r"RE(\d+-\d+) vom (\d{2}\.\d{2}\.\d{4})", booking.description)
            assert booking_numbers, f"Could not find invoice number in booking description: {booking.description}"
            for invoice_number, booking_date in booking_numbers:

                if invoice_number not in invoices_by_id and filter_by_datetime(datetime.strptime(booking_date, "%d.%m.%Y"), start, end) and not booking_date.endswith("2022"):
                    print(f"Booking {invoice_number} was not found in invoices ({booking_date})")
                    continue

                match booking.kind:
                    case ShilaBookingKind.lastschrift:
                        assert invoice_number not in already_booked, f"Booking {invoice_number} was already booked"
                        already_booked.add(invoice_number)
                    case ShilaBookingKind.lastschrift_undo:
                        already_booked.remove(invoice_number)
                    case _:
                        logger.error(f"Unknown booking kind: {booking.kind}")

    debt_to_grihed = Decimal(sum(invoice.total_price for invoice in invoices if invoice.invoice_number not in already_booked))

    print(f"Ursprünglicher Kontostand:\t{current_account_balance:.2f}€")
    print(f"Grihed Schulden:\t{debt_to_grihed:.2f}€")
    return current_account_balance - debt_to_grihed


def calculate_and_plot_shila_value(bookings: list[ShilaAccountBooking], invoices: list[GrihedInvoice], beverages: dict[str, BeverageCrate], start: datetime | None = None, end: datetime | None = None) -> Decimal:
    current_account_balance = calculate_account_balance(bookings, invoices, start, end)
    inventory_value_when_sold, inventory_value_to_purchase = calculate_inventory_value(beverages)
    tips, kleingeld = Decimal(2596.64), Decimal(675.25)
    debts_to_shila = Decimal(
        (
            5 * 3 + 4
            + 5 * 2
            + 5 * 8 + 1
            + 5 * 3
            + 5 + 3
            + 5 * 5 + 1
            + 5 * 2 + 2
            + 2
            + 4
            + 5 + 4
            + 2
            + 1
            + 2
            + 2
            + 5 + 3
            + 2
        ) * 0.5) + Decimal(512.18)

    print(f"Wert des Kontos:\t{current_account_balance - tips:.2f}€")
    print(f"Wert des Inventars:\t{inventory_value_when_sold:.2f}€")
    print(f"Kleingeld:\t\t {kleingeld:.2f}€")
    print(f"Schulden beim Shila:\t {debts_to_shila:.2f}€")
    print(f"Trinkgeld:\t\t{tips:.2f}€")
    print("─" * 32)
    print(f"Wert des Shilas:\t{current_account_balance - tips + inventory_value_when_sold + debts_to_shila + kleingeld:.2f}€")
    print()

    plot_shila_value(current_account_balance, inventory_value_when_sold, tips, debts_to_shila, kleingeld)

    return current_account_balance - tips + inventory_value_when_sold + debts_to_shila + kleingeld


def print_and_plot_profits_and_turnovers(bookings: list[ShilaAccountBooking], analyzed_crates: list[AnalyzedBeverageCrate], start: datetime | None = None, end: datetime | None = None) -> None:
    total_profit = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), start, end))
    total_turnover = -sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), start, end) and booking.amount < 0)
    total_money_in = sum(booking.amount for booking in bookings if filter_by_date(booking.actual_booking_date(), start, end) and booking.amount > 0)

    total_turnover_per_category: DefaultDict[ShilaBookingCategory, Decimal] = defaultdict(Decimal)
    for booking in bookings:
        if filter_by_date(booking.actual_booking_date(), start, end) and booking.amount < 0:
            total_turnover_per_category[booking.category] -= booking.amount

    print()
    print(f"Erwarteter Profit:\t {sum(crate.total_profit for crate in analyzed_crates):.2f}€")
    print(f"Erwarteter Umsatz:\t{sum(crate.total_turnover for crate in analyzed_crates):.2f}€")
    print()
    print(f"Getränke Umsatz:\t{total_turnover_per_category[ShilaBookingCategory.beverages]:.2f}€")
    print(f"Gepa Umsatz:\t\t {total_turnover_per_category[ShilaBookingCategory.gepa]:.2f}€")
    print(f"Bringmeister Umsatz\t  {total_turnover_per_category[ShilaBookingCategory.bringmeister]:.2f}€")
    print(f"Schokolade Umsatz:\t  {total_turnover_per_category[ShilaBookingCategory.chocholate]:.2f}€")
    print(f"Hosting Umsatz:\t\t   {total_turnover_per_category[ShilaBookingCategory.hosting]:.2f}€")
    print(f"Sonstiger Umsatz:\t {total_turnover_per_category[ShilaBookingCategory.other]:.2f}€")
    print("─" * 33)
    print(f"Tatsächlicher Umsatz:\t{total_turnover:.2f}€")
    print(f"Eingezahltes Geld:\t{total_money_in:.2f}€")
    print(f"Tatsächlicher Profit:\t {total_profit:.2f}€")

    plot_turnover_categories(dict(total_turnover_per_category))


def mv_abrechnung_main(start: datetime | None = None, end: datetime | None = None) -> None:
    # TODO: Pro Bestellung schauen wie viel gratis Wicküler es wären um einen Überschlag zu haben wie viele frei gesoffen werden könnten
    #   Mit folgestatistik "Alle Mitglieder könnten jeden Tag 42 Bier trinken und wir wären immernoch profitablel mit 69%"
    #   Wie sähe unser Kontostand aus, wenn jeden Tag 42 Bier getrunken werden würden

    s = time.perf_counter()

    # Invoices are filtered by date, bookings are not
    bookings, invoices = get_data(start, end)
    beverage_crates = get_beverage_crates()
    analyzed_crates = analyze_invoices(invoices)

    calculate_and_plot_shila_value(bookings, invoices, beverage_crates, start, end)
    print_and_plot_profits_and_turnovers(bookings, analyzed_crates, start, end)

    plot_bookings(bookings, start, end, True)
    plot_beverage_profit_and_turnover_piecharts(analyzed_crates)
    # plot_beverage_consumption_over_time(invoices, start, end)

    print(f"Time elapsed: {time.perf_counter() - s:.2f}s")
