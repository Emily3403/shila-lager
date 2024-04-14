from __future__ import annotations

import asyncio
import itertools
import os
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from asyncio import AbstractEventLoop, get_event_loop
from pathlib import Path
from typing import TypeVar, Callable, Iterable

from shila_lager.settings import is_linux, is_macos, is_testing, is_windows, working_dir_location, database_url
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
    os.makedirs(fs_path(), exist_ok=True)


def fs_path(*args: str | Path) -> Path:
    """Prepend the args with the dedicated eet_backend directory"""
    return Path(working_dir_location, *args)


def parse_args() -> Namespace:
    """Parse the command line arguments"""
    parser = ArgumentParser(prog="shila_lager", formatter_class=RawTextHelpFormatter, description="""Shila Lager""")

    # Arguments that you can always add
    parser.add_argument("-v", "--verbose", help="Make the application more verbose", action="count", default=0)  # TODO: Is default needed?
    parser.add_argument("-d", "--debug", help="Debug the application", action="store_true")

    # Mutually exclusive arguments
    operations = parser.add_mutually_exclusive_group()
    operations.add_argument("-V", "--version", help="Print the version number and exit", action="store_true")

    if is_testing:
        # Pytest adds extra arguments that don't fit into the defined schema.
        return parser.parse_known_args()[0]

    parsed_args = parser.parse_args()
    # Now modify the arguments based on each other
    if parsed_args.debug:
        parsed_args.verbose = 3

    return parsed_args


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


# -/- More or less useful functions ---

T = TypeVar("T")
U = TypeVar("U")
KT = TypeVar("KT")

startup()
program_args = parse_args()

DEBUG_ASSERTS = program_args.debug
