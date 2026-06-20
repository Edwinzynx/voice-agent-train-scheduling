import os
import re
import json
import logging
from groq import Groq
from ..config import config_manager
from .prompts import INTENT_SYSTEM_PROMPT, SLOT_FILLER_SYSTEM_PROMPT, CONFIRMATION_SYSTEM_PROMPT, EXECUTE_SYSTEM_PROMPT
from ..tools import irctc

logger = logging.getLogger(__name__)

# List of typical stations for mock parsing
MOCK_STATIONS = ["delhi", "mumbai", "bhopal", "varanasi", "lucknow", "patna", "bangalore", "chennai", "pune", "ernakulam", "chandigarh", "patiala"]
MOCK_CLASSES = ["1A", "2A", "3A", "SL", "CC", "EC"]

def call_groq_json(system_prompt: str, user_prompt: str, api_key: str) -> dict:
    """
    Calls Groq chat completion API with JSON response format and automatic rate limit retry.
    """
    import time
    model_name = config_manager.settings.llm_model or "llama-3.3-70b-versatile"
    client = Groq(api_key=api_key)
    
    max_retries = 8
    
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model_name,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500
            )
            response_text = chat_completion.choices[0].message.content
            return json.loads(response_text)
        except Exception as e:
            err_msg = str(e).lower()
            is_rate_limit = any(x in err_msg for x in ["rate_limit", "rate limit", "429", "413", "limit exceeded", "too many requests", "tpm", "rpm"])
            
            if is_rate_limit and attempt < max_retries - 1:
                # Sleep a flat 25 seconds to clear a major chunk of the rolling 1-minute window
                sleep_time = 25.0
                logger.warning(f"Groq API rate limit hit. Retrying in {sleep_time:.1f}s... Error: {e}")
                time.sleep(sleep_time)
            else:
                logger.error(f"Error in Groq API call: {e}")
                raise e

def contains_word_or_phrase(text: str, item: str) -> bool:
    if len(item) <= 3:
        return bool(re.search(rf"\b{re.escape(item)}\b", text))
    return item in text

def mock_classify_intent(user_input: str) -> dict:
    """
    Rule-based local fallback for intent classification.
    """
    text = user_input.lower()
    
    # Detect language roughly
    is_hindi = any(contains_word_or_phrase(text, word) for word in ["hai", "kab", "kya", "kar", "se", "ko", "tujhe", "radd", "gaadi"])
    is_english = any(contains_word_or_phrase(text, word) for word in ["book", "cancel", "status", "train", "seat", "availability"])
    lang = "Hinglish" if (is_hindi and is_english) else "Hindi" if is_hindi else "English"
    
    intent = "UNKNOWN"
    # 0. Check for end of conversation phrases
    if any(contains_word_or_phrase(text, phrase) for phrase in ["no more", "nothing", "no thanks", "thank you", "thanks", "bye", "exit", "stop", "na", "nahi", "bas", "that is all", "that's it"]):
        if not any(contains_word_or_phrase(text, word) for word in ["cancel", "book", "status", "seat", "avail", "tomorrow", "kal", "se", "ko"]):
            intent = "END_CONVERSATION"
            
    # Re-ordered checks to prevent general words like 'ticket' in cancel flows matching BOOK_TICKET
    if intent == "UNKNOWN":
        if "cancel" in text or "radd" in text or "cancellation" in text:
            intent = "CANCEL_TICKET"
        elif "status" in text or "pnr" in text or "chalti" in text or "live" in text:
            intent = "GET_PNR_STATUS"
        elif "seat" in text or "avail" in text or "khali" in text:
            intent = "CHECK_SEAT"
        elif "train" in text or "gaadi" in text or "search" in text or "khoj" in text:
            intent = "FIND_TRAINS"
        elif "book" in text or "booking" in text or "ticket" in text or "kar do" in text or "yatra" in text:
            intent = "BOOK_TICKET"
        
    return {
        "intent": intent,
        "reason": "Rule-based mock classifier match",
        "language_detected": lang
    }

