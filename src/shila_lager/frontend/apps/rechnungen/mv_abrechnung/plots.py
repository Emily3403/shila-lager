from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from numbers import Number
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

from shila_lager.frontend.apps.rechnungen.models import ShilaAccountBooking, GrihedInvoice, ShilaBookingCategory
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.data import AnalyzedBeverageCrate, group_invoices_by_time_interval
from shila_lager.frontend.apps.rechnungen.mv_abrechnung.static_data import beverage_categories, meta_categories
from shila_lager.settings import plot_output_dir
from shila_lager.utils import flat_map, autopct_pie_format_with_number


def fill_plt_with_shila_events(add_shila_closed_times: bool, start: datetime | None = None, end: datetime | None = None) -> None:
    def axvline(date: datetime, **kwargs: Any) -> None:
        if start is not None and date < start:
            return
        if end is not None and date > end:
            return

        plt.axvline(x=mdates.date2num(date), **kwargs)

    def axvspan(start_date: datetime, end_date: datetime, **kwargs: Any) -> None:
        if start is not None and start_date < start:
            return
        if end is not None and end_date > end:
            return

        plt.axvspan(mdates.date2num(start_date), mdates.date2num(end_date), **kwargs)

    lw = 1.7
    op = 0.7

    colors = {
        "Shila zu": ("lightcoral", op - 0.3),
        "Konzerte": ("mediumvioletred", op - 0.3),
        "Shilafahrt": ("mediumvioletred", op),
        "Bierpreiserhöhung": ("limegreen", op),
        "Events / SAP": ("seagreen", op),
        "Semesterferien": ("silver", op - 0.1),
        "Kein allgemeiner Tresorzugriff": ("limegreen", op),
    }

    if add_shila_closed_times:
        axvspan(datetime(2024, 1, 16), datetime(2024, 2, 18), color=colors["Shila zu"], label="Shila zu")
        axvspan(datetime(2023, 12, 23), datetime(2024, 1, 7), color=colors["Shila zu"], label="Shila zu")
        axvspan(datetime(2022, 12, 23), datetime(2023, 1, 5), color=colors["Shila zu"], label="Shila zu")

        axvspan(datetime(2022, 7, 23), datetime(2022, 10, 17), color=colors["Semesterferien"], label="Semesterferien")
        axvspan(datetime(2023, 2, 18), datetime(2023, 4, 17), color=colors["Semesterferien"], label="Semesterferien")
        axvspan(datetime(2023, 7, 22), datetime(2023, 10, 16), color=colors["Semesterferien"], label="Semesterferien")
        axvspan(datetime(2024, 2, 17), datetime(2024, 4, 15), color=colors["Semesterferien"], label="Semesterferien")
        # axvspan(datetime(2024, 7, 20), datetime(2024, 10, 16), color=colors["Semesterferien"])

    axvline(datetime(2022, 10, 28), color=colors["Shilafahrt"], linestyle="--", linewidth=lw, label="Shilafahrt")
    axvline(datetime(2023, 11, 3), color=colors["Shilafahrt"], linestyle="--", linewidth=lw, label="Shilafahrt")

    axvline(datetime(2022, 10, 30), color=colors["Bierpreiserhöhung"], linestyle="-", linewidth=lw, label="Bierpreiserhöhnug")
    axvline(datetime(2024, 4, 11), color=colors["Kein allgemeiner Tresorzugriff"], linestyle="-", linewidth=lw, label="Kein allgemeiner Tresorzugriff")

    for event in [
        datetime(2024, 4, 26), datetime(2024, 4, 19),
        datetime(2023, 10, 20), datetime(2023, 10, 20), datetime(2023, 7, 12), datetime(2023, 4, 21),
        datetime(2022, 7, 8)
    ]:
        axvline(event, color=colors["Events / SAP"], linestyle="--", linewidth=lw, label="Events / SAP")

    # Remove duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc="lower right")


