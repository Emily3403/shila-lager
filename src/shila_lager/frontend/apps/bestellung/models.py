from __future__ import annotations

from decimal import Decimal

from django.db.models import Model, CharField, TextChoices, DecimalField, IntegerField, ForeignKey, CASCADE, OneToOneField


class BottleType(TextChoices):
    glass = "glass"
    plastic = "plastic"


class BeverageCrate(Model):
    class Meta:
        verbose_name_plural = "Beverage Crates"

    name = CharField(max_length=256, unique=True)
    grihed_id = CharField(max_length=64, primary_key=True)

    number_of_bottles = IntegerField(default=20)
    ml_in_each_bottle = IntegerField(default=500)

    price = DecimalField(max_digits=4, decimal_places=2)
    deposit = DecimalField(max_digits=4, decimal_places=2, default=4.5)
    selling_price_per_bottle = DecimalField(max_digits=4, decimal_places=2)

    bottle_type = CharField(max_length=64, choices=BottleType, default=BottleType.glass)

    inventory: CrateInventory

    def __str__(self) -> str:
        return self.name

    @property
    def total_price(self) -> Decimal:
        return self.price + self.deposit


class CrateInventory(Model):
    class Meta:
        verbose_name_plural = "Crate Inventories"

    crate = OneToOneField(BeverageCrate, on_delete=CASCADE, verbose_name="Beverage Crate", primary_key=True, related_name="inventory")
    current_stock = IntegerField()
    should_be_in_stock = IntegerField()

    def __str__(self):
        return f"{self.crate.name} Inventory"
