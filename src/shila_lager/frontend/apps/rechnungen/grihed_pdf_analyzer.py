from __future__ import annotations

import pickle
import re
import time
from dataclasses import dataclass
from datetime import datetime
from math import isclose
from pathlib import Path

from pypdf import PdfReader

from shila_lager.settings import manual_upload_dir, working_dir_location


@dataclass
class GrihedInvoiceItem:
    quantity: int
    id: str
    name: str
    deposit: float
    price: float
    total: float

    @classmethod
    def from_regex(cls, regex_match: tuple[str, str, str, str, str, str]) -> GrihedInvoiceItem:
        return cls(
            quantity=int(regex_match[0] if regex_match[0] != "####" else 1),
            id=regex_match[1].replace(" ", ""),
            name=regex_match[2],
            deposit=float(regex_match[3].replace(".", "_").replace(",", ".")),
            price=float(regex_match[4].replace(".", "_").replace(",", ".")),
            total=float(regex_match[5].replace(".", "_").replace(",", "."))
        )


@dataclass
class GrihedInvoice:
    invoice_number: str
    date: datetime
    total_price: float
    items: list[GrihedInvoiceItem]

    @classmethod
    def load(cls, date: str) -> GrihedInvoice | None:
        try:
            with open(working_dir_location / "temp_saved_invoices" / f"{date}.pickle", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return None

    def save(self) -> None:
        with open(working_dir_location / "temp_saved_invoices" / f"{self.date.strftime('%Y-%m-%d')}.pickle", "wb") as f:
            pickle.dump(self, f)


invoice_number_regex = re.compile(r"Rechnung-Nr:\s*(\d+)\s*–\s*(\d+)")
date_regex = re.compile(r"Liefertag:\s*(\d{2}\.\d{2}\.\d{4})")
total_price_regex = re.compile(r"Zahlbetrag:\s*(-?(?:\d*\.)?\d+,\d+) €")

# This is a horrendous regex, but it works for now. It is very unreadable and should be refactored.
# @formatter:off
item_regex = re.compile((
    r"\s*(\d+|####)\s+"  # Quantity (Menge)
    r"([A-Z]+ \d+)\s+"   # ID (ArtNr)
    r"([\w\W]*?)\s{2,}"  # Name (Artikelbezeichnung)
    r"\d+(?:[/\w,]*)? x \d+(?:,\d+\w)?(?:[/\w,]*)?\s+"  # Content (Inhalt)
    r"[\w\s]*\s{2,}"     # Packaging (Gebinde)
    r"\d+ %\s+"          # Tax rate (St-Satz)
    r"(-?\d+,\d+) €\s+"  # Deposit (Pfand)
    r"(-?\d+,\d+) €\s+"  # Price (Preis)
    r"(-?\d+,\d+) €\s+"  # Total (Summe in €)
))
# @formatter:on


def analyze_grihed_pdf(pdf_path: Path) -> GrihedInvoice | None:
    if (it := GrihedInvoice.load(pdf_path.name.replace(".pdf", ""))) is not None:
        return it

    reader = PdfReader(pdf_path)
    pdf = "\n\n\n".join(page.extract_text(extraction_mode="layout") for page in reader.pages)

    invoice_numbers, _date, _total_price = invoice_number_regex.search(pdf), date_regex.search(pdf), total_price_regex.search(pdf)
    unparsed_items = item_regex.findall(pdf)
    if invoice_numbers is None or _date is None or _total_price is None or unparsed_items == []:
        return None

    invoice_number = invoice_numbers.group(1) + "-" + invoice_numbers.group(2)
    date = datetime.strptime(_date.group(1), "%d.%m.%Y")
    total_price = float(_total_price.group(1).replace(".", "_").replace(",", "."))

    items = [GrihedInvoiceItem.from_regex(item) for item in unparsed_items]

    # Sanity check: Do the total prices of the items add up to the total price of the invoice?
    if not isclose(sum(item.total for item in items), total_price):
        print("Error: Total price of items does not match total price of invoice.")
        return None

    return GrihedInvoice(invoice_number, date, total_price, items)


def analyze_all_grihed_pdfs():
    # manual_upload_dir is the dir where the PDFs are stored.
    s = time.perf_counter()
    items = []
    for pdf_path in (manual_upload_dir / "Grihed").iterdir():
        items.append(analyze_grihed_pdf(pdf_path))

    for item in items:
        item.save()

    print(f"{time.perf_counter() - s:3f}s")

    ids = set()
    for item in items:
        for i in item.items:
            ids.add(i.id)

    print("\n".join(f"{it[0]} {it[1:]}" for it in sorted(ids)))