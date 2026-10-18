"""Isolated regressions: no speech, LLM, or railway provider requests."""
import pytest

from app.brain import fsm, validation


@pytest.mark.parametrize("initial_state", ["LANGUAGE", "INTENT", "COLLECT"])
@pytest.mark.parametrize("fragment_intent", ["UNKNOWN", "BOOK_TICKET"])
def test_unavailable_booking_keeps_fragmented_route(monkeypatch, initial_state, fragment_intent):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session("fragment")
    session.state = initial_state
    session.intent = "FIND_TRAINS" if initial_state == "COLLECT" else None
    session.dialect = "Hindi"
    session.language_selected = initial_state != "LANGUAGE"
    monkeypatch.setattr(fsm.irctc, "simulation_enabled", lambda: False)
    monkeypatch.setattr(fsm.irctc, "book_ticket", lambda **kw: pytest.fail("Booking must remain unavailable"))
    searches = []
    monkeypatch.setattr(fsm.irctc, "find_trains", lambda **kw: searches.append(kw) or {"success": True, "trains": []})
    contexts = []

    def brain(state, text, context):
        if state == "INTENT":
            return {"intent": fragment_intent if text == "चंडीगढ़ की।" else "BOOK_TICKET", "language_detected": "Hindi"}
        contexts.append(context)
        assert context["intent"] == "FIND_TRAINS"
        if text == "चंडीगढ़ की।":
            assert context["slots"]["source"] == "Delhi"
            assert any("दिल्ली से" in item["text"] for item in context["history"])
            return {"slots": {"source": None, "destination": "Chandigarh"}}
        return {"slots": {"source": "Delhi"}}

    monkeypatch.setattr(fsm, "run_brain_step", brain)
    answer = coordinator.process_turn("fragment", "मुझे एक ट्रेन की टिकट बुक करनी है दिल्ली से")
    assert "टिकट बुक नहीं कर सकती" in answer and "किस स्टेशन तक" in answer
    assert session.state == "COLLECT" and session.slots["source"] == "Delhi"
    answer = coordinator.process_turn("fragment", "चंडीगढ़ की।")
    assert "तारीख" in answer and "टिकट बुक नहीं कर सकती" not in answer
    assert session.slots["source"] == "Delhi" and session.slots["destination"] == "Chandigarh"
    assert session.dialect == "Hindi" and len(contexts) == 2
    answer = coordinator.process_turn("fragment", "कल")
    assert session.state == "CONFIRM" and "ट्रेन खोजने" in answer
    assert "टिकट बुक करने" not in answer and session.slots["passenger_name"] is None
    assert not searches
    coordinator.process_turn("fragment", "हाँ")
    assert searches == [{"src": "Delhi", "dst": "Chandigarh", "date": validation.normalize_date("tomorrow")}]
    assert session.intent == "FIND_TRAINS"


@pytest.mark.parametrize("initial_state", ["INTENT", "COLLECT"])
def test_booking_redirect_retains_selected_train_and_date(monkeypatch, initial_state):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session("selection")
    session.state = initial_state
    session.intent = "CHECK_SEAT"
    session.dialect = "English"
    session.language_selected = True
    session.slots.update(source="Delhi", destination="Chandigarh", date=validation.normalize_date("tomorrow"), train_no="12012")
    session.available_trains = [{"no": "12012", "name": "Shatabdi", "classes": ["CC", "EC"]}]
    session.search_key = tuple(session.slots[k] for k in ("source", "destination", "date"))
    before = session.slots.copy()
    monkeypatch.setattr(fsm.irctc, "simulation_enabled", lambda: False)
    monkeypatch.setattr(fsm.irctc, "find_trains", lambda *a, **kw: pytest.fail("Known route should not be searched again"))
    monkeypatch.setattr(fsm, "run_brain_step", lambda state, text, context:
                        {"intent": "BOOK_TICKET"} if state == "INTENT" else {"slots": {}})
    answer = coordinator.process_turn("selection", "Book a ticket please")
    assert "can't book tickets" in answer and "Which class" in answer
    assert session.slots == before and session.intent == "CHECK_SEAT"


@pytest.mark.parametrize("intent", ["CANCEL_TICKET", "GET_PNR_STATUS"])
def test_other_unavailable_services_are_not_redirected_to_search(monkeypatch, intent):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session("unavailable")
    session.state = "INTENT"
    session.dialect = "English"
    session.language_selected = True
    monkeypatch.setattr(fsm.irctc, "simulation_enabled", lambda: False)
    monkeypatch.setattr(fsm, "run_brain_step", lambda *a: {"intent": intent})
    answer = coordinator.process_turn("unavailable", "ticket status")
    assert "service is not connected" in answer
    assert session.state == "INTENT" and session.intent is None
