from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from math import isclose

from shila_lager.frontend.apps.bestellung.crud import get_sorted_grihed_prices, create_grihed_price, get_beverage_crates, create_beverage_crate, get_sorted_sale_prices
from shila_lager.frontend.apps.bestellung.models import BottleType, GrihedPrice, SalePrice
from shila_lager.frontend.apps.rechnungen.models import GrihedInvoice, GrihedInvoiceItem, ShilaAccountBooking
from shila_lager.settings import logger
from shila_lager.utils import german_price_to_decimal

sale_price_translation = price_translation = {
    ("B0991", "Allgäuer Büble Edelbräu"): 1.5 * 20,
    ("B0995", "Andechs Spezial hell 0,50l"): 1.5 * 20,
    ("B0996", "Astra Urtyp Pils 0,33l"): 1 * 27,
    ("S2247", "Becker Maracuja 1,0l Tetra"): 3 * 6,
    ("E3127", "Bionade  Zitr.Bergamotte 0,33l  12er"): 1 * 12,
    ("E3128", "Bionade Mix (Hol/Ing/Kr/Lit.) 0,33l  12er"): 1 * 12,
    ("E3130", "Bionade naturtrübe Orange 0,33l  12er"): 1 * 12,
    ("E3132", "Bionade naturtrübe Zitrone 0,33l  12er"): 1 * 12,
    ("B1035", "Berliner Kindl Jubiläums Pilsener 0,33l"): 1 * 24,
    ("B1040", "Berliner Kindl Jubiläums Pilsener 0,50l"): 1.5 * 20,
    ("B1047", "Berliner Kindl Radler (trüb)"): 1 * 20,
    ("B1053", "Berliner Pilsner 0,33l"): 1 * 24,
    ("W8010", "C. Jacob Gr. Burgunder (Pfalz) trocken"): 6,
    ("W8012", "C. Jacob weisser Burgunder (Pfalz) trocken"): 6,
    ("W8033", "Chardonnay IGT Mezzadro"): 6,
    ("B1345", "Clausthaler Extra Herb Alkoholfrei 0,50l"): 1 * 20,
    ("E3438", "Club Mate"): 1 * 20,
    ("E3351", "Fritz Bio-Apfelsaftschorle 0,33l"): 1.2 * 24,
    ("E3354", "Fritz Bio-Rhabarbersaftschorle 0,33l"): 1.2 * 24,
    ("E3347", "Fritz Zitrone 0,33l"): 1.2 * 24,
    ("E3433", "Mio Mio Mate Ginger 0,50l"): 1.2 * 24,
    ("E3449", "Paulaner Spezi Original  0,50l"): 1 * 20,
    ("K5003", "H - Milch 3,8% Arla - BIO"): 0,
    ("K5005", "H - Milch aro 1,5% Fett"): 0,
    ("W8028", "Hüttenglut Glühwein 6x1,00l"): 18,
    ("B1357", "Jever Fun 0,50l"): 1 * 20,
    ("B1165", "Jever Pils 0,50l"): 1.5 * 20,
    ("W8025", "Kimmle Riesling  6 x 1,0l (weiss) Mehrweg"): 6 * 6,
    ("L0150", "Leergutkasten komplett"): 1.5,
    ("L0310", "Leergutkasten komplett"): 3.1,
    ("L0330", "Leergutkasten komplett"): 3.3,
    ("L0342", "Leergutkasten komplett"): 3.42,
    ("L0450", "Leergutkasten komplett"): 4.5,
    ("L0240", "Leergutkasten komplett"): 2.4,
    ("L0366", "Leergutkasten komplett"): 3.66,
    ("L0510", "Leergutkasten komplett"): 5.1,
    ("L0650", "Leergutkasten komplett"): 6.5,
    ("L0300", "Leergutkasten komplett"): 3,
    ("W8019", "Leoff Riesling, trocken"): 6,
    ("W8017", "Leoff gr. Burgunder, trocken"): 6,
    ("W8021", "Leoff weisser Burgunder, trocken"): 6,
    ("O7185", "Lutter & Wegner  Gendarmenmarkt Trocken 11%"): 6,
    ("B1183", "Pilsator 0,50l"): 1 * 20,
    ("E3416", "Proviant Apfelschorle naturtrüb 0,33l (60%)"): 1 * 24,
    ("E3417", "Proviant Limonade Ingwer-Zitrone 0,33l"): 1 * 24,
    ("E3419", "Proviant Limonade Orange naturtrüb 0,33l"): 1 * 24,
    ("E3418", "Proviant Limonade Rhabarber naturtrüb 0,33l"): 1 * 24,
    ("O7040", "Rotkäppchen trocken, 11%"): 6,
    ("B1225", "Schultheiss Pils 0,50l"): 1 * 20,
    ("E3456", "Soli Cola 0,50l"): 1 * 20,
    ("E3451", "Soli Mate  Bio  0,50l"): 1 * 20,
    ("R0001", "Sondergutschrift laut Hinweis (inkl. voller Ust)"): 0,
    ("E3446", "Spezi 0,50l"): 1 * 20,
    ("M4135", "Spreequell Classic  1,0l PET"): 0.8 * 12,
    ("M4195", "Spreequell Naturelle 1,0l PET"): 0.8 * 12,
    ("B1245", "Sternburger Export 0,50l"): 1 * 20,
    ("O7060", "Söhnlein Brillant Jahrgangssekt trocken,11%"): 6,
    ("E3450", "Th. Henry Mate Mate"): 1 * 20,
    ("B1278", "Wicküler Pilsener 0,50l"): 1 * 20,
    ("K5230", "aro Zucker Kg-Packung"): 0,
    ("L0008", "leere Einzelflasche Mw (Bier)"): 0.08,
}


