from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from dateparser.search import search_dates

from booking_service import ROOM_ALIASES


def parse_duration(text: str) -> int | None:
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(hours?|hrs?|hr)\b", text, re.I)
    if match:
        return int(float(match.group(1)) * 60)
    match = re.search(r"\b(\d+)\s*(minutes?|mins?|min)\b", text, re.I)
    return int(match.group(1)) if match else None


def parse_room(text: str) -> str | None:
    lowered = text.lower()
    for alias in sorted(ROOM_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return ROOM_ALIASES[alias]
    return None


def parse_datetime(text: str):
    settings = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(),
        "RETURN_AS_TIMEZONE_AWARE": False,
    }
    matches = search_dates(text, languages=["en"], settings=settings) or []
    if not matches:
        return None, None
    # Prefer a match that includes a time marker.
    for fragment, parsed in reversed(matches):
        if re.search(r"\d\s*(?:am|pm)|\d:\d", fragment, re.I):
            return parsed.date(), parsed.time().replace(second=0, microsecond=0)
    parsed = matches[-1][1]
    return parsed.date(), None


def resolve_day_word(text: str):
    lowered = text.lower()
    if "day after tomorrow" in lowered:
        return date.today() + timedelta(days=2)
    if "tomorrow" in lowered:
        return date.today() + timedelta(days=1)
    if "today" in lowered:
        return date.today()
    return None
