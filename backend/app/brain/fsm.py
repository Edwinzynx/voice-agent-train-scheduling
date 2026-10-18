import time
import logging
import re
from ..tools import irctc, sms
from .llm import run_brain_step
from .results import result_summary, schedule_followup
from .validation import REQUIRED_SLOTS, confirmation_decision, date_expression, normalize_date

logger = logging.getLogger(__name__)

class SessionState:
    def __init__(self, session_id: str, caller_number: str = "WebRTC-User"):
        self.session_id = session_id
        self.caller_number = caller_number
        self.state = "GREET"
        self.intent = None
        self.slots = {
            "source": None,
            "destination": None,
            "date": None,
            "class_code": None,
            "passenger_name": None,
            "pnr_number": None,
            "train_no": None
        }
        self.dialect = "Hinglish"
        self.language_selected = False
        self.history = []
        self.latencies = []
        self.start_time = time.time()
        self.booking_success = False
        self.available_trains = []
        self.last_action_result = None
        self.search_key = None
        
    def add_history(self, direction: str, text: str, latency_ms: float = 0.0):
        self.history.append({
            "direction": direction,
            "text": text,
            "state": self.state,
            "timestamp": time.time(),
            "slots": self.slots.copy(),
            "latency_ms": latency_ms
        })
        if latency_ms > 0:
            self.latencies.append(latency_ms)

    def get_latency_metrics(self):
        if not self.latencies:
            return 0.0, 0.0, 0.0
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        p50 = sorted_lat[int(n * 0.5)]
        p90 = sorted_lat[int(n * 0.9)] if n > 1 else sorted_lat[-1]
        p99 = sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[-1]
        return p50, p90, p99

