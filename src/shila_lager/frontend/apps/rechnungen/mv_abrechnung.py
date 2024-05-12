from datetime import datetime
from decimal import Decimal

from pytz import UTC

from shila_lager.frontend.apps.bestellung.models import BeverageCrate


def analyze_total_profit() -> None:
    beverage_crates: list[BeverageCrate] = sorted(BeverageCrate.objects.all(), key=lambda it: it.name)
    total_profit, real_total_payed, real_total_sold = Decimal(0), Decimal(0), Decimal(0)
    max_num_orderes = 0

    for crate in beverage_crates:
        invoice_items = crate.invoice_items.all()
        if not invoice_items:
            continue

        total_payed, total_sold, total_quantity = Decimal(0), Decimal(0), Decimal(0)

        # TODO: Pfand, Soli-Rabatte
        for item in invoice_items:
            if item.invoice.date <= UTC.localize(datetime.strptime("01.01.2024", "%d.%m.%Y")):
                continue
            total_payed += item.total_price
            total_sold += item.quantity * item.sale_price.price
            total_quantity += item.quantity

        print(f"{crate.name}: {total_sold - total_payed}€ in {total_quantity} crates and {len(invoice_items)} orders")
        print(f"Average number of crates ordered: {total_quantity / len(invoice_items):.2f}\n")

        total_profit += total_sold - total_payed
        real_total_payed += total_payed
        real_total_sold += total_sold
        max_num_orderes = max(max_num_orderes, len(invoice_items))

    print(f"\n\nTotal profit: {total_profit}, average profit per order: {total_profit / len(beverage_crates):.2f}")
    print(f"Total payed: {real_total_payed}, total sold: {real_total_sold}")


def analyze_deposit() -> None:
    pass


def analyze_account_bookings() -> None:
    pass


def mv_abrechnung_main() -> None:
    analyze_total_profit()
    pass
