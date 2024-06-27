from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Model, CharField, TextChoices, DecimalField, CASCADE, ForeignKey, DateTimeField
from django_stubs_ext.db.models.manager import RelatedManager

if TYPE_CHECKING:
    from shila_lager.frontend.apps.rechnungen.models import GrihedInvoiceItem, ShilaInventoryCount


class BottleType(TextChoices):
    glass_bottle = "glass"
    single_glass_bottle = "single_glass_bottle"
    pet_plastic = "plastic"
    tetra_pack = "tetra_pack"
    package = "package"

    crate_return = "crate_return"
    bonus_credit = "bonus_credit"
    other_charges = "other_charges"
    unknown = "unknown"

    @property
    def is_bottle(self) -> bool:
        return self not in {BottleType.crate_return, BottleType.bonus_credit, BottleType.other_charges, BottleType.unknown}

    @classmethod
    def from_str(cls, bottle_type: str, crate_id: str) -> BottleType:
        match bottle_type.strip():
            case "Flaschen":
                return cls.glass_bottle
            case "Flasche":
                return cls.single_glass_bottle
            case "Pet Flaschen" | "Pet Einweg F":
                return cls.pet_plastic
            case "Tetra Pack":
                return cls.tetra_pack
            case "Packung":
                return cls.package

            case "einach":
                return cls.bonus_credit
            case "Kasten" | "Kasten ohne":
                return cls.crate_return

            case "":
                if crate_id.startswith("L"):
                    return cls.crate_return

                return cls.unknown
            case _:
                if crate_id == "A0101":
                    return cls.other_charges
                print(crate_id, bottle_type)
                assert False


class BeverageCrate(Model):
    class Meta:
        verbose_name_plural = "Beverage Crates"
        unique_together = "name", "content"

    id = CharField(max_length=64, primary_key=True)
    name = CharField(max_length=256)

    content = CharField(max_length=64)
    bottle_type = CharField(max_length=64, choices=BottleType)

    grihed_prices: RelatedManager[GrihedPrice]
    sale_prices: RelatedManager[SalePrice]
    invoice_items: RelatedManager[GrihedInvoiceItem]
    inventory_counts: RelatedManager[ShilaInventoryCount]

    def __str__(self) -> str:
        return f"{self.id} {self.name}"

    def current_sale_price(self) -> Decimal:
        return self._current_sale_price().price

    def current_purchase_price(self) -> Decimal:
        return self._current_purchase_price().price

    def _current_sale_price(self) -> SalePrice:
        it = self.sale_prices.order_by("valid_from").last()
        assert it is not None
        return it

    def _current_purchase_price(self) -> GrihedPrice:
        it = self.grihed_prices.order_by("valid_from").last()
        assert it is not None
        return it


class SalePrice(Model):
    class Meta:
        verbose_name_plural = "Sale Prices"
        unique_together = "crate_id", "valid_from"

    crate = ForeignKey(BeverageCrate, on_delete=CASCADE, verbose_name="Beverage Crate ID", related_name="sale_prices")
    price = DecimalField(max_digits=4, decimal_places=2)
    valid_from = DateTimeField()

    crate_id: str

    def __str__(self) -> str:
        return f"{self.crate_id} Sale Price"


class GrihedPrice(Model):
    class Meta:
        verbose_name_plural = "Grihed Prices"
        unique_together = "crate_id", "valid_from"

    crate = ForeignKey(BeverageCrate, on_delete=CASCADE, verbose_name="Beverage Crate ID", related_name="grihed_prices")
    price = DecimalField(max_digits=16, decimal_places=10)  # Some prices (Soli) are fractions that have to be in a very high resolution, else they will not match the expected price
    deposit = DecimalField(max_digits=8, decimal_places=2)
    valid_from = DateTimeField()

    crate_id: str

    def __str__(self) -> str:
        return f"{self.crate_id} Grihed Price"
