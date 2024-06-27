from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import DefaultDict

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, BottleType
from shila_lager.frontend.apps.rechnungen.beverage_facts import collapse_categories
from shila_lager.frontend.apps.rechnungen.models import ShilaInventoryCount, AnalyzedBeverageCrate, GrihedInvoiceItem
from shila_lager.settings import empty_crate_price, logger
from shila_lager.utils import filter_by_date, zero, BeverageID, DepositCategory, reverse_dict

pfand_scale_factor = Decimal("0.7")


def analyze_beverage_crates(beverages: dict[str, BeverageCrate], start: datetime | None = None, end: datetime | None = None, inventory: tuple[ShilaInventoryCount, ShilaInventoryCount] | None = None) -> dict[BeverageID, AnalyzedBeverageCrate]:
    num_ordered: DefaultDict[BeverageID, list[GrihedInvoiceItem]] = defaultdict(list)
    num_returned: DefaultDict[DepositCategory, Decimal] = defaultdict(Decimal)
    payed_deposits: DefaultDict[DepositCategory, Decimal] = defaultdict(Decimal)
    beverage_id_to_deposit_category: dict[BeverageID, DepositCategory] = {}

    # This first loop takes all the invoices into account
    for id, beverage in beverages.items():
        id = collapse_beverage_id(id)
        category = beverage._current_purchase_price().deposit
        bottle_type = BottleType(beverage.bottle_type)

        if bottle_type.is_bottle:
            # Only add actual crates to the beverage ids
            beverage_id_to_deposit_category[id] = beverage._current_purchase_price().deposit

        for invoice_item in beverage.invoice_items.all():
            if not filter_by_date(invoice_item.invoice.date, start, end):
                continue

            if bottle_type == BottleType.crate_return:
                # Crate returns don't have deposits but rather a negative price
                category = -beverage._current_purchase_price().price
                num_returned[category] += invoice_item.quantity
                continue

            assert not id.startswith("L") and not id.startswith("R")
            if not bottle_type.is_bottle:
                # Don't take into account non bottles
                continue

            # TODO: Transform the ID from sekt or wein
            num_ordered[id].append(invoice_item)
            payed_deposits[category] += invoice_item.quantity

    return_values = calculate_return_values(num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category)
    num_sold = calculate_num_sold(inventory, num_ordered, beverages)

    analyzed_beverage_crates = {}
    for id, beverage in beverages.items():
        bottle_type = BottleType(beverage.bottle_type)
        if not bottle_type.is_bottle or bottle_type == BottleType.crate_return:
            continue

        ordered = num_ordered[id]
        if len(ordered) == 0:
            # TODO: Refactor this into a class which checks all GrihedPrices of a BeverageCrate and selects the appropriate one, depending on the date
            average_purchase_price_per_crate = beverage.current_purchase_price()
            average_deposit_per_crate = beverage._current_purchase_price().deposit
        else:
            average_purchase_price_per_crate = Decimal(sum(item.purchase_price.price for item in ordered) / len(ordered))
            average_deposit_per_crate = Decimal(sum(item.purchase_price.deposit for item in ordered) / len(ordered))

        total_payed = num_sold[id] * (average_purchase_price_per_crate + average_deposit_per_crate)
        total_deposit_returned = return_values.get(id, zero)
        total_profit = num_sold[id] * beverage.current_sale_price() - total_payed + total_deposit_returned
        total_profit_without_deposits = num_sold[id] * (beverage.current_sale_price() - average_purchase_price_per_crate)
        total_profit_with_payed_but_not_returned_deposits = num_sold[id] * beverage.current_sale_price() - total_payed + num_sold[id] * average_deposit_per_crate * pfand_scale_factor

        analyzed_beverage_crates[id] = AnalyzedBeverageCrate(
            beverage,
            start,
            end,

            num_ordered=get_actual_num_ordered(num_ordered, id),
            num_returned=num_returned_per_beverage(num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category, id),
            num_sold=num_sold[id],

            total_payed=total_payed,
            total_profit=total_profit,
            total_profit_without_deposits=total_profit_without_deposits,
            total_profit_with_payed_but_not_returned_deposits=total_profit_with_payed_but_not_returned_deposits,
            total_deposit_returned=total_deposit_returned,
        )

    return analyzed_beverage_crates


