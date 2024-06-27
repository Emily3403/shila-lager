import csv
import time
from datetime import datetime
from pathlib import Path

from shila_lager.frontend.apps.rechnungen.crud import get_shila_account_bookings, get_grihed_invoices
from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, ShilaBookingKind
from shila_lager.settings import manual_upload_dir, logger, grihed_creditor_id, grihed_mandate_reference, grihed_description, grihed_beneficiary_or_payer, grihed_iban, grihed_bic, grihed_currency, grihed_additional_info, grihed_booking_date_regex
from shila_lager.utils import german_price_to_decimal


def import_booking_csv(csv_path: Path) -> list[ShilaAccountBooking] | None:
    if csv_path.suffix.lower() != ".csv":
        logger.error(f"{csv_path} is not a CSV file")
        return None

    # TODO: Support ISO-8859-1 and other encodings
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
            existing_bookings.add(booking)

    return ShilaAccountBooking.objects.bulk_create(bookings_to_create)


def import_grihed_non_booked_items() -> list[ShilaAccountBooking]:
    invoices = get_grihed_invoices()
    bookings = get_shila_account_bookings()
    booked_invoice_numbers: set[str] = set()

    # First pass: Remove old temp bookings
    for booking in bookings:
        if booking.beneficiary_or_payer != grihed_beneficiary_or_payer:
            continue

        if booking.is_temp:
            booking.delete()
            continue

        booked_invoice_numbers.update({it for it, _ in grihed_booking_date_regex.findall(booking.description)})

    # Second pass: Add new temp bookings
    bookings_to_add = []
    for invoice in invoices:
        if invoice.invoice_number in booked_invoice_numbers:
            continue

        bookings_to_add.append(ShilaAccountBooking(
            booking_date=datetime.now().date(), value_date=datetime.now().date(), kind=ShilaBookingKind.lastschrift, description=grihed_description(invoice.invoice_number, invoice.date),
            creditor_id=grihed_creditor_id, mandate_reference=grihed_mandate_reference, customer_reference=None, collector_reference=None, original_amount=None, chargeback_amount=None,
            beneficiary_or_payer=grihed_beneficiary_or_payer, iban=grihed_iban, bic=grihed_bic, amount=-invoice.total_price, currency=grihed_currency, additional_info=grihed_additional_info
        ))
        # logger.info(f"Added booking for {invoice.invoice_number} ({invoice.date})")

    return ShilaAccountBooking.objects.bulk_create(bookings_to_add)


def import_bookings() -> list[ShilaAccountBooking]:
    s = time.perf_counter()
    items = []
    for csv_path in (manual_upload_dir / "Sparkasse").iterdir():
        items.append(import_booking_csv(csv_path))

    import_grihed_non_booked_items()

    logger.info(f"Importing all Bookings took {time.perf_counter() - s:3f}s")
    return [it for item in items if item is not None for it in item]
