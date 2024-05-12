from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.db.models import QuerySet

from shila_lager.frontend.apps.bestellung.models import GrihedPrice, BeverageCrate, BottleType, SalePrice


def get_beverage_crates() -> dict[str, BeverageCrate]:
    beverages = BeverageCrate.objects.all()
    return {beverage.id: beverage for beverage in beverages}


def create_beverage_crate(id: str, name: str, content: str, bottle_type: BottleType) -> BeverageCrate:
    beverage = BeverageCrate(id=id, name=name, content=content, bottle_type=bottle_type)
    beverage.save()
    return beverage


def get_sorted_grihed_prices() -> defaultdict[str, list[GrihedPrice]]:
    _prices: QuerySet[GrihedPrice] = GrihedPrice.objects.all()
    all_prices = defaultdict(lambda: [])
    for price in _prices:
        all_prices[price.crate_id].append(price)

    for prices in all_prices.values():
        prices.sort(key=lambda it: it.valid_from, reverse=True)

    return all_prices


def get_sorted_sale_prices() -> defaultdict[str, list[SalePrice]]:
    _prices: QuerySet[SalePrice] = SalePrice.objects.all()
    all_prices = defaultdict(lambda: [])
    for price in _prices:
        all_prices[price.crate_id].append(price)

    for prices in all_prices.values():
        prices.sort(key=lambda it: it.valid_from, reverse=True)

    return all_prices


def create_grihed_price(crate_id: str, price: Decimal, deposit: Decimal, valid_from: datetime) -> GrihedPrice:
    grihed_price = GrihedPrice(crate_id=crate_id, price=price, deposit=deposit, valid_from=valid_from)
    grihed_price.save()
    return grihed_price
