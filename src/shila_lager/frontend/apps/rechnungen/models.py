from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Model, DecimalField, CharField, DateField, ForeignKey, IntegerField, RESTRICT, DateTimeField

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, GrihedPrice, SalePrice

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


# Create your models here.
class GrihedInvoice(Model):
    class Meta:
        verbose_name_plural = "Grihed Invoices"

    invoice_number = CharField(max_length=64, primary_key=True)
    date = DateTimeField()
    total_price = DecimalField(max_digits=16, decimal_places=2)

    items: RelatedManager[GrihedInvoiceItem]


class GrihedInvoiceItem(Model):
    class Meta:
        verbose_name_plural = "Grihed Invoice Items"
        unique_together = ("invoice", "beverage")

    quantity = IntegerField()
    name = CharField(max_length=256)
    total_price = DecimalField(max_digits=16, decimal_places=2)

    invoice = ForeignKey(GrihedInvoice, on_delete=RESTRICT, related_name="items")
    beverage = ForeignKey(BeverageCrate, on_delete=RESTRICT, related_name="invoice_items")
    purchase_price = ForeignKey(GrihedPrice, on_delete=RESTRICT, related_name="invoice_items")
    sale_price = ForeignKey(SalePrice, on_delete=RESTRICT, related_name="invoice_items")

    @property
    def calculated_total_price(self) -> Decimal:
        return (self.purchase_price.price + self.purchase_price.deposit) * self.quantity

    def __str__(self):
        return f"InvoiceItem for {self.quantity}x {self.name}"
