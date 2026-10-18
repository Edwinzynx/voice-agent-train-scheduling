import pytest
from app.brain import fsm, validation
from app.brain.results import listed_train_followup


@pytest.fixture
def results(monkeypatch):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session('results')
    session.state = 'INTENT'
    session.intent = 'FIND_TRAINS'
    session.dialect = 'English'
    session.language_selected = True
    session.slots.update(source='Delhi', destination='Chandigarh', date=validation.normalize_date('tomorrow'))
    session.available_trains = [
        {'no': str(14000 + i), 'name': f'OTHER {i} EXP', 'classes': ['SL', '3A', '2A', '1A']}
        for i in range(12)] + [
        {'no': '22447', 'name': 'VANDE BHARAT EX', 'classes': ['CC', 'EC'], 'dep': '05:50', 'src': 'New Delhi'}]
    session.search_key = tuple(session.slots[k] for k in ('source', 'destination', 'date'))
    monkeypatch.setattr(fsm, 'run_brain_step', lambda *a: pytest.fail('Existing results should not need the LLM'))
    monkeypatch.setattr(fsm.irctc, 'find_trains', lambda *a, **kw: pytest.fail('Existing results should not trigger another search'))
    return coordinator, session


def test_named_availability_question_uses_full_result_set(results):
    coordinator, session = results
    before = session.slots.copy()
    answer = coordinator.process_turn('results', 'Is there no Vande Bharat train available?')
    assert '22447' in answer and '05:50' in answer and '1 matching' in answer
    assert session.state == 'INTENT' and session.slots == before
    assert 'confirm find' not in answer


def test_partial_name_does_not_silently_select_among_multiple_services(results):
    coordinator, session = results
    session.available_trains.append({'no': '22449', 'name': 'VANDE BHARAT EXP', 'classes': ['CC']})
    answer = coordinator.process_turn('results', 'Is Vande Bharat available?')
    assert '22447' in answer and '22449' in answer and '2 matching' in answer
    assert session.slots['train_no'] is None


def test_different_date_is_not_answered_from_cached_results(results):
    _, session = results
    assert listed_train_followup('Is Vande Bharat available day after tomorrow?', session.available_trains, session.slots) is None


def test_card_number_beyond_four_selects_train_not_class(results):
    coordinator, session = results
    answer = coordinator.process_turn('results', 'train 13')
    assert session.slots['train_no'] == '22447' and session.slots['class_code'] is None
    assert session.state == 'COLLECT' and session.intent == 'CHECK_SEAT'
    assert 'CC' in answer and 'EC' in answer


def test_second_card_selects_second_train(results):
    coordinator, session = results
    coordinator.process_turn('results', 'second one')
    assert session.slots['train_no'] == '14001' and session.slots['class_code'] is None


def test_unlisted_option_is_not_substituted(results):
    coordinator, session = results
    answer = coordinator.process_turn('results', 'train 99')
    assert "isn't listed" in answer and session.slots['train_no'] is None
