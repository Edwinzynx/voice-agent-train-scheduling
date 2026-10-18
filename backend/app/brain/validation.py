"""Deterministic boundaries for dates, confirmation, and journey selection."""
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

INDIA = timezone(timedelta(hours=5, minutes=30))
REQUIRED_SLOTS = {
    "FIND_TRAINS": ["source", "destination", "date"],
    "BOOK_TICKET": ["source", "destination", "date", "train_no", "class_code", "passenger_name"],
    "CHECK_SEAT": ["source", "destination", "date", "train_no", "class_code"],
    "CANCEL_TICKET": ["pnr_number"],
    "GET_PNR_STATUS": ["pnr_number"],
}


def today_in_india() -> date:
    return datetime.now(INDIA).date()


def date_expression(text: str):
    """Extract explicit dates before relative phrases; return None for unrelated text."""
    text = str(text or "").strip().lower()
    patterns = [
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?\b",
        r"\b(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"(?<!\w)(?:day after tomorrow|day before yesterday|tomorrow|today|yesterday|parso|parson|kal|aaj|आज|कल|परसों)(?!\w)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def normalize_date(value: str, today: date = None) -> str:
    """Return ISO date or reject it. Never silently substitute today's date."""
    today = today or today_in_india()
    text = str(value or "").strip().lower()
    relative = {"today": 0, "aaj": 0, "आज": 0, "tomorrow": 1, "kal": 1, "कल": 1,
                "day after tomorrow": 2, "parso": 2, "parson": 2, "परसों": 2,
                "yesterday": -1, "day before yesterday": -2}
    result = None
    if text in relative:
        result = today + timedelta(days=relative[text])
    elif re.fullmatch(r"(?:next )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", text):
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        delta = (weekdays.index(text.removeprefix("next ")) - today.weekday()) % 7
        result = today + timedelta(days=delta or 7)
    else:
        text = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", text)
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%d %B %Y"):
            try:
                result = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if result is None and re.fullmatch(r"\d{1,2} [a-z]+", text):
            for year in (today.year, today.year + 1):
                try:
                    candidate = datetime.strptime(f"{text} {year}", "%d %B %Y").date()
                    if candidate >= today:
                        result = candidate
                        break
                except ValueError:
                    continue
    if result is None:
        raise ValueError("Please give a valid travel date, for example 25 October 2026.")
    if result < today:
        raise ValueError("That travel date is in the past. Please choose today or a future date.")
    return result.isoformat()


def confirmation_decision(text: str):
    """Only explicit, unambiguous approval can execute an action."""
    text = "".join(" " if unicodedata.category(char).startswith("P") and char not in "'’" else char
                   for char in str(text or "").lower())
    text = " ".join(text.split())
    if re.search(r"(?<!\w)(not sure|unsure|maybe|perhaps|wait|hold on|pata nahi|शायद)(?!\w)", text):
        return None
    if re.search(r"(?<!\w)(no|not|never|don't|don’t|do not|nahi|nahin|na|mat|नहीं|मत|गलत)(?!\w)", text):
        return False
    if re.search(r"(?<!\w)(change|instead|actually|correct my|correct the|replace|badal|बदल)(?!\w)", text):
        return False
    if re.fullmatch(r"(?:please )?(?:yes|yes please|yes that is correct|yes that's correct|yes proceed|yes confirm|haan|han|ha|ji haan|haan ji|हाँ|हां|जी हाँ|ठीक है|sure|okay|ok|confirm|confirmed|proceed|go ahead|theek hai|haan ticket confirm kar do|haan cancel kar dijiye)(?: please)?", text):
        return True
    if re.fullmatch(r"(?:please )?cancel(?: the)?(?: request| process)?", text):
        return False
    return None
