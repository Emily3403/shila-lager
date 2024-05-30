from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Model, CharField, TextChoices, DecimalField, IntegerField, CASCADE, OneToOneField, ForeignKey, DateTimeField
from django_stubs_ext.db.models.manager import RelatedManager

if TYPE_CHECKING:
    from shila_lager.frontend.apps.rechnungen.models import GrihedInvoiceItem


class BottleType(TextChoices):
    glass_bottle = "glass"
    single_glass_bottle = "single_glass_bottle"
    pet_plastic = "plastic"
    tetra_pack = "tetra_pack"
    package = "package"

    crate_return = "crate_return"
    bonus_credit = "bonus_credit"
    unknown = "unknown"

    @classmethod
    def from_str(cls, bottle_type: str, crate_id: str) -> BottleType:
        match bottle_type.strip():
            case "Flaschen":
                return cls.glass_bottle
            case "Flasche":
                return cls.single_glass_bottle
            case "Pet Flaschen":
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
                    return cls.crate_return
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
    inventory: RelatedManager[CrateInventory]
    invoice_items: RelatedManager[GrihedInvoiceItem]

    def __str__(self) -> str:
        return f"{self.id} {self.name}"

    def current_sale_price(self) -> Decimal:
        it = self.sale_prices.order_by("valid_from").last()
        assert it is not None
        return it.price

    def current_purchase_price(self) -> Decimal:
        it = self.grihed_prices.order_by("valid_from").last()
        assert it is not None
        return it.price


class CrateInventory(Model):
    class Meta:
        verbose_name_plural = "Crate Inventories"

    crate = OneToOneField(BeverageCrate, on_delete=CASCADE, verbose_name="Beverage Crate", primary_key=True, related_name="inventory")
    current_stock = IntegerField()
    should_be_in_stock = IntegerField()

    def __str__(self) -> str:
        return f"{self.crate.name} Inventory"


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
    price = DecimalField(max_digits=8, decimal_places=2)
    deposit = DecimalField(max_digits=8, decimal_places=2)
    valid_from = DateTimeField()

    crate_id: str

    def __str__(self) -> str:
        return f"{self.crate_id} Grihed Price"