def plot_bookings(all_bookings: list[ShilaAccountBooking], start: datetime | None = None, end: datetime | None = None, only_netto: bool = True) -> None:
    # TODO: Shilafahrt rausrechnen
    # TODO: I think it would be best if we color the lines up and down a specific color, depending on which kind of booking it was
    # TODO: Add an optional line from all einzahlungen to each other to see the overall trend
    # TODO: Linie drüber legen mit "wie viel hätte reinkommen sollen" → bis zur nächsten Einzahlung, mit top-up prinzip
    #   Eine cumline, die alles überspannt und jedes Jahr
    #   Vielleicht irgendetwas mit gewinn line oder so
    # TODO: Senkrechte Flanken

    plt.figure(figsize=(32, 15))
    plt.title(f"Shila{' Netto' if only_netto else ''} Kontostand")
    plt.xlabel("Zeitpunkt")
    plt.ylabel("Betrag in €")
    plt.grid(True)

    filter_by_start, filter_by_end = lambda it: start is None or start.date() <= it, lambda it: end is None or it <= end.date()

    original_dates_and_balances = [(it.booking_date, np.float64(it.amount)) for it in all_bookings if filter_by_start(it.booking_date) and filter_by_end(it.booking_date)]
    modified_dates_and_balances = [(it.actual_booking_date(), np.float64(it.amount)) for it in all_bookings if filter_by_start(it.actual_booking_date()) and filter_by_end(it.actual_booking_date())]
    orgiginal_discarded_balances, modified_discarded_balances = [np.float64(it.amount) for it in all_bookings if not filter_by_start(it.booking_date)], [np.float64(it.amount) for it in all_bookings if not filter_by_start(it.actual_booking_date())]
    original_dates_and_balances.sort(key=lambda it: it[0]), modified_dates_and_balances.sort(key=lambda it: it[0])

    if orgiginal_discarded_balances:
        original_dates_and_balances.insert(0, (original_dates_and_balances[0][0], np.sum(orgiginal_discarded_balances)))
    if modified_discarded_balances:
        modified_dates_and_balances.insert(0, (modified_dates_and_balances[0][0], np.sum(modified_discarded_balances)))

    (original_dates, original_balances), (modified_dates, modified_balances) = zip(*original_dates_and_balances), zip(*modified_dates_and_balances)
    original_cum_balances, modified_cum_balances = np.cumsum(original_balances), np.cumsum(modified_balances)
    assert len(original_dates) == len(original_cum_balances)
    assert len(modified_dates) == len(modified_cum_balances)

    if only_netto is False:
        # TODO: Make this less jagged
        plt.stairs(original_cum_balances, original_dates + (original_dates[-1],), color="mediumvioletred")

    plt.stairs(modified_cum_balances, modified_dates + (modified_dates[-1],), color="blue")
    plt.fill_between(modified_dates, 0, modified_cum_balances, where=(modified_cum_balances >= 0), color="blue", alpha=0.4, step="post")
    plt.fill_between(modified_dates, 0, modified_cum_balances, where=(modified_cum_balances < 0), color="red", alpha=0.4, step="post")

    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(1000))
    plt.savefig(plot_output_dir / f"shila{'_netto' if only_netto else ''}_kontostand_stairs.png", dpi=400, bbox_inches="tight")

    fill_plt_with_shila_events(True, start, end)
    plt.savefig(plot_output_dir / f"shila{'_netto' if only_netto else ''}_kontostand_mit_events_stairs.png", dpi=400, bbox_inches="tight")