def calculate_return_values(
    num_ordered: dict[BeverageID, list[GrihedInvoiceItem]],
    num_returned: dict[DepositCategory, Decimal],
    payed_deposits: dict[DepositCategory, Decimal],
    beverage_id_to_deposit_category: dict[BeverageID, DepositCategory]  # This should contain every beverage id
) -> dict[BeverageID, Decimal]:
    """
    This function operates under the fundamental assumption that deposit values do not change.
    This might bite me in the ass in the future, but for now this is a good tradeoff between complexity and future-proofness

    return: dict from `BeverageID` to `total_return_value` and `total_returned`
    """

    # TODO: It might be better to calculate this based on `num_sold` rather than `num_ordered`

    _num_returned_per_beverage = partial(num_returned_per_beverage, num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category)

    def num_not_returned(b: BeverageID) -> Decimal:
        return max(get_actual_num_ordered(num_ordered, b) - _num_returned_per_beverage(b), zero)

    total_not_returned = sum(num_not_returned(b) for b in beverage_id_to_deposit_category)

    def value_for_full_crates_returned(b: BeverageID) -> Decimal:
        return _num_returned_per_beverage(b) * beverage_id_to_deposit_category[b]

    def value_for_empty_crates(b: BeverageID) -> Decimal:
        not_returned = num_not_returned(b)
        if not_returned == zero or total_not_returned == zero:
            return zero

        return not_returned / total_not_returned * empty_crate_price

    return sanity_check_return_values(
        {b: value_for_full_crates_returned(b) + value_for_empty_crates(b) for b, category in beverage_id_to_deposit_category.items()},
        num_ordered, num_returned, payed_deposits, beverage_id_to_deposit_category
    )


def num_returned_per_beverage(
    num_ordered: dict[BeverageID, list[GrihedInvoiceItem]],
    num_returned: dict[DepositCategory, Decimal],
    payed_deposits: dict[DepositCategory, Decimal],
    beverage_id_to_deposit_category: dict[BeverageID, DepositCategory],
    b: BeverageID
) -> Decimal:
    category = beverage_id_to_deposit_category.get(b)
    if category is None:
        return zero

    n, p = get_actual_num_ordered(num_ordered, b), payed_deposits.get(category, zero)
    if n == zero or p == zero:
        return zero

    return n / p * num_returned.get(category, zero)


def get_actual_num_ordered(num_ordered: dict[BeverageID, list[GrihedInvoiceItem]], b: BeverageID) -> Decimal:
    return Decimal(sum(item.quantity for item in num_ordered.get(b, [])))


def sanity_check_return_values(
    return_values: dict[BeverageID, Decimal],
    num_ordered: dict[BeverageID, list[GrihedInvoiceItem]],
    num_returned: dict[DepositCategory, Decimal],
    payed_deposits: dict[DepositCategory, Decimal],
    beverage_id_to_deposit_category: dict[BeverageID, DepositCategory]
) -> dict[BeverageID, Decimal]:
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


def calculate_num_sold(
    inventory: tuple[ShilaInventoryCount, ShilaInventoryCount] | None,
    num_ordered: DefaultDict[BeverageID, list[GrihedInvoiceItem]],
    beverages: dict[str, BeverageCrate]
) -> dict[BeverageID, Decimal]:
    num_sold = {}
    old, new = inventory or (None, None)

    if old is not None and new is not None:
        old_inventory = {it.crate.id: it.count for it in old.details.all()}
        new_inventory = {it.crate.id: it.count for it in new.details.all()}
    else:
        old_inventory, new_inventory = {}, {}

    for id, beverage in beverages.items():
        old_quantity = old_inventory.get(id, zero)
        new_quantity = new_inventory.get(id, zero)

        num_sold[id] = old_quantity - new_quantity + get_actual_num_ordered(num_ordered, id)

    return num_sold


reverse_collapse_categories = reverse_dict(collapse_categories)
def collapse_beverage_id(id: BeverageID) -> BeverageID:
    return reverse_collapse_categories.get(id, id)
