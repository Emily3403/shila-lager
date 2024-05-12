import csv
import time
from datetime import datetime
from pathlib import Path

from shila_lager.frontend.apps.rechnungen.crud import get_shila_account_bookings
from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, ShilaBookingKind
from shila_lager.settings import manual_upload_dir, logger
from shila_lager.utils import german_price_to_decimal


def import_booking_csv(csv_path: Path) -> list[ShilaAccountBooking] | None:
    if csv_path.suffix.lower() != ".csv":
        logger.error(f"{csv_path} is not a CSV file")
        return None

    with open(csv_path, "r") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader, None)
        if header is None:
            logger.error(f"{csv_path} is empty")
            return None

        rows = list(reader)

    assert header == ['Auftragskonto', 'Buchungstag', 'Valutadatum', 'Buchungstext', 'Verwendungszweck', 'Glaeubiger ID', 'Mandatsreferenz', 'Kundenreferenz (End-to-End)', 'Sammlerreferenz', 'Lastschrift Ursprungsbetrag', 'Auslagenersatz Ruecklastschrift', 'Beguenstigter/Zahlungspflichtiger',
                      'Kontonummer/IBAN', 'BIC (SWIFT-Code)', 'Betrag', 'Waehrung', 'Info']

    existing_bookings = get_shila_account_bookings()
    bookings_to_create = []

    for row in rows:
        booking_date = datetime.strptime(row[1], "%d.%m.%y").date()
        value_date = datetime.strptime(row[2], "%d.%m.%y").date()
        booking_kind = ShilaBookingKind.from_str(row[3])
        description = row[4]

        creditor_id = row[5] or None
        mandate_reference = row[6] or None
        customer_reference = row[7] or None
        collector_reference = row[8] or None

        original_amount = german_price_to_decimal(row[9])
        chargeback_amount = german_price_to_decimal(row[10])
        beneficiary_or_payer = row[11] or None
        iban = row[12]
        bic = row[13]

        amount = german_price_to_decimal(row[14])
        currency = row[15]
        additional_info = row[16]

        if amount is None:
            logger.error("Imported amount is None")
            continue

        booking = ShilaAccountBooking(
            booking_date=booking_date, value_date=value_date, kind=booking_kind, description=description, creditor_id=creditor_id, mandate_reference=mandate_reference, customer_reference=customer_reference, collector_reference=collector_reference, original_amount=original_amount,
            chargeback_amount=chargeback_amount, beneficiary_or_payer=beneficiary_or_payer, iban=iban, bic=bic, amount=amount, currency=currency, additional_info=additional_info
        )

        if booking not in existing_bookings:
            bookings_to_create.append(booking)

    return ShilaAccountBooking.objects.bulk_create(bookings_to_create)


def import_bookings() -> None:
    s = time.perf_counter()
    items = []
    for csv_path in (manual_upload_dir / "Sparkasse").iterdir():
        items.append(import_booking_csv(csv_path))

    print(f"Importing all Bookings took {time.perf_counter() - s:3f}s")
    pass