class FSMCoordinator:
    def __init__(self):
        self.sessions = {}

    def get_or_create_session(self, session_id: str, caller_number: str = "WebRTC-User") -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id, caller_number)
        return self.sessions[session_id]

    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def process_turn(self, session_id: str, user_input: str) -> str:
        """
        Main entry point for processing a single user turn.
        Returns the spoken response text from the agent.
        """
        start_time = time.time()
        session = self.get_or_create_session(session_id)
        session.last_action_result = None
        if session.state in ("INTENT", "COLLECT", "CONFIRM") and session.available_trains:
            answer = schedule_followup(user_input, session.available_trains, session.slots)
            if answer:
                session.add_history("inbound", user_input)
                session.add_history("outbound", answer, (time.time() - start_time) * 1000)
                return answer
        if re.search(r"already (?:told|said|gave)|pehle.*bataya|पहले.*बताया", user_input, re.I) and session.slots.get("date"):
            answer = f"Yes, I have {session.slots.get('source')} to {session.slots.get('destination')} for {session.slots['date']}."
            if session.available_trains:
                answer += " Please tell me the train name or number for its timings."
            session.add_history("inbound", user_input)
            session.add_history("outbound", answer, (time.time() - start_time) * 1000)
            return answer
        if session.state == "INTENT" and session.available_trains:
            named = any(t.get("name") and t["name"].casefold() in user_input.casefold() for t in session.available_trains)
            numbered = re.search(r"\b\d{5}\b", user_input)
            ordinal = re.fullmatch(r"(?:choose |select |the |option |train )*(first|second|third|fourth|1st|2nd|3rd|4th)(?: one| option| train| please)*[.!]?", user_input.strip().lower())
            if named or numbered or ordinal:
                session.intent = "CHECK_SEAT"
                session.state = "COLLECT"
        
        # Log inbound message
        session.add_history("inbound", user_input)
        
        response_text = ""
        
        # State machine processing
        if session.state == "GREET":
            # Greeting explicitly asking which language to speak in - English only
            response_text = "Hello! Welcome to LocoVoice, your train journey assistant. Which language would you prefer to talk in: English, Hindi, or Hinglish?"
            session.state = "LANGUAGE"
            
        elif session.state == "LANGUAGE":
            # 1. Parse language selection (supporting Devnagari and phonetic equivalents)
            text = user_input.lower()
            
            is_hindi = any(word in text for word in ["hindi", "hindee", "हिंदी", "हिन्दी", "हिं"])
            is_english = any(word in text for word in ["english", "inglish", "eng", "इंग्लिश", "अंग्रेजी", "अँग्रेजी", "इन्गलिश"])
            is_hinglish = any(word in text for word in ["hinglish", "mix", "both", "dono", "मिश्रित", "मिक्स", "दोनों"])
            
            if is_hinglish:
                session.dialect = "Hinglish"
                session.language_selected = True
                session.state = "INTENT"
                response_text = "Perfect, ab Hinglish mein baat karte hain. Aapko train book karni hai ya status check karna hai?"
            elif is_hindi:
                session.dialect = "Hindi"
                session.language_selected = True
                session.state = "INTENT"
                response_text = "Theek hai, ab hum Hindi mein baat karenge. Main aapki train booking mein kya sahayata kar sakta hoon?"
            elif is_english:
                session.dialect = "English"
                session.language_selected = True
                session.state = "INTENT"
                response_text = "Sure, let's speak in English. How can I assist you with your train journey today?"
            else:
                # 2. Direct bypass check: did the user ignore language question and speak their request directly?
                result = run_brain_step("INTENT", user_input, self._context(session))
                intent = result.get("intent", "UNKNOWN")
                if intent == "END_CONVERSATION":
                    session.state = "END"
                    return "Thank you for using LocoVoice. Goodbye!"
                if intent in REQUIRED_SLOTS:
                    unavailable = self._unavailable_intent(intent)
                    if unavailable:
                        session.state = "INTENT"
                        return unavailable
                    session.intent = intent
                    session.dialect = result.get("language_detected", "Hinglish")
                    session.language_selected = True
                    session.state = "COLLECT"
                    collect_result = run_brain_step("COLLECT", user_input, self._context(session))
                    collect_result = self._validate_collection(session, user_input, collect_result)
                    
                    if collect_result.get("all_slots_filled", False):
                        session.state = "CONFIRM"
                        response_text = self._confirmation_prompt(session)
                    else:
                        response_text = collect_result.get("next_question", "Please provide details.")
                else:
                    # Unrecognized choice. Prompt again.
                    response_text = "Please choose a language: English, Hindi, or Hinglish."
            
        elif session.state == "INTENT":
            # Classify intent
            result = run_brain_step("INTENT", user_input, self._context(session))
            if not getattr(session, "language_selected", False):
                session.dialect = result.get("language_detected", "Hinglish")
                session.language_selected = True
            intent = result.get("intent", "UNKNOWN")
            
            if intent == "END_CONVERSATION":
                session.state = "END"
                if session.dialect == "Hindi":
                    response_text = "Hamari seva ka upyog karne ke liye dhanyawaad. Aapka din shubh ho! Alvida."
                elif session.dialect == "Hinglish":
                    response_text = "Train booking agent ko use karne ke liye thank you. Have a great day! Bye bye!"
                else:
                    response_text = "Thank you for using our train booking service. Have a wonderful day and a safe journey! Goodbye."
            elif intent in REQUIRED_SLOTS:
                unavailable = self._unavailable_intent(intent)
                if unavailable:
                    return unavailable
                # A follow-up belongs to the existing journey until the user changes it.
                session.intent = intent
                if intent == "FIND_TRAINS":
                    session.slots["train_no"] = None
                    session.slots["class_code"] = None
                session.last_action_result = None
                session.state = "COLLECT"
                # Seed slots using this initial turn input
                collect_result = run_brain_step("COLLECT", user_input, self._context(session))
                collect_result = self._validate_collection(session, user_input, collect_result)
                
                if collect_result.get("all_slots_filled", False):
                    session.state = "CONFIRM"
                    # Generate confirmation question
                    response_text = self._confirmation_prompt(session)
                else:
                    response_text = collect_result.get("next_question", "Please provide details.")
            else:
                # Ask user to clarify
                if session.dialect == "Hindi":
                    response_text = "Kripya batayein, kya aap train search, seat availability, ticket booking ya cancel karna chahte hain?"
                elif session.dialect == "Hinglish":
                    response_text = "Main aapki train search, ticket booking ya status check karne mein help kar sakta hoon. Aapko kya karna hai?"
                else:
                    response_text = "I can help you search trains, check seat availability, book, or cancel tickets. What would you like to do?"
                    
        elif session.state == "COLLECT":
            # A date-only answer needs validation, not two provider requests.
            expression = date_expression(user_input)
            if expression and user_input.strip().rstrip('.!?').casefold() == expression.casefold():
                result = self._validate_collection(session, user_input, {"slots": session.slots.copy()})
                if result.get("all_slots_filled"):
                    session.state = "CONFIRM"
                    response_text = self._confirmation_prompt(session)
                else:
                    missing = next((k for k in REQUIRED_SLOTS[session.intent] if not session.slots.get(k)), "details")
                    response_text = result.get("next_question", f"Please provide {missing.replace('_', ' ')}.")
                session.add_history("outbound", response_text, (time.time() - start_time) * 1000)
                return response_text
            # 1. Check if the user intends to end the call or switch tasks
            intent_result = run_brain_step("INTENT", user_input, self._context(session))
            new_intent = intent_result.get("intent", "UNKNOWN")
            
            # Determine if we should switch intent
            should_switch_intent = False
            if new_intent == "END_CONVERSATION":
                should_switch_intent = True
            elif new_intent in ["CANCEL_TICKET", "GET_PNR_STATUS"]:
                should_switch_intent = True
            elif session.intent in ["FIND_TRAINS", "CHECK_SEAT", "UNKNOWN"] and new_intent == "BOOK_TICKET":
                # Only switch if the user explicitly mentions booking/ticket keywords to prevent misclassification of slot answers
                text_lower = user_input.lower()
                booking_keywords = ["book", "booking", "ticket", "reserve", "yatra", "kar do", "confirm"]
                if any(kw in text_lower for kw in booking_keywords):
                    should_switch_intent = True
            elif session.intent == "UNKNOWN" and new_intent != "UNKNOWN":
                should_switch_intent = True
                
            if new_intent == "END_CONVERSATION" and should_switch_intent:
                session.state = "END"
                if session.dialect == "Hindi":
                    response_text = "Hamari seva ka upyog karne ke liye dhanyawaad. Aapka din shubh ho! Alvida."
                elif session.dialect == "Hinglish":
                    response_text = "Train booking agent ko use karne ke liye thank you. Have a great day! Bye bye!"
                else:
                    response_text = "Thank you for using our train booking service. Have a wonderful day and a safe journey! Goodbye."
                
                latency_ms = (time.time() - start_time) * 1000
                session.add_history("outbound", response_text, latency_ms)
                return response_text
                
            elif should_switch_intent and new_intent != session.intent:
                unavailable = self._unavailable_intent(new_intent)
                if unavailable:
                    return unavailable
                prev_source = session.slots.get("source")
                prev_destination = session.slots.get("destination")
                prev_date = session.slots.get("date")
                
                session.intent = new_intent
                
                if new_intent == "BOOK_TICKET":
                    session.slots = {
                        "source": prev_source,
                        "destination": prev_destination,
                        "date": prev_date,
                        "class_code": None,
                        "passenger_name": None,
                        "pnr_number": None,
                        "train_no": None
                    }
                else:
                    session.slots = {
                        "source": None,
                        "destination": None,
                        "date": None,
                        "class_code": None,
                        "passenger_name": None,
                        "pnr_number": None,
                        "train_no": None
                    }
                session.available_trains = []
                session.last_action_result = None
                
            available_trains = session.available_trains
            context = {
                "slots": session.slots,
                "intent": session.intent,
                "dialect": session.dialect,
                "available_trains": available_trains,
                "history": session.history[-6:]
            }
            session.available_trains = available_trains
            # Fill remaining slots
            collect_result = run_brain_step("COLLECT", user_input, context)
            collect_result = self._validate_collection(session, user_input, collect_result)
            
            if collect_result.get("all_slots_filled", False):
                session.state = "CONFIRM"
                response_text = self._confirmation_prompt(session)
            else:
                response_text = collect_result.get("next_question", "Please provide details.")
                
        elif session.state == "CONFIRM":
            # Run confirmation evaluation
            is_confirmed = confirmation_decision(user_input)
            
            if is_confirmed is True:
                # Transition to EXECUTE
                session.state = "EXECUTE"
                response_text = self._execute_tool(session)
            elif is_confirmed is False:
                session.state = "COLLECT"
                response_text = "I haven't proceeded. Which detail would you like to change?"
                if re.search(r"change|instead|actually|correct|replace|badal|बदल", user_input, re.I) or date_expression(user_input):
                    result = run_brain_step("COLLECT", user_input, {"slots": session.slots, "intent": session.intent, "dialect": session.dialect, "available_trains": session.available_trains})
                    result = self._validate_collection(session, user_input, result)
                    response_text = result.get("next_question", response_text)
                    if result.get("all_slots_filled"):
                        session.state = "CONFIRM"
                        response_text = self._confirmation_prompt(session)
            else:
                response_text = "I haven't proceeded. Please say yes to confirm, or tell me which detail to change."
                if date_expression(user_input) or re.search(r"\b(?:my name|from|to|class|train \d{5})\b", user_input, re.I):
                    session.state = "COLLECT"
                    result = run_brain_step("COLLECT", user_input, {"slots": session.slots, "intent": session.intent, "dialect": session.dialect, "available_trains": session.available_trains})
                    result = self._validate_collection(session, user_input, result)
                    response_text = result.get("next_question", response_text)
                    if result.get("all_slots_filled"):
                        session.state = "CONFIRM"
                        response_text = self._confirmation_prompt(session)
                
        elif session.state == "EXECUTE":
            # Safeguard if reached directly
            response_text = self._execute_tool(session)
            
        elif session.state == "END":
            if session.dialect == "Hindi":
                response_text = "Hamari seva ka upyog karne ke liye dhanyawaad. Bye bye!"
            elif session.dialect == "Hinglish":
                response_text = "Train booking agent ko use karne ke liye thank you. Have a great day!"
            else:
                response_text = "Thank you for using our service. Have a safe journey!"
                
        # Calculate turn latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log outbound response
        session.add_history("outbound", response_text, latency_ms)
        
        return response_text

    def _context(self, session):
        return {"slots": session.slots.copy(), "intent": session.intent,
                "dialect": session.dialect, "available_trains": session.available_trains,
                "history": session.history[-6:]}

    def _confirmation_prompt(self, session):
        details = ", ".join(f"{key.replace('_', ' ')}: {session.slots[key]}" for key in REQUIRED_SLOTS[session.intent])
        action = session.intent.lower().replace("_", " ")
        if session.dialect == "Hindi":
            return f"कृपया पुष्टि करें: {action}, {details}। क्या मैं आगे बढ़ूँ?"
        if session.dialect == "Hinglish":
            return f"Please confirm karein: {action}, {details}. Kya main proceed karun?"
        return f"Please confirm {action}: {details}. Shall I proceed?"

    def _unavailable_intent(self, intent):
        features = {"BOOK_TICKET": "Ticket booking", "CANCEL_TICKET": "Ticket cancellation", "GET_PNR_STATUS": "PNR and running status"}
        if intent in features and not irctc.simulation_enabled():
            return irctc.service_unavailable(features[intent])["error"]
        return None

    def _validate_collection(self, session, user_input, result):
        previous = session.slots.copy()
        proposed = result.get("slots")
        if not isinstance(proposed, dict):
            raise RuntimeError("The conversation service returned invalid details. Please try again.")
        slots = previous.copy()
        for key in previous:
            value = proposed.get(key)
            if isinstance(value, (str, int)) and str(value).strip().lower() not in ("", "none", "null"):
                slots[key] = str(value).strip()
        session.slots = slots
        error = None
        expression = date_expression(user_input)
        if expression or slots.get("date"):
            try:
                slots["date"] = normalize_date(expression or slots["date"])
            except ValueError as exc:
                slots["date"] = None
                error = str(exc)
        changed = any(previous.get(k) != slots.get(k) for k in ("source", "destination", "date"))
        if changed:
            session.available_trains = []
            session.search_key = None
        # Preserve only a previous choice or a train explicitly named in this turn.
        slots["train_no"] = None if changed else previous.get("train_no")
        match = re.search(r"\b\d{5}\b", user_input)
        if match:
            slots["train_no"] = match.group(0)
        else:
            matches = [t for t in session.available_trains if t.get("name") and t["name"].casefold() in user_input.casefold()]
            if len(matches) == 1:
                slots["train_no"] = str(matches[0]["no"])
            ordinal = re.fullmatch(r"(?:choose |select |book |the |option |train )*(first|second|third|fourth|1st|2nd|3rd|4th|pehli|dusri|teesri|chauthi)(?: one| option| train| please| wala| wali)*[.!]?", user_input.strip().lower())
            if ordinal:
                indexes = {"first": 0, "1st": 0, "pehli": 0, "second": 1, "2nd": 1, "dusri": 1, "third": 2, "3rd": 2, "teesri": 2, "fourth": 3, "4th": 3, "chauthi": 3}
                options = [(str(t["no"]), code) for t in session.available_trains for code in t.get("classes", [])][:4]
                index = indexes[ordinal.group(1)]
                if index < len(options):
                    slots["train_no"], slots["class_code"] = options[index]
        if slots.get("class_code"):
            slots["class_code"] = slots["class_code"].upper()
        explicit_class = re.search(r"\bclass\s+(1A|2A|3A|3E|SL|CC|EC|2S)\b", user_input, re.I)
        if explicit_class:
            slots["class_code"] = explicit_class.group(1).upper()
        if not error and session.intent in ("BOOK_TICKET", "CHECK_SEAT"):
            error = self._validate_selected_train(session)
        missing = [k for k in REQUIRED_SLOTS.get(session.intent, []) if not slots.get(k)]
        result["slots"] = slots
        result["all_slots_filled"] = not missing and not error
        if error:
            result["next_question"] = error
        elif missing and missing[0] == "train_no":
            result["next_question"] = "Please choose a train from the results, or say its five-digit train number."
        return result

    def _validate_selected_train(self, session, refresh=False):
        slots = session.slots
        key = tuple(slots.get(k) for k in ("source", "destination", "date"))
        if not all(key):
            return None
        if refresh or session.search_key != key or not session.available_trains:
            result = irctc.find_trains(*key)
            if not result.get("success"):
                session.available_trains = []
                session.search_key = None
                return result.get("error", "Train search is temporarily unavailable.")
            session.available_trains = result["trains"]
            session.search_key = key
        if slots.get("train_no"):
            selected = next((t for t in session.available_trains if str(t["no"]) == slots["train_no"]), None)
            if not selected:
                slots["train_no"] = None
                return "That train is not available for this route and date. Please select a listed train."
            if slots.get("class_code") and slots["class_code"] not in selected.get("classes", []):
                slots["class_code"] = None
                return "That class is not offered on this train. Please select one of its listed classes."
        return None

    def select_train(self, session_id, train_no, class_code):
        session = self.get_or_create_session(session_id)
        selected = next((t for t in session.available_trains if str(t["no"]) == str(train_no)), None)
        if not selected or class_code not in selected.get("classes", []):
            raise ValueError("That selection is no longer available. Please search again.")
        if session.state not in ("INTENT", "COLLECT", "CONFIRM"):
            raise ValueError("Please search trains before making a selection.")
        if session.intent == "FIND_TRAINS":
            session.intent = "CHECK_SEAT"
        session.state = "COLLECT"
        text = f"Choose train {train_no} class {class_code}"
        session.last_action_result = None
        session.add_history("inbound", text)
        result = self._validate_collection(session, text, {"slots": session.slots.copy()})
        if result.get("all_slots_filled"):
            session.state = "CONFIRM"
            answer = self._confirmation_prompt(session)
        else:
            answer = result.get("next_question", "Please provide the missing journey details.")
        session.add_history("outbound", answer)
        return answer

    def _execute_tool(self, session: SessionState) -> str:
        """
        Executes the backend tools based on filled slots and current intent.
        Transitions session state to END.
        """
        intent = session.intent
        slots = session.slots
        result = {}
        missing = [key for key in REQUIRED_SLOTS.get(intent, []) if not slots.get(key)]
        if missing:
            session.state = "COLLECT"
            return f"Please provide {missing[0].replace('_', ' ')} before proceeding."
        try:
            if slots.get("date"):
                slots["date"] = normalize_date(slots["date"])
        except ValueError as exc:
            session.state = "COLLECT"
            session.slots["date"] = None
            return str(exc)
        if intent in ("BOOK_TICKET", "CHECK_SEAT"):
            error = self._validate_selected_train(session, refresh=True)
            if error:
                session.state = "COLLECT"
                return error
        
        try:
            if intent == "BOOK_TICKET":
                # Create passengers structure
                passenger = {"name": slots["passenger_name"]}
                res = irctc.book_ticket(
                    train_no=slots["train_no"],
                    date=slots["date"],
                    class_code=slots["class_code"],
                    passengers=[passenger],
                    payment_confirmed=True,
                    src=slots["source"],
                    dst=slots["destination"]
                )
                if res.get("success", False):
                    result = res["booking"]
                    session.booking_success = True
                    sms.send_booking_sms(session.caller_number, result)
                else:
                    result = {"error": res.get("error", "Booking failed")}
                    
            elif intent == "FIND_TRAINS":
                result = irctc.find_trains(
                    src=slots.get("source"),
                    dst=slots.get("destination"),
                    date=slots.get("date")
                )
                
            elif intent == "CHECK_SEAT":
                result = irctc.check_seat_availability(
                    train_no=slots["train_no"],
                    date=slots.get("date"),
                    class_code=slots.get("class_code", "3A"),
                    src=slots.get("source"),
                    dst=slots.get("destination")
                )
                
            elif intent == "CANCEL_TICKET":
                res = irctc.cancel_ticket(pnr=slots.get("pnr_number"))
                if res.get("success", False):
                    result = res
                    session.booking_success = True
                    sms.send_cancellation_sms(session.caller_number, slots.get("pnr_number"), res.get("refund_amount", 0.0))
                else:
                    result = {"error": res.get("error", "Cancellation failed")}
                    
            elif intent == "GET_PNR_STATUS":
                pnr = slots.get("pnr_number")
                if pnr:
                    result = irctc.get_pnr_status(pnr)
                else:
                    result = {"success": False, "error": "Please provide a PNR number."}
                    
        except Exception as e:
            logger.error(f"Error executing tool in FSM: {e}")
            result = {"error": "Internal system error occurred during execution."}
            
        session.last_action_result = result
        session.state = "INTENT"
        if "trains" in result:
            session.available_trains = result["trains"]
            session.search_key = tuple(slots.get(k) for k in ("source", "destination", "date"))
        if result.get("success"):
            session.booking_success = True
        if result.get("error") or result.get("success") is False:
            return result.get("error", "The action could not be completed.")
        
        # Read actual results directly: no extra prompt, quota cost, or invented facts.
        return result_summary(result, slots, session.dialect)

fsm_coordinator = FSMCoordinator()
