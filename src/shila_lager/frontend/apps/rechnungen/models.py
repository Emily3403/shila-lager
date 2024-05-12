from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db.models import Model, DecimalField, CharField, DateField, ForeignKey, IntegerField, RESTRICT, DateTimeField, TextChoices
from math import isclose

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

    def __str__(self) -> str:
        return f"InvoiceItem for {self.quantity}x {self.name}"


class ShilaTransactionPeers(TextChoices):
    # Getränke
    grihed = "GRIHED Service GmbH"
    team_getränke = "Team Getränke"

    # Sonstiges
    gepa = "GEPA MBH"
    dm = "DM-drogerie markt"
    hetzner = "Hetzner Online GmbH"

    sparkasse = "Berliner Sparkasse"
    tu_berlin = "TU Berlin"
    vpsl = "VPSL"

    # Natürliche Personen
    emily = "Emily Seebeck"
    lelle = "Leander Guelland"
    ille = "Ilja Behnke"
    jonas = "Jonas Pasche"
    jette = "Jette Eckel"
    helge = "Helge Kling"
    fabian = "Fabian Ruben"
    elias = "Elias Tretin"

    andere_personen = "Andere Personen"
    sonstiges = "Sonstiges"


class ShilaBookingKind(TextChoices):
    lastschrift = "Lastschrift"
    lastschrift_undo = "LS Wiedergutschrift"
    dauerauftrag = "Dauerauftrag"
    rechnung = "Rechnung"
    kartenzahlung = "Kartenzahlung"
    onlineuberweisung = "Online-Uberweisung"

    gutschrift = "Gutschrift"
    bargeldeinzahlung = "Bargeldeinzahlung"

    abschluss = "Abschluss"
    entgeltabschluss = "Entgeldabschluss"

    @classmethod
    def from_str(cls, kind: str) -> ShilaBookingKind:
        match kind.strip().lower():
            case "lastschrift" | "einmal lastschrift" | "folgelastschrift" | "erstlastschrift":
                return cls.lastschrift
            case "ls wiedergutschrift":
                return cls.lastschrift_undo
            case "dauerauftrag":
                return cls.dauerauftrag
            case "rechnung":
                return cls.rechnung
            case "kartenzahlung":
                return cls.kartenzahlung
            case "online-ueberweisung" | "einzelueberweisung":
                return cls.onlineuberweisung

            case "gutschr. ueberweisung" | "echtzeit-gutschrift":
                return cls.gutschrift
            case "bargeldeinzahlung" | "bargeldeinzahlung sb":
                return cls.bargeldeinzahlung

            case "abschluss":
                return cls.abschluss
            case "entgeltabschluss":
                return cls.entgeltabschluss

            case _:
                raise ValueError(f"Unknown booking kind {kind}")


class ShilaAccountBooking(Model):
    class Meta:
        verbose_name_plural = "Shila Account Bookings"

    booking_date = DateField()
    value_date = DateField()
    kind = CharField(max_length=64, choices=ShilaBookingKind)
    description = CharField(max_length=256)

    creditor_id = CharField(max_length=64, null=True)
    mandate_reference = CharField(max_length=64, null=True)
    customer_reference = CharField(max_length=64, null=True)
    collector_reference = CharField(max_length=64, null=True)

    original_amount = DecimalField(max_digits=16, decimal_places=2, null=True)
    chargeback_amount = DecimalField(max_digits=16, decimal_places=2, null=True)
    beneficiary_or_payer = CharField(max_length=64, choices=ShilaTransactionPeers, null=True)
    iban = CharField(max_length=64)
    bic = CharField(max_length=64)

    amount = DecimalField(max_digits=16, decimal_places=2)
    currency = CharField(max_length=16)
    additional_info = CharField(max_length=256)

    def __str__(self) -> str:
        return f"Booking {self.description} on {self.booking_date}"

    def __hash__(self) -> int:
        return hash(self.booking_date) ^ hash(self.value_date) ^ hash(self.description) ^ hash(round(self.amount, 2))

    def __eq__(self, other: ShilaAccountBooking | Any) -> bool:
        if not isinstance(other, ShilaAccountBooking):
            return False

        return (
            self.booking_date == other.booking_date and
            self.value_date == other.value_date and
            self.kind == other.kind and
            self.description == other.description and
            self.creditor_id == other.creditor_id and
            self.mandate_reference == other.mandate_reference and
            self.customer_reference == other.customer_reference and
            self.collector_reference == other.collector_reference and
            isclose(self.original_amount or -1, other.original_amount or -1) and
            isclose(self.chargeback_amount or -1, other.chargeback_amount or -1) and
            self.beneficiary_or_payer == other.beneficiary_or_payer and
            self.iban == other.iban and
            self.bic == other.bic and
            isclose(self.amount, other.amount) and
            self.currency == other.currency and
            self.additional_info == other.additional_info
        )
