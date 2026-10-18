from datetime import date, timedelta
import pytest
from app.brain import validation, fsm, llm
from app.config import config_manager
from app.tools import irctc


@pytest.mark.parametrize("phrase,expected", [
    ("do not confirm", False), ("not sure", None), ("yes, but change my name", False),
    ("change my name", False), ("no", False), ("nahi", False), ("नहीं", False),
    ("हाँ", True), ("yes, that's correct.", True), ("haan", True), ("okay", True),
    ("yesterday", None), ("surely not", False), ("maybe", None), ("", None),
])
def test_explicit_confirmation(phrase, expected):
    assert validation.confirmation_decision(phrase) is expected


@pytest.mark.parametrize("value,expected", [
    ("today", "2026-12-31"), ("tomorrow", "2027-01-01"), ("kal", "2027-01-01"),
    ("परसों", "2027-01-02"), ("1st January", "2027-01-01"), ("2027/01/04", "2027-01-04"),
    ("next monday", "2027-01-04"),
])
def test_dates_roll_forward(value, expected):
    assert validation.normalize_date(value, date(2026, 12, 31)) == expected


@pytest.mark.parametrize("value", ["", "not a date", "2026-06-19", "2027-02-30", "yesterday"])
def test_dates_never_default_to_today(value):
    with pytest.raises(ValueError):
        validation.normalize_date(value, date(2026, 10, 18))


def test_api_date_and_station_validation(monkeypatch):
    monkeypatch.setattr(validation, "today_in_india", lambda: date(2026, 10, 18))
    assert irctc.format_date_for_api("tomorrow") == "19-10-2026"
    assert irctc.resolve_station_code("NDLS") == "NDLS"
    with pytest.raises(ValueError):
        irctc.resolve_station_code("Imaginary station")


def test_mock_date_uses_clock(monkeypatch):
    monkeypatch.setattr(validation, "today_in_india", lambda: date(2026, 12, 31))
    result = llm.mock_fill_slots("tomorrow", {}, "FIND_TRAINS")
    assert result["slots"]["date"] == "2027-01-01"


@pytest.fixture
def journey(monkeypatch):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session("test")
    session.state = "COLLECT"
    session.intent = "BOOK_TICKET"
    session.slots.update(source="Delhi", destination="Chandigarh", date=validation.normalize_date("tomorrow"), class_code="CC", passenger_name="Amit")
    trains = [{"no": "12012", "name": "Shatabdi", "classes": ["CC", "EC"]}]
    monkeypatch.setattr(irctc, "find_trains", lambda *args, **kwargs: {"success": True, "trains": [dict(t) for t in trains]})
    return coordinator, session


def test_llm_cannot_choose_train(journey):
    coordinator, session = journey
    result = coordinator._validate_collection(session, "My name is Amit", {"slots": {**session.slots, "train_no": "12012"}, "all_slots_filled": True})
    assert session.slots["train_no"] is None
    assert not result["all_slots_filled"]


def test_train_must_match_route_and_class(journey):
    coordinator, session = journey
    result = coordinator._validate_collection(session, "train 99999", {"slots": session.slots.copy()})
    assert not result["all_slots_filled"]
    assert session.slots["train_no"] is None
    result = coordinator._validate_collection(session, "train 12012 class SL", {"slots": {**session.slots, "class_code": "SL"}})
    assert session.slots["train_no"] == "12012"
    assert session.slots["class_code"] is None
    assert not result["all_slots_filled"]


def test_route_correction_invalidates_selection(journey):
    coordinator, session = journey
    session.slots["train_no"] = "12012"
    result = coordinator._validate_collection(session, "change date to day after tomorrow", {"slots": session.slots.copy()})
    assert session.slots["train_no"] is None
    assert not result["all_slots_filled"]


def test_confirmation_does_not_execute_negation(journey, monkeypatch):
    coordinator, session = journey
    session.state = "CONFIRM"
    monkeypatch.setattr(coordinator, "_execute_tool", lambda *_: pytest.fail("Negation executed a tool"))
    response = coordinator.process_turn("test", "do not confirm")
    assert session.state == "COLLECT"
    assert "haven't proceeded" in response


