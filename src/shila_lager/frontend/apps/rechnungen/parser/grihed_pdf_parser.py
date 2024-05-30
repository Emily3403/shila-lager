from __future__ import annotations

import re
import time
from datetime import datetime
from math import isclose
from pathlib import Path

import pytz
from pypdf import PdfReader

from shila_lager.frontend.apps.rechnungen.crud import create_invoice
from shila_lager.frontend.apps.rechnungen.models import GrihedInvoice
from shila_lager.settings import manual_upload_dir, logger
from shila_lager.utils import german_price_to_decimal

invoice_number_regex = re.compile(r"Rechnung-Nr:\s*(\d+)\s*–\s*(\d+)")
date_regex = re.compile(r"Liefertag:\s*(\d{2}\.\d{2}\.\d{4})")
total_price_regex = re.compile(r"(?:Zahlbetrag|Gutschriftsbetrag):\s*(-?(?:\d*\.)?\d+,\d+) €")

# This is a okay-ish regex for parsing the items from the PDF. It gets the job done and is not too unreadable.
# @formatter:off
item_regex = re.compile((
    r"\s*(\d+|####)\s+"  # Quantity (Menge)
    r"([A-Z]+ \d+)\s+"   # ID (ArtNr)
    r"([\w\W]*?)\s{2,}"  # Name (Artikelbezeichnung)
    r"(\d+(?:[/\w,]*)? x \d+(?:,\d+\w)?(?:[/\w,]*)?|einfach)\s+"  # Content (Inhalt)
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
        logger.error(f"Could not parse PDF {pdf_path}")
        return None

    invoice_number = invoice_numbers.group(1) + "-" + invoice_numbers.group(2)
    date = pytz.UTC.localize(datetime.strptime(_date.group(1), "%d.%m.%Y"))
    total_price = german_price_to_decimal(_total_price.group(1))
    if total_price is None:
        logger.error(f"Total price could not be parsed in {pdf_path}")
        return None

    invoice = create_invoice(invoice_number, date, total_price, unparsed_items)
    if not isclose(sum(item.calculated_total_price for item in invoice.items.all()), total_price):
        logger.error(f"Total price mismatch in {pdf_path}")
        for item in invoice.items.all():
            logger.error(f"{item.quantity}x {item.beverage.name} for {item.calculated_total_price}€")
        return None

    return invoice


def import_all_grihed_pdfs() -> None:
    s = time.perf_counter()
    items = []
    for pdf_path in (manual_upload_dir / "Grihed").iterdir():
        items.append(import_grihed_pdf(pdf_path))

    print(f"Importing all Grihed PDFs ({len(items)}) took {time.perf_counter() - s:3f}s")
