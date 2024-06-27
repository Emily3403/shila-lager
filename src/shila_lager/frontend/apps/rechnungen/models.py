from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Never

from django.db.models import Model, DecimalField, CharField, DateField, ForeignKey, IntegerField, RESTRICT, TextChoices, ManyToManyField, CASCADE, JSONField, DateTimeField
from math import isclose

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, GrihedPrice, SalePrice
from shila_lager.settings import logger, grihed_temp_str

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


# Create your models here.
class GrihedInvoice(Model):
    class Meta:
        verbose_name_plural = "Grihed Invoices"

    invoice_number = CharField(max_length=64, primary_key=True)
    date = DateField()
    total_price = DecimalField(max_digits=16, decimal_places=2)

    items: RelatedManager[GrihedInvoiceItem]

    def __str__(self) -> str:
        return f"{self.invoice_number} from {self.date}"

    def __repr__(self) -> str:
        return self.__str__()


class GrihedInvoiceItem(Model):
    class Meta:
        verbose_name_plural = "Grihed Invoice Items"
        unique_together = ("invoice", "beverage")

    quantity = IntegerField()
    total_price = DecimalField(max_digits=16, decimal_places=2)

    invoice = ForeignKey(GrihedInvoice, on_delete=RESTRICT, related_name="items")
    beverage = ForeignKey(BeverageCrate, on_delete=RESTRICT, related_name="invoice_items")
    purchase_price = ForeignKey(GrihedPrice, on_delete=RESTRICT, related_name="invoice_items")
    sale_price = ForeignKey(SalePrice, on_delete=RESTRICT, related_name="invoice_items")

    @property
    def calculated_total_price(self) -> Decimal:
        return (self.purchase_price.price + self.purchase_price.deposit) * self.quantity

    def __str__(self) -> str:
        return f"InvoiceItem for {self.quantity}x {self.beverage.name} ({self.beverage.id})"


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


class ShilaBookingCategory(Enum):
    beverages = "Getränke"
    gepa = "GEPA"
    bringmeister = "Bringmeister"
    chocholate = "Schokolade"
    dm = "DM"
    hosting = "Hosting"
    sparkasse_fee = "Sparkasse Gebühr"
    mv_ausgaben = "MV Haushalt"
    other = "Sonstige"
    sparkasse_income = "Sparkasse Einzahlung"


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

    @property
    def is_temp(self) -> bool:
        return self.beneficiary_or_payer == "GRIHED Service GmbH" and grihed_temp_str in self.description

    def actual_booking_date(self) -> date:
        if self.beneficiary_or_payer != "GRIHED Service GmbH":
            return self.booking_date

        matched_date = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", self.description)
        if matched_date is None:
            logger.error(f"Could not find a date in {self.description}")
            return self.booking_date

        return date(*map(int, reversed(matched_date.groups())))

    @property
    def category(self) -> ShilaBookingCategory:
        match self.beneficiary_or_payer:
            case "GRIHED Service GmbH" | "Team Getraenke Lieferdienste TGL GmbH":
                return ShilaBookingCategory.beverages
            case "GEPA MBH" | "GEPA mbH" | "GEPA mbh" | "Cafe Libertad Kollektiv eG":
                return ShilaBookingCategory.gepa
            case "PLANT-FOR-THE-PLANET" | "THE GOOD SHOP by Stripe via PPRO":
                return ShilaBookingCategory.chocholate
            case "DM-drogerie markt":
                return ShilaBookingCategory.dm
            case "Jonas Pasche" | "Hetzner Online GmbH":
                return ShilaBookingCategory.hosting
            case _:
                if self.iban == "0000000000" and (
                    "Entgeltabrechnung siehe Anlage " in self.description or "Rechnung Berliner Sparkasse Entgelt" in self.description
                ):
                    return ShilaBookingCategory.sparkasse_fee

                if self.description.startswith("SB-EINZAHLUNG"):
                    return ShilaBookingCategory.sparkasse_income
                if "Flaschenpost" in self.description or self.beneficiary_or_payer is not None and "flaschenpost" in self.beneficiary_or_payer:
                    return ShilaBookingCategory.beverages
                if "Bringmeister" in self.description or "Metro" in self.description:
                    return ShilaBookingCategory.bringmeister

                if "MV Ausgabe" in self.description:
                    return ShilaBookingCategory.mv_ausgaben

                return ShilaBookingCategory.other


class ShilaInventoryCount(Model):
    class Meta:
        verbose_name_plural = "Shila Inventory Counts"

    date = DateTimeField(primary_key=True)
    crates: ManyToManyField[BeverageCrate, Never] = ManyToManyField(BeverageCrate, related_name="inventory_counts", through="ShilaInventoryCountDetail")
    other_monetary_value = DecimalField(max_digits=16, decimal_places=2)
    money_in_safe = DecimalField(max_digits=16, decimal_places=2)
    extra_expenses = JSONField()

    details: RelatedManager[ShilaInventoryCountDetail]

    def __str__(self) -> str:
        return f"Inventory Count {self.date}"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.date)

    def __eq__(self, other: ShilaInventoryCount | Any) -> bool:
        if not isinstance(other, ShilaInventoryCount):
            return False

        return self.date == other.date


class ShilaInventoryCountDetail(Model):
    class Meta:
        unique_together = ('date', 'crate')

    date = ForeignKey(ShilaInventoryCount, on_delete=CASCADE, related_name="details")
    crate = ForeignKey(BeverageCrate, on_delete=CASCADE)
    count = DecimalField(max_digits=16, decimal_places=4)

    def __str__(self) -> str:
        return f"Inventory Count Detail for {self.crate.name} on {self.date.date}"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class AnalyzedBeverageCrate:
    beverage: BeverageCrate
    start: datetime | None
    end: datetime | None

    # Number of crates
    num_ordered: Decimal
    num_returned: Decimal
    num_sold: Decimal

    # Amounts
    total_payed: Decimal
    total_profit: Decimal
    total_profit_without_deposits: Decimal
    total_profit_with_payed_but_not_returned_deposits: Decimal
    total_deposit_returned: Decimal

    def __str__(self) -> str:
        return f"{self.beverage.name}: {self.num_ordered:.2f}× ordered, {self.num_sold:.2f}× sold: {self.total_profit:.2f}€ profit"

    def __repr__(self) -> str:
        return self.__str__()