def test_correction_is_read_back_before_execution(journey, monkeypatch):
    coordinator, session = journey
    session.state = "CONFIRM"
    session.slots["train_no"] = "12012"
    monkeypatch.setattr(fsm, "run_brain_step", lambda *_: {"slots": {**session.slots, "passenger_name": "Priya"}})
    monkeypatch.setattr(coordinator, "_execute_tool", lambda *_: pytest.fail("Correction executed a tool"))
    response = coordinator.process_turn("test", "change my name to Priya")
    assert session.state == "CONFIRM"
    assert "Priya" in response and "12012" in response


def test_missing_train_never_substituted(journey, monkeypatch):
    coordinator, session = journey
    monkeypatch.setattr(irctc, "book_ticket", lambda *args, **kwargs: pytest.fail("Missing train booked"))
    assert "train no" in coordinator._execute_tool(session)
    assert session.state == "COLLECT"


def test_stale_card_is_rejected(journey):
    coordinator, session = journey
    session.available_trains = [{"no": "12012", "classes": ["CC"]}]
    with pytest.raises(ValueError):
        coordinator.select_train("test", "99999", "CC")


def test_production_never_simulates():
    config_manager.settings.allow_simulated_railway = True
    calls = [lambda: irctc.book_ticket("12012", "tomorrow", "CC", [], True),
             lambda: irctc.cancel_ticket("4829384729"), lambda: irctc.get_pnr_status("4829384729"),
             lambda: irctc.get_live_train_info("12012")]
    for call in calls:
        assert call()["code"] == "SERVICE_NOT_CONNECTED"


def test_production_never_falls_back_to_mock(monkeypatch):
    config_manager.settings.groq_api_key = "test"
    monkeypatch.setattr(llm, "call_groq_json", lambda *args: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(llm, "run_mock_brain_step", lambda *args: pytest.fail("Mock used in production"))
    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        llm.run_brain_step("INTENT", "book ticket", {})


def test_live_availability_display_format():
    data = {"trainName": "Example", "availabilityCache": {"CC": {"availabilityDisplayName": "AVL 4", "fare": "1190"}}}
    result = irctc.check_seat_availability("12012", "tomorrow", "CC", train_data=data)
    assert result["seats_available"] == 4
    assert result["price"] == 1190
    data["availabilityCache"]["CC"] = {}
    assert not irctc.check_seat_availability("12012", "tomorrow", "CC", train_data=data)["success"]
    data["availabilityCache"]["CC"] = {"availabilityDisplayName": "UNKNOWN"}
    result = irctc.check_seat_availability("12012", "tomorrow", "CC", train_data=data)
    assert result["price"] is None and result["seats_available"] is None


def test_ordinal_matches_displayed_train_class_options(journey):
    coordinator, session = journey
    coordinator._validate_selected_train(session)
    result = coordinator._validate_collection(session, "second one", {"slots": session.slots.copy()})
    assert result["all_slots_filled"]
    assert session.slots["train_no"] == "12012" and session.slots["class_code"] == "EC"


def test_card_selection_starts_real_seat_check(journey, monkeypatch):
    coordinator, session = journey
    coordinator._validate_selected_train(session)
    session.state = "INTENT"
    session.intent = "FIND_TRAINS"
    def brain(state, text, context):
        if state == "INTENT": return {"intent": "UNKNOWN"}
        if state == "COLLECT": return {"slots": context["slots"].copy()}
        return {"response": "Seat results are ready."}
    monkeypatch.setattr(fsm, "run_brain_step", brain)
    response = coordinator.select_train("test", "12012", "EC")
    assert session.intent == "CHECK_SEAT"
    assert session.state == "CONFIRM"
    assert "12012" in response and "EC" in response
    observed = []
    def seats(**kwargs):
        observed.append(kwargs)
        return {"success": True, "seats_available": 4}
    monkeypatch.setattr(irctc, "check_seat_availability", seats)
    coordinator.process_turn("test", "yes")
    assert observed[0]["train_no"] == "12012"
    assert observed[0]["class_code"] == "EC"


def test_spoken_ordinal_after_search(journey, monkeypatch):
    coordinator, session = journey
    coordinator._validate_selected_train(session)
    session.state = "INTENT"
    session.intent = "FIND_TRAINS"
    monkeypatch.setattr(fsm, "run_brain_step", lambda state, text, context: {"intent": "UNKNOWN"} if state == "INTENT" else {"slots": context["slots"].copy()})
    coordinator.process_turn("test", "second one")
    assert session.intent == "CHECK_SEAT" and session.state == "CONFIRM"
    assert session.slots["class_code"] == "EC"