def plot_bookings_bar(all_bookings: list[ShilaAccountBooking], start: datetime | None = None, end: datetime | None = None) -> None:
    plt.figure(figsize=(32, 15))
    plt.title("Shila Kontostand")
    plt.xlabel("Zeitpunkt")
    plt.ylabel("Betrag in €")
    plt.grid(True)

    filter_by_start, filter_by_end = lambda it: start is None or start.date() <= it, lambda it: end is None or it <= end.date()

    dates_and_balances = defaultdict(list)
    for booking in all_bookings:
        date = booking.actual_booking_date()
        if filter_by_start(date) and filter_by_end(date):
            dates_and_balances[date.strftime("%Y-%m-%d")].append(np.float64(booking.amount))

    discarded_balances = [np.float64(it.amount) for it in all_bookings if not filter_by_start(it.actual_booking_date())]
    if discarded_balances:
        dates_and_balances[min(dates_and_balances.keys())].append(np.sum(discarded_balances))

    sorted_dates_and_balances = sorted(dates_and_balances.items(), key=lambda it: it[0])
    dates, balances = zip(*[(datetime.strptime(date, "%Y-%m-%d").date(), np.sum(values)) for (date, values) in sorted_dates_and_balances])
    assert len(dates) == len(balances)
    plt.bar(dates, np.cumsum(balances), color="blue")

    plt.savefig(plot_output_dir / "shila_netto_kontostand_bar.png", dpi=400, bbox_inches="tight")

    fill_plt_with_shila_events(True, start, end)
    plt.savefig(plot_output_dir / "shila_netto_kontostand_mit_events_bar.png", dpi=400, bbox_inches="tight")