def mock_fill_slots(user_input: str, current_slots: dict, intent: str, dialect: str = "Hinglish", context: dict = None) -> dict:
    """
    Rule-based local fallback for slot filling.
    """
    text = user_input.lower()
    slots = current_slots.copy()
    
    # Pre-check: Did the user ask for available trains?
    if any(phrase in text for phrase in ["which train", "how many train", "trains are available", "available train", "give me options", "show trains"]):
        src = slots.get("source")
        dst = slots.get("destination")
        if src and dst:
            train_res = irctc.find_trains(src, dst, slots.get("date") or "tomorrow")
            trains = train_res.get("trains", [])
            if trains:
                options_str = ", ".join([f"{t['name']} ({t['no']})" for t in trains])
                next_question = f"Available trains: {options_str}. Which one would you like?"
                return {
                    "slots": slots,
                    "next_question": next_question,
                    "all_slots_filled": False
                }

    # Pre-check: Did the user ask for available classes?
    if any(phrase in text for phrase in ["which class", "what class", "available class", "classes are available", "what losses", "losses are available", "which coach", "show class", "what coaches"]):
        train_no = slots.get("train_no")
        if train_no:
            classes = ["1A", "2A", "3A", "SL", "CC", "EC"]
            next_question = f"For train {train_no}, available classes are: {', '.join(classes)}. Which class do you want?"
        else:
            next_question = "Available classes are AC 1st Class (1A), 2nd Class (2A), 3rd Class (3A), and Sleeper (SL). Which one do you prefer?"
            
        return {
            "slots": slots,
            "next_question": next_question,
            "all_slots_filled": False
        }
    
    # Extract stations with robust Hinglish & English patterns
    # 1. Define list of stop words to avoid extracting command keywords, classes, dates, etc., as stations
    STOP_WORDS = {
        "tomorrow", "today", "yesterday", "kal", "aaj", "train", "ticket", "book", 
        "cancel", "status", "seat", "avail", "sleeper", "chair", "class", "the", 
        "a", "an", "is", "it", "to", "from", "se", "ko", "jana", "yatri", "naam", 
        "name", "for", "on", "in", "at", "me", "mein", "ek", "do", "tin", "char", 
        "please", "kripya", "yes", "no", "haan", "nahi", "bye", "thanks", "thank",
        "destination", "source", "station", "that", "this", "would", "like", "want",
        "prefer", "go", "going", "travel", "journey", "hi", "hello", "hey",
        "which", "what", "where", "how", "who", "why", "when", "did", "do", "does",
        "had", "have", "has", "i", "you", "he", "she", "they", "we", "me", "my",
        "mine", "your", "yours", "his", "her", "hers", "their", "theirs", "our",
        "ours", "mention", "mentioned", "say", "said", "tell", "told", "ask",
        "asked", "know", "knew", "known", "please", "kindly", "could", "should",
        "would", "can", "may", "might", "must", "shall", "will", "be", "been",
        "being", "am", "are", "was", "were", "suits", "suit", "engineering", "source",
        "station", "stations", "trains", "passenger", "name", "second",
        "find", "search", "khoj", "get", "check", "show", "list", "give", "mujhe",
        "karna", "pnr", "status", "cancel", "mera", "das", "digit", "number", "kar",
        "do", "bhai", "ek", "chalna", "chahiye", "yatra", "confirm", "booking"
    }

    src_extracted = None
    dst_extracted = None
    
    # 2. Try to extract source/destination from explicit prepositional patterns first
    from_to_match = re.search(r"\bfrom\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\b", text)
    se_match = re.search(r"\b([a-zA-Z]+)\s+se\s+([a-zA-Z]+)\b", text)
    
    if from_to_match:
        c1, c2 = from_to_match.group(1), from_to_match.group(2)
        if c1.lower() not in STOP_WORDS and c2.lower() not in STOP_WORDS:
            src_extracted = c1.title()
            dst_extracted = c2.title()
    elif se_match:
        c1, c2 = se_match.group(1), se_match.group(2)
        if c1.lower() not in STOP_WORDS and c2.lower() not in STOP_WORDS:
            src_extracted = c1.title()
            dst_extracted = c2.title()
            
    if not src_extracted:
        from_match = re.search(r"\bfrom\s+([a-zA-Z]+)\b", text)
        se_single_match = re.search(r"\b([a-zA-Z]+)\s+se\b", text)
        if from_match and from_match.group(1).lower() not in STOP_WORDS:
            src_extracted = from_match.group(1).title()
        elif se_single_match and se_single_match.group(1).lower() not in STOP_WORDS:
            src_extracted = se_single_match.group(1).title()
            
    if not dst_extracted:
        to_match = re.search(r"\bto\s+([a-zA-Z]+)\b", text)
        ko_match = re.search(r"\b([a-zA-Z]+)\s+(?:ko|jana)\b", text)
        if to_match and to_match.group(1).lower() not in STOP_WORDS:
            dst_extracted = to_match.group(1).title()
        elif ko_match and ko_match.group(1).lower() not in STOP_WORDS:
            dst_extracted = ko_match.group(1).title()

    if src_extracted:
        slots["source"] = src_extracted
    if dst_extracted:
        slots["destination"] = dst_extracted
        
    # 3. Fallback: If slots are still missing, look for ANY words in user input that look like a station name
    if intent in ("FIND_TRAINS", "BOOK_TICKET") and (not slots.get("source") or not slots.get("destination")):
        potential_stations = []
        cleaned_words = re.findall(r"\b[a-zA-Z]+\b", text)
        for w in cleaned_words:
            w_lower = w.lower()
            if w_lower not in STOP_WORDS and len(w_lower) >= 3:
                if w_lower not in ["sleeper", "chair", "exec"] and w_lower not in ["june", "july", "august", "september"]:
                    potential_stations.append(w.title())
                    
        known_found = [s.title() for s in MOCK_STATIONS if s in text]
        candidates = []
        for s in known_found + potential_stations:
            if s not in candidates:
                candidates.append(s)
                
        if candidates:
            if slots.get("source") and not slots.get("destination"):
                filtered = [c for c in candidates if c.lower() != slots["source"].lower()]
                if filtered:
                    slots["destination"] = filtered[0]
            elif not slots.get("source") and slots.get("destination"):
                filtered = [c for c in candidates if c.lower() != slots["destination"].lower()]
                if filtered:
                    slots["source"] = filtered[0]
            else:
                if len(candidates) >= 2:
                    slots["source"] = candidates[0]
                    slots["destination"] = candidates[1]
                elif len(candidates) == 1:
                    slots["source"] = candidates[0]

    # 4. Index Selection Check
    available_trains = context.get("available_trains", []) if context else []
    if available_trains:
        # Build options matching the frontend logic (train, class) sliced to 4 results
        options = []
        for train in available_trains:
            train_no = train.get("no")
            # Get class details keys if present, otherwise default to classes list
            cls_keys = list(train.get("class_details", {}).keys()) if train.get("class_details") else train.get("classes", [])
            for class_code in cls_keys:
                options.append((train_no, class_code))
        
        # Limit options to top 4 to match frontend layout slice
        options = options[:4]
        
        # Check text for index choices (phonetic and numeric)
        idx = None
        if any(contains_word_or_phrase(text, w) for w in ["first", "1st", "pehla", "pehli", "one", "number one", "option 1", "train 1", "पहला", "पहली", "एक"]):
            idx = 0
        elif any(contains_word_or_phrase(text, w) for w in ["second", "2nd", "dusra", "dusri", "doosra", "doosri", "two", "number two", "option 2", "train 2", "दूसरा", "दूसरी", "दो"]):
            idx = 1
        elif any(contains_word_or_phrase(text, w) for w in ["third", "3rd", "tisra", "tisri", "three", "number three", "option 3", "train 3", "तीसरा", "तीसरी", "तीन"]):
            idx = 2
        elif any(contains_word_or_phrase(text, w) for w in ["fourth", "4th", "chotha", "chautha", "chauthi", "four", "number four", "option 4", "train 4", "चौथा", "चौथी", "चार"]):
            idx = 3
            
        if idx is not None and idx < len(options):
            slots["train_no"] = options[idx][0]
            slots["class_code"] = options[idx][1]

    # Extract class codes with friendly synonyms mapping
    class_mappings = {
        "1a": "1A", "2a": "2A", "3a": "3A", "sl": "SL", "cc": "CC", "ec": "EC",
        "sleeper": "SL", "chair car": "CC", "exec": "EC"
    }
    for key, val in class_mappings.items():
        if key in text:
            slots["class_code"] = val
            
    if "cheaper" in text or "sasta" in text or "cheap" in text:
        train_no = slots.get("train_no") or "12012"
        if train_no in ["12002", "22436", "12012"]:
            slots["class_code"] = "CC"
        else:
            slots["class_code"] = "SL"

    # Extract 10 digit PNR
    pnr_match = re.search(r"\b\d{10}\b", text)
    if pnr_match:
        slots["pnr_number"] = pnr_match.group(0)

    # Extract 5 digit Train No
    train_match = re.search(r"\b\d{5}\b", text)
    if train_match:
        slots["train_no"] = train_match.group(0)

    # Extract passenger name by looking for explicit targets or common nouns in dataset
    known_names = ["amit", "edwin", "john doe", "john"]
    name_found = False
    for name in known_names:
        if name in text:
            slots["passenger_name"] = name.title()
            name_found = True
            break
            
    if not name_found:
        name_match = re.search(r"\b(?:yatri ka naam|yatri|naam|name is|name|passenger is|passenger|for)\s+(?:hai|is)?\s*([a-zA-Z]+)", text)
        if name_match:
            candidate = name_match.group(1)
            # Filter out helper words
            if candidate not in MOCK_STATIONS and candidate not in ["tomorrow", "today", "ticket", "kal", "aaj", "se", "ko", "ka", "hai", "is", "second"]:
                slots["passenger_name"] = candidate.title()

    # Extract Date: tomorrow, today, or general string
    if "tomorrow" in text or "kal" in text:
        slots["date"] = "2026-06-19" # hardcode mock tomorrow relative to current date (Jun 18 2026)
    elif "today" in text or "aaj" in text:
        slots["date"] = "2026-06-18"
    elif not slots.get("date"):
        # Match something like "25th june"
        date_exp = re.search(r"\b\d{1,2}(?:th|st|nd|rd)?\s+(?:june|july|august|september)\b", text)
        if date_exp:
            slots["date"] = date_exp.group(0).title()

    # Check which slots are missing depending on intent
    required = []
    if intent == "BOOK_TICKET":
        required = ["source", "destination", "date", "class_code", "passenger_name"]
    elif intent == "FIND_TRAINS":
        required = ["source", "destination", "date"]
    elif intent == "CHECK_SEAT":
        required = ["train_no", "date", "class_code"]
    elif intent == "CANCEL_TICKET" or intent == "GET_PNR_STATUS":
        required = ["pnr_number"]
    elif intent == "END_CONVERSATION":
        required = []

    missing = [s for s in required if not slots.get(s)]
    all_filled = len(missing) == 0

    next_question = "How can I help you today?"
    if not all_filled:
        next_slot = missing[0]
        if dialect == "Hindi":
            if next_slot == "source":
                next_question = "Main aapki sahayata kar sakta hoon. Aap kis station se yatra shuru karna chahte hain?"
            elif next_slot == "destination":
                next_question = "Bahut badhiya. Aapko kis station tak jana hai?"
            elif next_slot == "date":
                next_question = "Aap kis tareekh ko yatra karna chahte hain?"
            elif next_slot == "class_code":
                next_question = "Aap kis class mein seat book karna chahenge, jaise Sleeper ya 3A?"
            elif next_slot == "passenger_name":
                next_question = "Kripya yatri ka naam batayein."
            elif next_slot == "pnr_number":
                next_question = "Kripya apna das-digit ka PNR number batayein."
            elif next_slot == "train_no":
                next_question = "Yatra ke liye train number kya hai?"
        elif dialect == "English":
            if next_slot == "source":
                next_question = "I can definitely help with that. From which station would you like to start your journey?"
            elif next_slot == "destination":
                next_question = "Great. And what is your destination station?"
            elif next_slot == "date":
                next_question = "What date are you planning to travel?"
            elif next_slot == "class_code":
                next_question = "Which coach class do you prefer, such as Sleeper or 3rd AC?"
            elif next_slot == "passenger_name":
                next_question = "Could I please get the passenger's name for the ticket?"
            elif next_slot == "pnr_number":
                next_question = "Please state your 10-digit PNR number."
            elif next_slot == "train_no":
                next_question = "Could you please provide the 5-digit train number?"
        else: # Hinglish / Default
            if next_slot == "source":
                next_question = "Sure, main booking mein help karunga. Aap kis station se chalna chahte hain?"
            elif next_slot == "destination":
                next_question = "Perfect. Aapko kis station tak jana hai?"
            elif next_slot == "date":
                next_question = "Kis date ko yatra karni hai?"
            elif next_slot == "class_code":
                next_question = "Kaunsa coach class book karna hai? Jaise 3A ya Sleeper."
            elif next_slot == "passenger_name":
                next_question = "Yatri ka naam kya hai?"
            elif next_slot == "pnr_number":
                next_question = "Apna das-digit ka PNR number batayein."
            elif next_slot == "train_no":
                next_question = "Gaadi sankhya (Train number) kya hai?"

    return {
        "slots": slots,
        "next_question": next_question,
        "all_slots_filled": all_filled
    }

