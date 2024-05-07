from __future__ import annotations

import re
import time
from datetime import datetime
from math import isclose
from pathlib import Path

import pytz
from pypdf import PdfReader

from shila_lager.frontend.apps.bestellung.models import BeverageCrate, SalePrice
from shila_lager.frontend.apps.rechnungen.crud import create_invoice
from shila_lager.frontend.apps.rechnungen.models import GrihedInvoice
from shila_lager.settings import manual_upload_dir

invoice_number_regex = re.compile(r"Rechnung-Nr:\s*(\d+)\s*–\s*(\d+)")
date_regex = re.compile(r"Liefertag:\s*(\d{2}\.\d{2}\.\d{4})")
total_price_regex = re.compile(r"Zahlbetrag:\s*(-?(?:\d*\.)?\d+,\d+) €")

# This is a horrendous regex, but it works for now. It is very unreadable and should be refactored.
# @formatter:off
item_regex = re.compile((
    r"\s*(\d+|####)\s+"  # Quantity (Menge)
    r"([A-Z]+ \d+)\s+"   # ID (ArtNr)
    r"([\w\W]*?)\s{2,}"  # Name (Artikelbezeichnung)
    r"(\d+(?:[/\w,]*)? x \d+(?:,\d+\w)?(?:[/\w,]*)?)\s+"  # Content (Inhalt)
    r"([\w\s]*?)\s{2,}"  # Packaging (Gebinde)
    r"\d+ %\s+"          # Tax rate (St-Satz)
    r"(-?\d+,\d+) €\s+"  # Deposit (Pfand)
    r"(-?\d+,\d+) €\s+"  # Price (Preis)
    r"(-?\d+,\d+) €\s+"  # Total (Summe in €)
))
# @formatter:on


def import_grihed_pdf(pdf_path: Path) -> GrihedInvoice | None:
    reader = PdfReader(pdf_path)
    pdf = "\n\n\n".join(page.extract_text(extraction_mode="layout") for page in reader.pages)

    invoice_numbers, _date, _total_price = invoice_number_regex.search(pdf), date_regex.search(pdf), total_price_regex.search(pdf)
    unparsed_items = item_regex.findall(pdf)
    if invoice_numbers is None or _date is None or _total_price is None or unparsed_items == []:
        return None

    invoice_number = invoice_numbers.group(1) + "-" + invoice_numbers.group(2)
    date = pytz.UTC.localize(datetime.strptime(_date.group(1), "%d.%m.%Y"))
    total_price = float(_total_price.group(1).replace(".", "_").replace(",", "."))

    invoice = create_invoice(invoice_number, date, total_price, unparsed_items)
    if not isclose(sum(item.calculated_total_price for item in invoice.items.all()), total_price):
        print(f"Total price mismatch in {pdf_path}")
        for item in invoice.items.all():
            print(f"{item.quantity}x {item.name} for {item.calculated_total_price}€")
        return None

    return invoice


def import_all_grihed_pdfs():
    # manual_upload_dir is the dir where the PDFs are stored.
    s = time.perf_counter()
    items = []
    for pdf_path in (manual_upload_dir / "Grihed").iterdir():
        items.append(import_grihed_pdf(pdf_path))

    print(f"{time.perf_counter() - s:3f}s")


def import_sale_prices():

    beverage_crates: list[BeverageCrate] = sorted(BeverageCrate.objects.all(), key=lambda it: it.name)

    for crate in beverage_crates:
        if (price := price_translation.get((crate.id, crate.name))) is not None:
            sale_price, _ = SalePrice.objects.update_or_create(crate=crate, price=price, valid_from=pytz.UTC.localize(datetime.strptime("01.01.2023", "%d.%m.%Y")))
            sale_price.save()
        else:
            print(f"Missing price for {crate.id} {crate.name}")