# TODO: Refactor this into a more general approach for prices
def maybe_create_grihed_price(prices: defaultdict[str, list[GrihedPrice]], beverage_id: str, price: Decimal, deposit: Decimal, date: datetime) -> GrihedPrice:
    def create_price() -> GrihedPrice:
        final_price = create_grihed_price(beverage_id, price, deposit, date)
        prices[beverage_id].append(final_price)
        prices[beverage_id].sort(key=lambda it: it.valid_from, reverse=True)
        return final_price

    prices_for_beverage = prices.get(beverage_id)
    if prices_for_beverage is None:
        # No prices for this beverage exist yet
        return create_price()

    maybe_valid_price = next((grihed_price for grihed_price in prices_for_beverage if grihed_price.valid_from <= date), None)
    if maybe_valid_price is not None and isclose(maybe_valid_price.price, price):
        # This is the one
        return maybe_valid_price

    # Now, either the price is different or there is no valid price for this date. So, check if the same price exists already and, if so, update the valid_from date
    maybe_same_price = next((grihed_price for grihed_price in prices_for_beverage if isclose(grihed_price.price, price)), None)
    if maybe_same_price is not None:
        maybe_same_price.valid_from = date
        maybe_same_price.save()
        return maybe_same_price

    return create_price()


def maybe_create_sale_price(prices: defaultdict[str, list[SalePrice]], beverage_id: str, beverage_name: str, valid_from: datetime) -> SalePrice:
    price = sale_price_translation.get((beverage_id, beverage_name))
    if price is None:
        raise ValueError(f"No price found for beverage {beverage_id} {beverage_name}")

    def create_price() -> SalePrice:
        final_price = SalePrice(crate_id=beverage_id, price=price, valid_from=valid_from)
        final_price.save()
        prices[beverage_id].append(final_price)
        prices[beverage_id].sort(key=lambda it: it.valid_from, reverse=True)
        return final_price

    prices_for_beverage = prices.get(beverage_id)
    if prices_for_beverage is None:
        # No prices for this beverage exist yet
        return create_price()

    maybe_valid_price = next((sale_price for sale_price in prices_for_beverage if sale_price.valid_from <= valid_from), None)
    if maybe_valid_price is not None and isclose(maybe_valid_price.price, price):
        # This is the one
        return maybe_valid_price

    # Now, either the price is different or there is no valid price for this date. So, check if the same price exists already and, if so, update the valid_from date
    maybe_same_price = next((sale_price for sale_price in prices_for_beverage if isclose(sale_price.price, price)), None)
    if maybe_same_price is not None:
        maybe_same_price.valid_from = valid_from
        maybe_same_price.save()
        return maybe_same_price

    return create_price()


def create_invoice(invoice_number: str, date: datetime, total_price: Decimal, items: list[tuple[str, str, str, str, str, str, str, str]]) -> GrihedInvoice:
    invoice, _ = GrihedInvoice.objects.update_or_create(invoice_number=invoice_number, date=date, total_price=total_price)
    invoice.save()

    beverages = get_beverage_crates()
    grihed_prices = get_sorted_grihed_prices()
    sale_prices = get_sorted_sale_prices()

    for item in items:
        _quantity, _beverage_id, name, content, bottle_type, _deposit, _price, _total = item

        quantity = int(1 if _quantity == "####" else _quantity)
        beverage_id = _beverage_id.replace(" ", "")
        deposit = german_price_to_decimal(_deposit)
        total = german_price_to_decimal(_total)
        price = german_price_to_decimal(_price) if _quantity != "####" else total

        if price is None or deposit is None or total is None:
            logger.error(f"Price could not be parsed in {invoice_number} for {name}")
            continue

        beverage = beverages.get(beverage_id) or create_beverage_crate(beverage_id, name, content, BottleType.from_str(bottle_type))
        grihed_price = maybe_create_grihed_price(grihed_prices, beverage_id, price, deposit, date)
        sale_price = maybe_create_sale_price(sale_prices, beverage_id, name, date)

        invoice_item, _ = GrihedInvoiceItem.objects.update_or_create(
            quantity=int(quantity), name=name, total_price=total, invoice=invoice, beverage=beverage, purchase_price=grihed_price, sale_price=sale_price
        )
        invoice_item.save()

        if invoice_item.calculated_total_price != total:
            logger.error(f"Total price mismatch in {invoice_number} for {name}")

    return invoice


def get_shila_account_bookings() -> set[ShilaAccountBooking]:
    return set(ShilaAccountBooking.objects.all())
