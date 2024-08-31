"""Scraping  for Sigalas Calendar Translator - Sigalas Calendar Translator.

Copyright (C) 2024  Parker Wahle

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""  # noqa: E501, B950

from __future__ import annotations

from datetime import datetime, date

import ics
from ics import Calendar
from ics.grammar.parse import ContentLine
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

MONTH_URL = "https://docs.google.com/presentation/d/18gyUuM0Av9SGZ0IiQ9zNWLgBIkZk2sjlL9CPDkhdyvk/edit?pli=1#slide=id.g25f875d857d_1_0"
YEAR = "2024-2025"

def get_month_data() -> tuple[Calendar, Calendar, Calendar, Calendar, Calendar, Calendar, Calendar, Calendar]:
    """Scrape the month data from the month URL. Returns a tuple of 8 ics.Calendars, one for each LHS period."""

    period_1_calendar = ics.Calendar()
    period_2_calendar = ics.Calendar()
    period_3_calendar = ics.Calendar()
    period_4_calendar = ics.Calendar()
    period_5_calendar = ics.Calendar()
    period_6_calendar = ics.Calendar()
    period_7_calendar = ics.Calendar()
    period_8_calendar = ics.Calendar()

    for i, calendar in enumerate([period_1_calendar, period_2_calendar, period_3_calendar, period_4_calendar, period_5_calendar, period_6_calendar, period_7_calendar, period_8_calendar]):
        calendar.extra.append(
            ContentLine(name="X-WR-CALNAME", value=f"Sigalas {YEAR} Period {i + 1}")
        )

    # ===== GENERAL GOOGLE SLIDES STUFF =====
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(MONTH_URL)
        month_data = page.content()
        browser.close()

    parsed = BeautifulSoup(month_data, "html5lib")

    # first step: get the filmstrip (pages on the left side of screen) id=filmstrip
    filmstrip = parsed.find("div", {"id": "filmstrip"})

    # scroller: div.punch-filmstrip-scroll
    scroller = filmstrip.find("div", {"class": "punch-filmstrip-scroll"})

    # inner scroller: #filmstrip > div.punch-filmstrip-scroll > svg
    inner_scroller = scroller.find("svg")

    # get a tag for each of g.punch-filmstrip-thumbnail in the inner_scroller
    thumbnails = inner_scroller.find_all("g", {"class": "punch-filmstrip-thumbnail"})

    for thumbnail in thumbnails:
        # in this thumbnail there is a single g
        # in that g there is a single svg
        # in that svg there is a single g
        # g holds another g

        # we have arrived at the slide
        slide = thumbnail.find("g").find("svg").find("g").find("g")

        # ===== END GENERAL GOOGLE SLIDES STUFF =====
        # below is processing that is sigalas-calendar specific, change per individual teacher's formatting
        month = slide.select_one('g[id*="paragraph-0"] text').text.strip()

        # main table in the slide, it's the last g on the first layer
        slide_table = slide.find_all("g", recursive=False)[-1]

        cells = [cell.find("g").find("g") for cell in slide_table.find_all("g", {"direction": "ltr"})]

        for cell in cells:
            text_lines_tags = cell.select('g[transform] g.sketchy-text-content-text')

            text_lines = [" ".join(text.text for text in line_tag.find_all("text")) for line_tag in text_lines_tags]

            if len(text_lines) == 0:
                continue  # this cell is empty

            cell_header = text_lines[0]

            day_of_month = int(cell_header.split(":")[0].strip())

            if day_of_month == 2 and month == "September":
                continue  # special case for the first day of school; it's the schedule

            period_assignments = text_lines[1:]
            new_period_assignments = []

            # preprocess the period assignments:
            # if the first character is not a number, concatenate it with the previous line
            for period_assignment in period_assignments:
                if period_assignment[0].isdigit():
                    new_period_assignments.append(period_assignment)
                else:
                    new_period_assignments[-1] += f" {period_assignment}"

            for period_assignment in new_period_assignments:
                if period_assignment == "":
                    continue

                period = int(period_assignment[0])

                calendar: Calendar

                match period:
                    case 1:
                        calendar = period_1_calendar
                    case 2:
                        calendar = period_2_calendar
                    case 3:
                        calendar = period_3_calendar
                    case 4:
                        calendar = period_4_calendar
                    case 5:
                        calendar = period_5_calendar
                    case 6:
                        calendar = period_6_calendar
                    case 7:
                        calendar = period_7_calendar
                    case 8:
                        calendar = period_8_calendar
                    case _:
                        raise ValueError("Invalid period")

                assignment = " ".join(period_assignment.split(":")[1:]).strip() or "TBD"

                year = YEAR.split("-")[1] if month in ["January", "February", "March", "April", "May", "June"] else YEAR.split("-")[0]

                event_datetime = datetime.strptime(f"{year}-{month}-{day_of_month}", "%Y-%B-%d")

                assignment_event = ics.Event(
                    name=assignment,
                    begin=event_datetime,
                    description=f"Sigalas Assignment for {assignment}",
                )
                assignment_event.make_all_day()

                calendar.events.add(assignment_event)

    return period_1_calendar, period_2_calendar, period_3_calendar, period_4_calendar, period_5_calendar, period_6_calendar, period_7_calendar, period_8_calendar

__all__ = ("get_month_data",)