def run_mock_brain_step(state: str, user_input: str, context: dict) -> dict:
    """
    Offline rule-based fallback parser.
    """
    if state == "INTENT":
        return mock_classify_intent(user_input)
    elif state == "COLLECT":
        return mock_fill_slots(user_input, context.get("slots", {}), context.get("intent", ""), context.get("dialect", "Hinglish"), context)
    elif state == "CONFIRM":
        text = user_input.lower()
        is_confirmed = True if any(word in text for word in ["yes", "haan", "sure", "confirm", "theek", "okay"]) else False if any(word in text for word in ["no", "na", "cancel", "nahi", "galat"]) else None
        
        intent = context.get("intent", "UNKNOWN")
        if is_confirmed:
            if intent == "BOOK_TICKET":
                resp = "Absolutely, I am booking that ticket now. Please wait a moment."
            elif intent == "FIND_TRAINS":
                resp = "Sure, I am searching for trains now. Please wait."
            else:
                resp = "Absolutely, proceeding with your request now. Please wait."
        elif is_confirmed is False:
            resp = "Understood. I have cancelled the process."
        else:
            if intent == "BOOK_TICKET":
                resp = "Are you ready to proceed with booking? Please say yes or no."
            elif intent == "FIND_TRAINS":
                resp = "Should I proceed with searching trains? Please say yes or no."
            else:
                resp = "Should I proceed? Please say yes or no."
        return {
            "response": resp,
            "is_confirmed": is_confirmed
        }
    elif state == "EXECUTE" or state == "END":
        # Just return a greeting or completion string
        return {
            "response": f"Wonderful, everything is successfully processed! Details: {context.get('result', '')}. Have a safe journey!"
        }
    # Fallback
    return {"response": "Hello, how can I help you today?"}

