"""FastAPI api  for Sigalas Calendar Translator - Sigalas Calendar Translator.

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
from fastapi import FastAPI, Response

from .scraping import get_month_data

app = FastAPI()

@app.get("/{calendar_id}.ics")
def serve_calendar(calendar_id: int):
    if 1 <= calendar_id <= 8:
        calendar = get_month_data()[calendar_id - 1]
        return Response(content=str(calendar), media_type="text/calendar")
    return {"error": "Invalid calendar ID. Please use a number between 1 and 8."}

__all__ = ("app",)
