"""Stable conversation wording in the user's selected language."""
import re


def choose(dialect, english, hindi, hinglish=None):
    return hindi if dialect == 'Hindi' else (hinglish or hindi) if dialect == 'Hinglish' else english


def class_name(code, dialect='English'):
    names = {
        'SL': ('Sleeper', 'स्लीपर'), '3A': ('AC three tier', 'एसी थ्री टियर'),
        '2A': ('AC two tier', 'एसी टू टियर'), '1A': ('First AC', 'फर्स्ट एसी'),
        '3E': ('AC three tier economy', 'एसी थ्री टियर इकॉनमी'),
        'CC': ('AC chair car', 'एसी चेयर कार'), 'EC': ('Executive chair car', 'एग्ज़िक्यूटिव चेयर कार'),
        '2S': ('Second sitting', 'सेकंड सिटिंग'),
    }
    en, hi = names.get(str(code), (str(code), str(code)))
    return choose(dialect, en, hi, en)


def expand_status(text, dialect='English'):
    translations = {
        'GNWL': ('General waiting list', 'सामान्य प्रतीक्षा सूची'),
        'RLWL': ('Remote location waiting list', 'रिमोट लोकेशन प्रतीक्षा सूची'),
        'PQWL': ('Pooled quota waiting list', 'पूल्ड कोटा प्रतीक्षा सूची'),
        'TQWL': ('Tatkal waiting list', 'तत्काल प्रतीक्षा सूची'),
        'WL': ('Waiting list', 'प्रतीक्षा सूची'), 'RAC': ('Reservation against cancellation', 'रद्दीकरण के बदले आरक्षण'),
        'CNF': ('Confirmed', 'पुष्ट'), 'AVL': ('Available', 'उपलब्ध'),
        'AVAILABLE': ('Available', 'उपलब्ध'), 'REGRET': ('No further reservations available', 'आगे आरक्षण उपलब्ध नहीं'),
    }
    def replace(match):
        en, hi = translations[match.group().upper()]
        return choose(dialect, en, hi, en)
    return re.sub(r'\b(?:GNWL|RLWL|PQWL|TQWL|WL|RAC|CNF|AVL|AVAILABLE|REGRET)\b', replace, str(text), flags=re.I)


def missing_question(slot, dialect, trains=(), slots=None):
    questions = {
        'source': ('Which station are you travelling from?', 'यात्रा किस स्टेशन से शुरू होगी?'),
        'destination': ('Which station are you travelling to?', 'आपको किस स्टेशन तक जाना है?'),
        'date': ('What is your journey date?', 'आपकी यात्रा की तारीख क्या है?'),
        'train_no': ('Please choose a train from the results, or say its five-digit train number.', 'कृपया सूची में से ट्रेन चुनें या उसकी पाँच अंकों की संख्या बताएं।'),
        'class_code': ('Which class would you like?', 'आप किस श्रेणी में सीट देखना चाहेंगे?'),
        'passenger_name': ('What is the passenger name?', 'यात्री का नाम क्या है?'),
        'pnr_number': ('What is the ten-digit PNR number?', 'दस अंकों की पीएनआर संख्या क्या है?'),
    }
    en, hi = questions.get(slot, ('Please provide the missing details.', 'कृपया बाकी जानकारी बताएं।'))
    answer = choose(dialect, en, hi)
    selected = next((t for t in trains if str(t.get('no')) == (slots or {}).get('train_no')), None)
    if slot == 'class_code' and selected:
        classes = ', '.join(f'{class_name(c, dialect)} ({c})' for c in selected.get('classes', []))
        name = f"{selected.get('name')} ({selected.get('no')})"
        answer = choose(dialect, f'{name} offers {classes}. {answer}', f'{name} में {classes} श्रेणियां हैं। {answer}')
    return answer


MESSAGES = {
    "I haven't proceeded. Which detail would you like to change?": 'मैंने आगे कार्रवाई नहीं की है। आप कौन सी जानकारी बदलना चाहते हैं?',
    "I haven't proceeded. Please say yes to confirm, or tell me which detail to change.": 'मैंने आगे कार्रवाई नहीं की है। पुष्टि के लिए हाँ कहें, या बताएं कि कौन सी जानकारी बदलनी है।',
    'That train is not available for this route and date. Please select a listed train.': 'यह ट्रेन इस मार्ग और तारीख की सूची में नहीं है। कृपया सूची में से ट्रेन चुनें।',
    'That class is not offered on this train. Please select one of its listed classes.': 'इस ट्रेन में यह श्रेणी उपलब्ध नहीं है। कृपया इसकी सूची में से श्रेणी चुनें।',
    'Please give a valid travel date, for example 25 October 2026.': 'कृपया यात्रा की सही तारीख बताएं।',
    'That travel date is in the past. Please choose today or a future date.': 'यह तारीख बीत चुकी है। कृपया आज या आगे की तारीख चुनें।',
    'Please choose a language: English, Hindi, or Hinglish.': 'कृपया भाषा चुनें: अंग्रेज़ी, हिंदी या हिंग्लिश।',
    'Thank you for using LocoVoice. Goodbye!': 'लोकोवॉइस का उपयोग करने के लिए धन्यवाद। आपकी यात्रा शुभ हो!',
    'Please provide details.': 'कृपया बाकी जानकारी बताएं।',
    'Train search is temporarily unavailable.': 'अभी ट्रेन की जानकारी नहीं मिल पा रही है। कृपया थोड़ी देर बाद फिर कोशिश करें।',
    'The action could not be completed.': 'कार्रवाई पूरी नहीं हो पाई। कृपया फिर कोशिश करें।',
    'Internal system error occurred during execution.': 'तकनीकी समस्या के कारण कार्रवाई पूरी नहीं हो पाई। कृपया फिर कोशिश करें।',
}


def surface_text(text, dialect):
    if dialect != 'English':
        text = MESSAGES.get(text, text)
        if 'service is not connected' in text.lower():
            text = 'यह सेवा अभी जुड़ी नहीं है। मैं फिलहाल ट्रेन खोजने और सीट की उपलब्धता देखने में सहायता कर सकती हूँ।'
    # Only first-person assistant forms; never change the user's gender or train grammar.
    text = re.sub(r'\b(?:kar )?sakta hoon\b', 'कर सकती हूँ' if dialect == 'Hindi' else 'kar sakti hoon', text, flags=re.I)
    text = re.sub(r'\bkar raha hoon\b', 'कर रही हूँ' if dialect == 'Hindi' else 'kar rahi hoon', text, flags=re.I)
    text = text.replace('कर सकता हूँ', 'कर सकती हूँ').replace('कर सकता हूं', 'कर सकती हूँ')
    text = text.replace('कर रहा हूँ', 'कर रही हूँ').replace('कर रहा हूं', 'कर रही हूँ')
    return expand_status(text, dialect)


def spoken_text(text, dialect):
    """Expand only known railway terms at the speech boundary; keep cards unchanged."""
    text = surface_text(text, dialect)
    text = re.sub(r'\b(?:1A|2A|3A|3E|SL|CC|EC|2S)\b', lambda m: class_name(m.group(), dialect), text)
    text = re.sub(r'\bEXP\b', choose(dialect, 'Express', 'एक्सप्रेस', 'Express'), text)
    text = re.sub(r'\bSF\b', choose(dialect, 'Superfast', 'सुपरफास्ट', 'Superfast'), text)
    text = re.sub(r'\bSPL\b', choose(dialect, 'Special', 'स्पेशल', 'Special'), text)
    return text
