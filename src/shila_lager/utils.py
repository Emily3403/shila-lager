from __future__ import annotations

import asyncio
import itertools
from asyncio import AbstractEventLoop, get_event_loop
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, Callable, Iterable, Any

from django.utils.dateparse import parse_datetime
from pytz import UTC

from shila_lager.settings import is_linux, is_macos, is_windows, working_dir_location, database_url, manual_upload_dir, plot_output_dir
from shila_lager.version import __version__


def print_version() -> None:
    # This is such an ingenious solution constructed by ChatGPT
    os_string = {is_windows: "Windows", is_macos: "MacOS", is_linux: "Linux"}.get(True, "Unknown OS")
    database_string = {"sqlite" in database_url: "SQLite", "mariadb" in database_url: "MariaDB", "postgresql" in database_url: "PostgreSQL"}.get(True, "Unknown Database")

    # This is a bit talkative, but I like giving info
    print(
        f"This is shila_lager with version: {__version__}\n"
        f"I am running on {os_string}\n"
        f"I am working in the directory \"{fs_path()}\" to store data\n"
        f"I am using {database_string} as the database engine\n"
    )


def startup() -> None:
    """The startup routine to ensure a valid directory structure"""
    fs_path().mkdir(exist_ok=True)
    manual_upload_dir.mkdir(exist_ok=True)
    plot_output_dir.mkdir(exist_ok=True)


def fs_path(*args: str | Path) -> Path:
    """Prepend the args with the dedicated eet_backend directory"""
    return Path(working_dir_location, *args)


# --- More or less useful functions ---

def get_input(allowed: set[str]) -> str:
    while True:
        choice = input()
        if choice in allowed:
            break

        print(f"Unhandled character: {choice!r} is not in the expected {{" + ", ".join(repr(item) for item in sorted(list(allowed))) + "}\nPlease try again.\n")

    return choice


def flat_map(func: Callable[[T], Iterable[U]], it: Iterable[T]) -> Iterable[U]:
    return itertools.chain.from_iterable(map(func, it))


def reverse_dict(it: dict[T, list[U]]) -> dict[U, T]:
    return {value: key for key, values in it.items() for value in values}


def get_async_time(event_loop: AbstractEventLoop | None = None) -> float:
    return (event_loop or get_event_loop()).time()


def queue_get_nowait(q: asyncio.Queue[T]) -> T | None:
    try:
        return q.get_nowait()
    except Exception:
        return None


# Copied and adapted from https://stackoverflow.com/a/63839503
class HumanBytes:
    @staticmethod
    def format(num: float) -> tuple[float, str]:
        """
        Human-readable formatting of bytes, using binary (powers of 1024) representation.

        Note: num > 0
        """

        unit_labels = ["  B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
        last_label = unit_labels[-1]
        unit_step = 1024
        unit_step_thresh = unit_step - 0.5

        for unit in unit_labels:
            if num < unit_step_thresh:
                # Only return when under the rounding threshold
                break
            if unit != last_label:
                num /= unit_step

        return num, unit

    @staticmethod
    def format_str(num: float | None) -> str:
        if num is None:
            return "?"

        n, unit = HumanBytes.format(num)
        return f"{n:.2f} {unit}"

    @staticmethod
    def format_pad(num: float | None) -> str:
        if num is None:
            return "   ?"

        n, unit = HumanBytes.format(num)
        return f"{f'{n:.2f}'.rjust(6)} {unit}"


def german_price_to_decimal(price: str) -> Decimal | None:
    if not price:
        return None

    try:
        return Decimal(price.replace(".", "_").replace(",", "."))
    except Exception:
        return None


def parse_numeric(it: str | float | int) -> Decimal:
    if isinstance(it, (float, int)):
        return Decimal(it)

    try:
        return Decimal(eval(it))
    except Exception:
        print(it)
        raise


def filter_by_date(it: date | datetime, start: date | datetime | None, end: date | datetime | None) -> bool:
    match it:
        # Always put datetime first as it is a subclass of date
        case datetime():
            return _filter_by_datetime(it, to_datetime(start), to_datetime(end))
        case date():
            return _filter_by_date(it, to_date(start), to_date(end))


def _filter_by_datetime(it: datetime, start: datetime | None, end: datetime | None) -> bool:
    return (start is None or it >= start) and (end is None or it <= end)


def _filter_by_date(it: date, start: date | None, end: date | None) -> bool:
    return (start is None or it > start) and (end is None or it <= end)


def to_date(it: date | datetime | None) -> date | None:
    match it:
        case None:
            return None
        case datetime():
            return it.date()
        case date():
            return it


def to_datetime(it: date | datetime | None) -> datetime | None:
    match it:
        case None:
            return None
        case datetime():
            return it
        case date():
            return datetime(it.year, it.month, it.day)


def autopct_pie_format_with_number(values: Iterable[float], cond: Callable[[float], bool] | None = None, autopct: str = "%1.1f%%") -> Callable[[float], str]:
    def my_format(pct: Any) -> Any:
        total = sum(values)
        val = pct * total / 100.0
        fmt = autopct % pct
        if cond is None or cond(val):
            return fmt + f'\n{val:.0f}€'
        return fmt

    return my_format


def parse_and_localize_date(date_str: str) -> datetime | None:
    it = parse_datetime(date_str)
    if it is None:
        return None
    return UTC.localize(it)


# -/- More or less useful functions ---

T = TypeVar("T")
U = TypeVar("U")
KT = TypeVar("KT")

# Type aliases
BeverageID = str
DepositCategory = Decimal

zero = Decimal(0)
