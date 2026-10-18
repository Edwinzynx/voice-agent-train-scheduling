"""Concise answers grounded in retrieved railway data, without another LLM call."""
import re


def train_timing(train, arrival=False):
    label = f"{train.get('name') or 'Train'} ({train.get('no', 'unknown')})"
    field, station, verb = ('arr', 'dst', 'arrives at') if arrival else ('dep', 'src', 'departs from')
    time = train.get(field)
    if not time:
        return f"{label}: {'arrival' if arrival else 'departure'} time was not supplied."
    return f"{label} {verb} {train.get(station) or 'the station'} at {time} IST."


def result_summary(result, slots, dialect='English'):
    if 'trains' in result:
        trains = result['trains']
        route = f"{slots.get('source')} to {slots.get('destination')}"
        date = slots.get('date')
        if dialect == 'Hindi':
            intro = f"{date} को {route} के लिए {len(trains)} ट्रेनें मिलीं।"
        elif dialect == 'Hinglish':
            intro = f"{date} ko {route} ke liye {len(trains)} trains mili hain."
        else:
            intro = f"Found {len(trains)} trains from {route} for {date}."
        details = ' '.join(train_timing(t) for t in trains[:3])
        return f"{intro} {details} Choose a listed train and class to check seats." if trains else intro
    if 'seats_available' in result or 'status' in result:
        status = result.get('status') or (f"{result['seats_available']} seats available" if result.get('seats_available') is not None else 'Not supplied')
        fare = f"₹{result['price']}" if result.get('price') is not None else 'Not supplied'
        return f"Train {slots.get('train_no')}, {slots.get('class_code')}, {slots.get('date')}: {status}. Fare: {fare}."
    return 'The action is complete. Review the result details on screen.'


def schedule_followup(text, trains, slots):
    """Return None for new searches/selections; never silently select an ambiguous train."""
    lower = text.casefold()
    if not re.search(r'\b(time|depart\w*|arriv\w*|start\w*|leave\w*|reach\w*|schedule|kab|baje)\b|कब|बजे', lower):
        return None
    # A different travel date requires a fresh search, not a cached schedule.
    from .validation import date_expression, normalize_date
    expression = date_expression(text)
    if expression:
        try:
            if normalize_date(expression) != slots.get('date'):
                return None
        except ValueError:
            return None
    number = re.search(r'\b\d{5}\b', text)
    matches = [t for t in trains if number and str(t.get('no')) == number.group()]
    if not number:
        matches = [t for t in trains if t.get('name') and t['name'].casefold() in lower]
        if not matches:
            # Match complete station names, allowing city prefixes in the user's speech.
            def mentions(value):
                words = [word for word in re.findall(r'\w+', str(value).casefold())
                         if word not in ('station', 'stn', 'junction', 'jn', 'terminus')]
                return bool(words) and all(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in words)
            matches = [t for t in trains if mentions(t.get('src', '')) and mentions(t.get('dst', ''))]
        if not matches and re.search(r'\b(it|that train|this train)\b', lower):
            matches = [t for t in trains if str(t.get('no')) == slots.get('train_no')]
    if not matches:
        return f"I still have your journey date, {slots.get('date')}. Which listed train do you mean? Please say its name or five-digit number."
    arrival = bool(re.search(r'\b(arriv\w*|reach\w*)\b|पहुँच', lower))
    intro = f"For your {slots.get('date')} journey: "
    if len(matches) > 1:
        intro += f"{len(matches)} trains match those stations. "
    details = ' '.join(train_timing(t, arrival) for t in matches[:3])
    suffix = ' Which train number do you mean?' if len(matches) > 1 else ''
    return intro + details + suffix
