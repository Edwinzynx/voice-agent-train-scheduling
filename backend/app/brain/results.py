"""Concise answers grounded in retrieved railway data, without another LLM call."""
import re
from .language import choose, class_name, expand_status


def train_timing(train, arrival=False, dialect='English'):
    label = f"{train.get('name') or 'Train'} ({train.get('no', 'unknown')})"
    field, station, verb = ('arr', 'dst', 'arrives at') if arrival else ('dep', 'src', 'departs from')
    time = train.get(field)
    if not time:
        return choose(dialect, f"{label}: {'arrival' if arrival else 'departure'} time was not supplied.",
                      f"{label}: {'आगमन' if arrival else 'प्रस्थान'} का समय नहीं मिला।")
    return choose(dialect, f"{label} {verb} {train.get(station) or 'the station'} at {time} IST.",
                  f"{label} {'का आगमन' if arrival else 'का प्रस्थान'} {train.get(station) or 'स्टेशन'} {'पर' if arrival else 'से'} {time} बजे है, भारतीय समय के अनुसार।")


def result_summary(result, slots, dialect='English'):
    if 'trains' in result:
        trains = result['trains']
        route = choose(dialect, f"{slots.get('source')} to {slots.get('destination')}", f"{slots.get('source')} से {slots.get('destination')}")
        date = slots.get('date')
        if dialect == 'Hindi':
            intro = f"{date} को {route} के लिए {len(trains)} ट्रेनें मिलीं।"
        elif dialect == 'Hinglish':
            intro = f"{date} को {route} के लिए {len(trains)} trains मिली हैं।"
        else:
            intro = f"Found {len(trains)} trains from {route} for {date}."
        details = ' '.join(train_timing(t, dialect=dialect) for t in trains[:3])
        instruction = choose(dialect, 'Choose a listed train and class to check seats.', 'सीट की उपलब्धता देखने के लिए सूची से ट्रेन और श्रेणी चुनें।')
        return f"{intro} {details} {instruction}" if trains else intro
    if 'seats_available' in result or 'status' in result:
        status = result.get('status') or (choose(dialect, f"{result['seats_available']} seats available", f"{result['seats_available']} सीटें उपलब्ध हैं") if result.get('seats_available') is not None else choose(dialect, 'Not supplied', 'जानकारी नहीं मिली'))
        status = expand_status(status, dialect)
        fare = str(result['price']) if result.get('price') is not None else choose(dialect, 'Not supplied', 'जानकारी नहीं मिली')
        coach = class_name(slots.get('class_code'), dialect)
        answer = choose(dialect,
            f"Train {slots.get('train_no')}, {coach}, {slots.get('date')}: {status}. Fare: ₹{fare}.",
            f"ट्रेन {slots.get('train_no')}, {coach}, तारीख {slots.get('date')}: {status}। किराया: {fare} रुपये।")
        if re.search(r'\b(?:WL|GNWL|RLWL|PQWL|TQWL)\b', str(result.get('status', '')), re.I):
            answer += choose(dialect, ' This is a waiting-list position, not a confirmed seat.', ' यह प्रतीक्षा सूची की स्थिति है, पुष्ट सीट नहीं।')
        return answer
    return choose(dialect, 'The action is complete. Review the result details on screen.', 'कार्रवाई पूरी हो गई है। कृपया स्क्रीन पर जानकारी देखें।')


def schedule_followup(text, trains, slots, dialect='English'):
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
        return choose(dialect,
            f"I still have your journey date, {slots.get('date')}. Which listed train do you mean? Please say its name or five-digit number.",
            f"आपकी यात्रा की तारीख {slots.get('date')} मेरे पास है। कृपया ट्रेन का नाम या पाँच अंकों की संख्या बताएं।")
    arrival = bool(re.search(r'\b(arriv\w*|reach\w*)\b|पहुँच', lower))
    intro = choose(dialect, f"For your {slots.get('date')} journey: ", f"आपकी {slots.get('date')} की यात्रा के लिए: ")
    if len(matches) > 1:
        intro += choose(dialect, f"{len(matches)} trains match those stations. ", f"इन स्टेशनों के लिए {len(matches)} ट्रेनें हैं। ")
    details = ' '.join(train_timing(t, arrival, dialect) for t in matches[:3])
    suffix = choose(dialect, ' Which train number do you mean?', ' आपका मतलब किस ट्रेन संख्या से है?') if len(matches) > 1 else ''
    return intro + details + suffix
