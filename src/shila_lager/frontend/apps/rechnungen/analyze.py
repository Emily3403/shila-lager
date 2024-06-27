from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import DefaultDict

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, BottleType
from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount, AnalyzedBeverageCrate
from shila_lager.settings import empty_crate_price, logger
from shila_lager.utils import filter_by_date

beverage_id = str
deposit_category = Decimal


def analyze_beverage_crates(beverages: dict[str, BeverageCrate], start: datetime | None = None, end: datetime | None = None, inventory: tuple[ShilaInventoryCount, ShilaInventoryCount] | None = None) -> set[AnalyzedBeverageCrate]:
    num_ordered: DefaultDict[beverage_id, Decimal] = defaultdict(Decimal)
    num_returned: DefaultDict[deposit_category, Decimal] = defaultdict(Decimal)

    payed_deposits: DefaultDict[deposit_category, Decimal] = defaultdict(Decimal)

    beverage_id_to_deposit_category: dict[beverage_id, deposit_category] = {}

    total_payed: DefaultDict[beverage_id, Decimal] = defaultdict(Decimal)

    # This first loop takes all the invoices into account
    for id, beverage in beverages.items():
        category = beverage._current_purchase_price().deposit
        bottle_type = BottleType(beverage.bottle_type)

        if bottle_type.is_bottle:
            # Don't add Crate Returns to beverage IDs
            beverage_id_to_deposit_category[id] = beverage._current_purchase_price().deposit

        for invoice_item in beverage.invoice_items.all():
            if not filter_by_date(invoice_item.invoice.date, start, end):
                continue

            if bottle_type == BottleType.crate_return:
                category = -beverage._current_purchase_price().price  # Crate returns don't have deposits but rather a negative price
                num_returned[category] += invoice_item.quantity
                continue

            assert not id.startswith("L")
            if not bottle_type.is_bottle or category == 0:
                continue

            num_ordered[id] += invoice_item.quantity
            payed_deposits[category] += invoice_item.quantity

    return_values = calculate_return_values(num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category)
    analyzed_beverage_crates = set()

    # Now add the inventory to the mix
    num_sold: DefaultDict[beverage_id, Decimal] = defaultdict(Decimal)
    old_inventory, new_inventory = inventory or (None, None)

    old_inventory_counts: dict[beverage_id, Decimal] = {it.crate.id: it.count for it in (old_inventory.details.all())}
    new_inventory_counts: dict[beverage_id, Decimal] = {it.crate.id: it.count for it in new_inventory.details.all()}


    for id, beverage in beverages.items():
        if inventory is not None:
            old_inventory, new_inventory = inventory
            num_sold[id] = old_inventory
        else:
            num_sold[id] = num_ordered[id]

    for id, beverage in beverages.items():
        total_return_value = return_values[id]

        analyzed_beverage_crates.add(AnalyzedBeverageCrate(
            beverage,
            start,
            end,

            num_ordered[id],
            num_returned_per_beverage(num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category, id),
            num_sold[id],

            total_payed,
            total_profit,
            total_theoretical_profit,
        ))

    return analyzed_beverage_crates


def calculate_return_values(
    num_ordered: dict[beverage_id, Decimal],
    num_returned: dict[deposit_category, Decimal],
    payed_deposits: dict[deposit_category, Decimal],
    beverage_id_to_deposit_category: dict[beverage_id, deposit_category]  # This should contain every beverage id
) -> dict[beverage_id, Decimal]:
    """
    This function operates under the fundamental assumption that deposit values do not change.
    This might bite me in the ass in the future, but for now this is a good tradeoff between complexity and future-proofness

    return: dict from `beverage_id` to `total_return_value` and `total_returned`
    """

    zero = Decimal(0)
    _num_returned_per_beverage = partial(num_returned_per_beverage, num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category)

    def num_not_returned(b: beverage_id) -> Decimal:
        return max(num_ordered.get(b, zero) - _num_returned_per_beverage(b), zero)

    total_not_returned = sum(num_not_returned(b) for b in beverage_id_to_deposit_category)

    def value_for_full_crates_returned(b: beverage_id) -> Decimal:
        return _num_returned_per_beverage(b) * beverage_id_to_deposit_category[b]

    def value_for_empty_crates(b: beverage_id) -> Decimal:
        return num_not_returned(b) / total_not_returned * empty_crate_price

    return sanity_check_return_values(
        {b: value_for_full_crates_returned(b) + value_for_empty_crates(b) for b, category in beverage_id_to_deposit_category.items()},
        num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category
    )


def num_returned_per_beverage(
    num_ordered: dict[beverage_id, Decimal],
    num_returned: dict[deposit_category, Decimal],
    payed_deposits: dict[deposit_category, Decimal],
    beverage_id_to_deposit_category: dict[beverage_id, deposit_category],
    b: beverage_id
) -> Decimal:
    zero = Decimal(0)
    category = beverage_id_to_deposit_category[b]

    n, p = num_ordered.get(b, zero), payed_deposits.get(category, zero)
    if n == zero or p == zero:
        return zero

    return n / p * num_returned.get(category, zero)


def sanity_check_return_values(
    return_values: dict[beverage_id, Decimal],
    num_ordered: dict[beverage_id, Decimal],
    num_returned: dict[deposit_category, Decimal],
    payed_deposits: dict[deposit_category, Decimal],
    beverage_id_to_deposit_category: dict[beverage_id, deposit_category]
) -> dict[beverage_id, Decimal]:
    for id, category in beverage_id_to_deposit_category.items():
        total_return_value = return_values[id]
        if category == 0:
            continue

        if total_return_value < 0:
            logger.error(f"Negative return value for {id}: {return_values[id]}")

        # TODO: Make more and fix these sanity checks
        # if num_ordered[id] > returned_deposits[category] and num_ordered[id] != 0:
        #     logger.error(f"More crates returned than ordered: {returned_deposits[category]} < {num_ordered[id]}")
        #
        # if payed_deposits[category] < returned_deposits[category]:
        #     logger.error(f"More deposits payed than returned: {payed_deposits[category]} < {returned_deposits[category]}")
        #
        # if return_values[id] > num_ordered[id] * category:
        #     logger.error(f"Return value for {id} too high: {return_values[id]} > {num_ordered[id] * category}")

    return return_values
