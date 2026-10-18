"""Resolve train references against this journey's results only."""
import re
from difflib import SequenceMatcher


def normalized_name(text):
    words = re.findall(r'[a-z0-9]+', str(text).casefold())
    aliases = {'exp': 'express', 'sf': 'superfast', 'spl': 'special'}
    return ' '.join(aliases.get(word, word) for word in words)


def match_train(text, trains):
    """Return (exact match, suggested match). Suggestions always need confirmation."""
    number = re.search(r'\b\d{5}\b', text)
    if number:
        return next((t for t in trains if str(t.get('no')) == number.group()), None), None
    query = normalized_name(text)
    exact = [t for t in trains if normalized_name(t.get('name', ''))
             and f" {normalized_name(t['name'])} " in f' {query} ']
    if len(exact) == 1:
        return exact[0], None
    # Score windows so a polite request around a name doesn't dominate similarity.
    words = query.split()
    ranked = []
    for train in trains:
        name = normalized_name(train.get('name', ''))
        if not name:
            continue
        size = len(name.split())
        scores = [SequenceMatcher(None, name, ' '.join(words[i:i+n])).ratio()
                  for n in range(max(1, size-1), size+2) for i in range(max(0, len(words)-n+1))]
        ranked.append((max(scores, default=0), train))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if ranked and ranked[0][0] >= .80 and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= .12):
        return None, ranked[0][1]
    return None, None


def filler_only(text):
    return bool(re.fullmatch(r'(?:uh|um|umm|erm|hmm|हम्म|उह|अं)(?:[\s.,!?।]*)', text.strip(), re.I))


def selected_class(text):
    match = re.search(r'\b(1A|2A|3A|3E|SL|CC|EC|2S)\b', text, re.I)
    if match:
        return match.group().upper()
    aliases = {'sleeper': 'SL', 'स्लीपर': 'SL', 'chair car': 'CC', 'चेयर कार': 'CC',
               'third ac': '3A', 'ac three tier': '3A', 'ac 3 tier': '3A', 'थ्री टियर': '3A',
               'second ac': '2A', 'ac two tier': '2A', 'टू टियर': '2A', 'first ac': '1A'}
    return next((code for phrase, code in aliases.items() if phrase in text.casefold()), None)