def plot_beverage_profit_and_turnover_piecharts(crates: list[AnalyzedBeverageCrate]) -> None:
    crates_by_id = {crate.id: crate for crate in crates}
    category_profits, category_theoretical_profits, category_turnovers, category_colors = defaultdict(dict), defaultdict(dict), defaultdict(dict), {}
    reverse_meta_categories = {category: meta_category for meta_category, (_, categories) in meta_categories.items() for category in categories}

    # TODO: Generalize this entire function across profits, theoretical and turnovers
    # TODO: Weiteren Plot mit Balken und Bezugslinie dazwischen: https://stackoverflow.com/questions/55965824/matplotlib-add-line-to-link-stacked-bar-plot-categories
    # TODO: Add Kaffee and Snacks

    def get_it(id: str, attr: str) -> Decimal:
        # TODO: This is a bit loosy goosy, I don"t like that I could misspell the attribute name
        return getattr(crates_by_id.get(id), attr, Decimal(0))

    for meta_category, (_, categories) in meta_categories.items():
        for category in categories:
            color, ids = beverage_categories[category]
            category_profits[meta_category][category] = sum(get_it(id, "total_profit") for id in ids)
            category_theoretical_profits[meta_category][category] = sum(get_it(id, "total_theoretical_profit") for id in ids)
            category_turnovers[meta_category][category] = sum(get_it(id, "total_turnover") for id in ids)
            category_colors[category] = color

    labels, profits = zip(*flat_map(lambda it: sorted(it.items(), key=lambda item: abs(item[1]), reverse=True), category_profits.values()))
    theoretical_profits = [category_theoretical_profits[reverse_meta_categories[label]][label] for label in labels]
    turnovers = [category_turnovers[reverse_meta_categories[label]][label] for label in labels]
    profit_colors, turnover_colors = [category_colors[category] for category in labels if category != "Soli"], [category_colors[category] for category in labels]

    # First plot: pie chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    def format_label(label: str, profit: Decimal, is_turnover: bool) -> str:
        profit_str = f"{profit:.0f}€"
        if label in {"Wein", "Sekt", "Limo", "Wasser"}:
            return label

        fmt_label, post_label = label, ""
        if is_turnover and label in {"Anderes Bier", "Berliner Kindl", "Andechs"} or not is_turnover and label in {"Berliner Kindl"}:
            fmt_label = " " * (5 if label != "Berliner Kindl" else 9) + label
            profit_str = " " * 4 + profit_str

        if label in {"Mate"} and is_turnover or label in {"Soli", "Anderes Bier"} and not is_turnover:
            fmt_label = "\n" + fmt_label
        if label == "Pilsator" or label == "Berliner Kindl" and is_turnover:
            post_label = "\n"
        if label == "Spezi" and not is_turnover:
            post_label = "\n\n"

        return fmt_label + "\n" + profit_str + post_label

    formatted_labels = [format_label(label, profit, False) for label, profit in zip(labels, profits) if label != "Soli"]
    values = [abs(float(profit)) for label, profit in zip(labels, profits) if label != "Soli"]
    wedges1, texts1, autotexts1 = ax1.pie(values, labels=formatted_labels, colors=profit_colors, autopct="%1.1f", startangle=180, labeldistance=1.24, textprops={"horizontalalignment": "center", "fontsize": 12})
    # ax1.set_title("Gewinn")

    formatted_labels = [format_label(label, profit, True) for label, profit in zip(labels, turnovers)]
    wedges2, texts2, autotexts2 = ax2.pie(list(map(lambda it: abs(float(it)), turnovers)), labels=formatted_labels, colors=turnover_colors, autopct="%1.1f", startangle=180, labeldistance=1.24, textprops={"horizontalalignment": "center", "fontsize": 12})

    # ax2.set_title("Ausgaben")

    def draw_meta_category_border(ax: Any, wedges: Any, category_labels):
        for meta_category, (color, categories) in meta_categories.items():
            meta_indices = [i for i, label in enumerate(category_labels) if label in categories]
            if not meta_indices:
                continue

            # Calculate the start and end angles of the meta-category
            start_angle = wedges[meta_indices[0]].theta1
            end_angle = wedges[meta_indices[-1]].theta2

            # Draw the arc for the meta-category border
            arc = Arc((0, 0), 2, 2, angle=0, theta1=start_angle, theta2=end_angle, color=color, lw=20)
            ax.add_patch(arc)

    # Draw meta-category borders
    draw_meta_category_border(ax1, wedges1, [label for label in labels if label != "Soli"])
    draw_meta_category_border(ax2, wedges2, labels)

    plt.tight_layout()
    plt.savefig(plot_output_dir / "gewinn_und_ausgaben_pro_getränk_pie.png", dpi=500, bbox_inches="tight")

    # Second plot: stacked bar chart
    # TODO: Anders stacken: Ausgaben, Einnahmen, theoretische einnahmen
    fig, ax = plt.subplots(figsize=(14, 7))
    bar_width = 0.65
    r = range(len(profits))

    bars3 = ax.bar(r, turnovers, width=bar_width, label="Ausgaben", color="C1")
    bars2 = ax.bar(r, theoretical_profits, width=bar_width, label="Flaschenschwund", color="red")
    bars1 = ax.bar(r, profits, width=bar_width, label="Gewinn", color="C0")

    for bar in bars1:
        yval = bar.get_height()
        if 0 < yval < 500:
            additional_height = -yval - 250
        else:
            additional_height = -250

        ax.text(bar.get_x() + bar.get_width() / 2, yval + additional_height, f"{yval:.2f}", va="bottom", ha="center")

    for _bar, bar in zip(bars1, bars2):
        yval = bar.get_height()
        amount = yval - _bar.get_height()

        if yval < 0:
            add_val = -120
        else:
            add_val = 130

        if amount > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_y() + amount + add_val, f"{amount:.2f}", va="center_baseline", ha="center", color="red")

    for bar, label in zip(bars3, labels):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + bar.get_y(), f"{yval:.2f}", va="bottom", ha="center")

    ax.set_title("Umsatz und Gewinn pro Kategorie")
    ax.set_xticks(r)
    ax.set_xticklabels(labels)
    ax.legend()
    plt.tight_layout()
    plt.savefig(plot_output_dir / "gewinn_und_ausgaben_pro_getränk_bar.png", dpi=400, bbox_inches="tight")