def run_brain_step(state: str, user_input: str, context: dict) -> dict:
    """
    Executes a single processing step in the brain.
    Depending on configuration, uses Groq Llama 3.1 8B or local rule-based mock engine.
    """
    settings = config_manager.settings
    
    if settings.use_mock_llm:
        return run_mock_brain_step(state, user_input, context)

    # Real LLM Call using Groq
    api_key = settings.groq_api_key
    try:
        if state == "INTENT":
            return call_groq_json(INTENT_SYSTEM_PROMPT, f"User message: {user_input}", api_key)
        elif state == "COLLECT":
            import datetime
            current_date = datetime.date.today().strftime("%Y-%m-%d")
            dialect = context.get("dialect", "Hinglish")
            formatted_prompt = SLOT_FILLER_SYSTEM_PROMPT.replace("{dialect}", dialect)
            available_trains = context.get("available_trains", [])
            
            # Strip out raw_train_data to prevent prompt token limit exhaustion
            clean_trains = []
            for t in available_trains:
                t_clean = t.copy()
                t_clean.pop("raw_train_data", None)
                clean_trains.append(t_clean)
            
            user_prompt = (
                f"Current Date: {current_date}\n"
                f"Current slots table: {json.dumps(context.get('slots', {}))}\n"
                f"Active Intent: {context.get('intent')}\n"
                f"Selected Language Dialect: {dialect}\n"
                f"Available Trains Context: {json.dumps(clean_trains)}\n"
                f"User input: {user_input}"
            )
            res = call_groq_json(formatted_prompt, user_prompt, api_key)
            
            # Programmatically compute all_slots_filled in Python to prevent LLM inconsistencies
            slots_returned = res.get("slots", {})
            
            # Programmatically clean up class_code slot synonyms
            class_code = slots_returned.get("class_code")
            if class_code:
                cc_clean = str(class_code).strip().lower()
                class_mapping = {
                    "chair car": "CC", "cc": "CC", "chaircar": "CC",
                    "executive class": "EC", "exec": "EC", "ec": "EC", "executive": "EC",
                    "sleeper": "SL", "sl": "SL",
                    "first ac": "1A", "1st ac": "1A", "1a": "1A",
                    "second ac": "2A", "2nd ac": "2A", "2a": "2A",
                    "third ac": "3A", "3rd ac": "3A", "3a": "3A"
                }
                slots_returned["class_code"] = class_mapping.get(cc_clean, class_code)
                
            intent = context.get("intent", "")
            required_slots = []
            if intent == "BOOK_TICKET":
                required_slots = ["source", "destination", "date", "class_code", "passenger_name"]
            elif intent == "FIND_TRAINS":
                required_slots = ["source", "destination", "date"]
            elif intent == "CHECK_SEAT":
                required_slots = ["train_no", "date", "class_code"]
            elif intent == "CANCEL_TICKET" or intent == "GET_PNR_STATUS":
                required_slots = ["pnr_number"]
            elif intent == "END_CONVERSATION":
                required_slots = []
                
            def is_filled(val):
                return val is not None and str(val).strip() != "" and str(val).lower() not in ["null", "none"]
                
            missing = [s for s in required_slots if not is_filled(slots_returned.get(s))]
            res["all_slots_filled"] = len(missing) == 0
            return res
            
        elif state == "CONFIRM":
            intent = context.get("intent", "UNKNOWN")
            user_prompt = f"Intent: {intent}\nSlots details: {json.dumps(context.get('slots', {}))}\nUser confirmation text: {user_input}"
            formatted_prompt = CONFIRMATION_SYSTEM_PROMPT.replace("{details}", json.dumps(context.get('slots', {}))).replace("{dialect}", context.get("dialect", "Hinglish")).replace("{intent}", intent)
            return call_groq_json(formatted_prompt, user_prompt, api_key)
        elif state == "EXECUTE" or state == "END":
            res_obj = context.get('result', {})
            if isinstance(res_obj, dict) and "trains" in res_obj:
                res_obj_clean = res_obj.copy()
                clean_list = []
                for t in res_obj.get("trains", []):
                    t_clean = t.copy()
                    t_clean.pop("raw_train_data", None)
                    clean_list.append(t_clean)
                res_obj_clean["trains"] = clean_list
                res_obj = res_obj_clean
                
            user_prompt = f"Execution result: {json.dumps(res_obj)}"
            formatted_prompt = EXECUTE_SYSTEM_PROMPT.replace("{result}", json.dumps(res_obj)).replace("{dialect}", context.get("dialect", "Hinglish"))
            return call_groq_json(formatted_prompt, user_prompt, api_key)
    except Exception as e:
        logger.error(f"Groq execution failed, falling back to mock brain state runner. Error: {e}")
        # Fall back to mock runner for this step, but do not set settings.use_mock_llm permanently.
        return run_mock_brain_step(state, user_input, context)
