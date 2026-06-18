import time
import logging
from ..tools import irctc, sms
from .llm import run_brain_step

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
        self.history = []
        self.latencies = []
        self.start_time = time.time()
        self.booking_success = False
        
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
        
        # Log inbound message
        session.add_history("inbound", user_input)
        
        response_text = ""
        
        # State machine processing
        if session.state == "GREET":
            # Greeting explicitly asking which language to speak in - English only
            response_text = "Hello! Welcome to the train booking service. Which language would you prefer to talk in: English, Hindi, or Hinglish?"
            session.state = "LANGUAGE"
            
        elif session.state == "LANGUAGE":
            # 1. Parse language selection (supporting Devnagari and phonetic equivalents)
            text = user_input.lower()
            
            is_hindi = any(word in text for word in ["hindi", "hindee", "हिंदी", "हिन्दी", "हिं"])
            is_english = any(word in text for word in ["english", "inglish", "eng", "इंग्लिश", "अंग्रेजी", "अँग्रेजी", "इन्गलिश"])
            is_hinglish = any(word in text for word in ["hinglish", "mix", "both", "dono", "मिश्रित", "मिक्स", "दोनों"])
            
            if is_hinglish:
                session.dialect = "Hinglish"
                session.state = "INTENT"
                response_text = "Perfect, ab Hinglish mein baat karte hain. Aapko train book karni hai ya status check karna hai?"
            elif is_hindi:
                session.dialect = "Hindi"
                session.state = "INTENT"
                response_text = "Theek hai, ab hum Hindi mein baat karenge. Main aapki train booking mein kya sahayata kar sakta hoon?"
            elif is_english:
                session.dialect = "English"
                session.state = "INTENT"
                response_text = "Sure, let's speak in English. How can I assist you with your train journey today?"
            else:
                # 2. Direct bypass check: did the user ignore language question and speak their request directly?
                result = run_brain_step("INTENT", user_input, {})
                intent = result.get("intent", "UNKNOWN")
                if intent != "UNKNOWN":
                    session.intent = intent
                    session.dialect = result.get("language_detected", "Hinglish")
                    session.state = "COLLECT"
                    collect_result = run_brain_step("COLLECT", user_input, {"slots": session.slots, "intent": session.intent})
                    session.slots = collect_result.get("slots", session.slots)
                    
                    if collect_result.get("all_slots_filled", False):
                        session.state = "CONFIRM"
                        confirm_result = run_brain_step("CONFIRM", "", {"slots": session.slots, "dialect": session.dialect})
                        response_text = confirm_result.get("response", "Please confirm details.")
                    else:
                        response_text = collect_result.get("next_question", "Please provide details.")
                else:
                    # Unrecognized choice. Prompt again.
                    response_text = "Please choose a language: English, Hindi, or Hinglish."
            
        elif session.state == "INTENT":
            # Classify intent
            result = run_brain_step("INTENT", user_input, {})
            session.dialect = result.get("language_detected", "Hinglish")
            intent = result.get("intent", "UNKNOWN")
            
            if intent != "UNKNOWN":
                session.intent = intent
                session.state = "COLLECT"
                # Seed slots using this initial turn input
                collect_result = run_brain_step("COLLECT", user_input, {"slots": session.slots, "intent": session.intent})
                session.slots = collect_result.get("slots", session.slots)
                
                if collect_result.get("all_slots_filled", False):
                    session.state = "CONFIRM"
                    # Generate confirmation question
                    confirm_result = run_brain_step("CONFIRM", "", {"slots": session.slots, "dialect": session.dialect})
                    response_text = confirm_result.get("response", "Please confirm details.")
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
            # Fill remaining slots
            collect_result = run_brain_step("COLLECT", user_input, {"slots": session.slots, "intent": session.intent})
            session.slots = collect_result.get("slots", session.slots)
            
            if collect_result.get("all_slots_filled", False):
                session.state = "CONFIRM"
                confirm_result = run_brain_step("CONFIRM", "", {"slots": session.slots, "dialect": session.dialect})
                response_text = confirm_result.get("response", "Please confirm details.")
            else:
                response_text = collect_result.get("next_question", "Please provide details.")
                
        elif session.state == "CONFIRM":
            # Run confirmation evaluation
            confirm_result = run_brain_step("CONFIRM", user_input, {"slots": session.slots, "dialect": session.dialect})
            is_confirmed = confirm_result.get("is_confirmed", None)
            
            if is_confirmed is True:
                # Transition to EXECUTE
                session.state = "EXECUTE"
                response_text = self._execute_tool(session)
            elif is_confirmed is False:
                # Transition to END
                session.state = "END"
                if session.dialect == "Hindi":
                    response_text = "Request cancel kar di gayi hai. Dhanyawaad."
                elif session.dialect == "Hinglish":
                    response_text = "Theek hai, process cancel kar diya hai. Thank you!"
                else:
                    response_text = "Okay, the process has been cancelled. Thank you."
            else:
                # Repeat confirmation prompt
                response_text = confirm_result.get("response", "Shall I proceed?")
                
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

    def _execute_tool(self, session: SessionState) -> str:
        """
        Executes the backend tools based on filled slots and current intent.
        Transitions session state to END.
        """
        intent = session.intent
        slots = session.slots
        result = {}
        
        try:
            if intent == "BOOK_TICKET":
                # Create passengers structure
                passenger = {"name": slots.get("passenger_name", "Unknown"), "age": 30, "gender": "M"}
                res = irctc.book_ticket(
                    train_no=slots.get("train_no") or "12626", # Fallback to Kerala Express if missing
                    date=slots.get("date", "2026-06-25"),
                    class_code=slots.get("class_code", "3A"),
                    passengers=[passenger],
                    payment_confirmed=True
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
                    train_no=slots.get("train_no") or "12626",
                    date=slots.get("date"),
                    class_code=slots.get("class_code", "3A")
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
                    result = irctc.get_live_train_info(slots.get("train_no") or "12626")
                    
        except Exception as e:
            logger.error(f"Error executing tool in FSM: {e}")
            result = {"error": "Internal system error occurred during execution."}
            
        session.state = "END"
        
        # Synthesize final message using LLM
        exec_result = run_brain_step("EXECUTE", "", {"result": result, "dialect": session.dialect})
        return exec_result.get("response", f"Action complete. Details: {result}")

fsm_coordinator = FSMCoordinator()