def plot_beverage_consumption_over_time(invoices: list[GrihedInvoice]) -> None:
    interval_days = 14
    grouped_invoices = group_invoices_by_time_interval(invoices, interval_days)

    dates = sorted(grouped_invoices.keys())
    turnovers = [sum(float(it.total_turnover) for it in grouped_invoices[date]) for date in dates]
    profits = [sum(float(it.total_profit) for it in grouped_invoices[date]) for date in dates]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, turnovers, label="Ausgaben")
    ax.plot(dates, profits, label="Gewinn")
    ax.set_title(f"Gewinn und Ausgaben (Intervall: {interval_days} tage)")
    ax.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_locator(plt.MultipleLocator(1000))
    plt.tight_layout()
    plt.savefig(plot_output_dir / "gewinn_und_ausgaben_line.png", dpi=400, bbox_inches="tight")

    # Second plot: Line chart per category
    fig, ax = plt.subplots(figsize=(12, 6))
    for category, (color, ids) in beverage_categories.items():
        category_profits = [sum(float(it.total_profit) for it in grouped_invoices[date] if it.id in ids) for date in dates]
        ax.plot(dates, category_profits, label=category, color=color)

    ax.set_title(f"Gewinn pro Kategorie (Intervall: {interval_days} tage)")
    ax.legend(loc="upper left")
    plt.grid(True)
    plt.xticks(rotation=45)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_locator(plt.MultipleLocator(500))
    plt.tight_layout()
    plt.savefig(plot_output_dir / "gewinn_pro_kategorie_line.png", dpi=400, bbox_inches="tight")

    fig, ax = plt.subplots(figsize=(12, 6))
    for category, (color, ids) in beverage_categories.items():
        category_turnovers = [sum(float(it.total_turnover) for it in grouped_invoices[date] if it.id in ids) for date in dates]
        ax.plot(dates, category_turnovers, label=category, color=color)

    ax.set_title(f"Umsatz pro Kategorie (Intervall: {interval_days} tage)")
    ax.legend(loc="upper left")
    plt.grid(True)
    plt.xticks(rotation=45)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_locator(plt.MultipleLocator(1000))
    plt.tight_layout()
    plt.savefig(plot_output_dir / "ausgaben_pro_kategorie_line.png", dpi=400, bbox_inches="tight")


def plot_shila_value(current_account_balance: Decimal, inventory_value_when_sold: Decimal, tips: Decimal, debts_to_shila: Decimal, kleingeld: Decimal) -> None:
    actual_account_balance = current_account_balance - tips
    labels = ["Kontostand", "Trinkgeld", "Schulden", "Kleingeld", "Inventar"]
    values = [float(actual_account_balance), float(tips), float(debts_to_shila), float(kleingeld), float(inventory_value_when_sold)]

    # Colors for the pie chart
    colors = ["#4774ee", "#4766d7", "red", "gold", "forestgreen"]

    # Create the pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(values, labels=labels, colors=colors, autopct=autopct_pie_format_with_number(values), startangle=140, labeldistance=1.04, textprops={"fontsize": "16"})
    # ax.set_title(f"Wert des Shilas", fontsize="23")
    plt.tight_layout()
    plt.savefig(plot_output_dir / "shila_wert.png", dpi=400, bbox_inches="tight", transparent=True)


def plot_turnover_categories(_turnover_per_category: dict[ShilaBookingCategory, Decimal]) -> None:
    too_little_to_plot = {ShilaBookingCategory.hosting, ShilaBookingCategory.chocholate, ShilaBookingCategory.dm}
    turnover_per_category = {category.value: abs(float(turnover)) for category, turnover in _turnover_per_category.items() if category not in too_little_to_plot}
    turnover_per_category[ShilaBookingCategory.other.value] += sum(float(_turnover_per_category[category]) for category in too_little_to_plot)
    labels, values = zip(*reversed(sorted(turnover_per_category.items(), key=lambda it: it[1], reverse=True)))

    colors = ["forestgreen", "gold", "red", "#4774ee"]

    def autopct(values: NDArray[Number]) -> str:
        def my_format(pct):
            total = sum(values)
            val = pct * total / 100.0
            fmt = "%1.1f%%" % pct
            if val > 1000:
                return fmt + f'\n{val:.0f}€'
            return "\n" + fmt + f'\n{val:.0f}€'

        return my_format

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.pie(values, autopct=autopct(values), labels=labels, startangle=0, labeldistance=1.04, colors=colors, textprops={"fontsize": "14"})
    # ax.legend(loc="upper center", labels=labels, bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
    # ax.set_title("Umsatz pro Kategorie", fontsize="23")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_output_dir / "konto_ausgaben_pro_kategorie_pie.png", dpi=400, bbox_inches="tight", transparent=True)
