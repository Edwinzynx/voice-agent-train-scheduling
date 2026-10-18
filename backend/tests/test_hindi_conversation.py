import pytest
from app.brain import fsm, validation
from app.brain.language import spoken_text
from app.brain.selection import match_train
from app.brain.results import result_summary


@pytest.mark.parametrize('text', ['haan', 'जी हां।', 'जी हाँ', 'हाँ आगे बढ़िए', 'जी हां। आगे बढ़िए please yes।', 'हाँ जी, confirm', 'हां, कर दीजिए', 'yes confirm'])
def test_hindi_approvals(text):
    assert validation.confirmation_decision(text) is True


@pytest.mark.parametrize('text', ['हाँ लेकिन तारीख बदलें', 'हाँ नहीं', 'नहीं आगे मत बढ़िए', 'हाँ कल', 'haan maybe', 'जी हाँ रुकिए', 'हाँ, दूसरी ट्रेन', 'yes tomorrow'])
def test_parameters_and_negations_are_not_approval(text):
    assert validation.confirmation_decision(text) is not True


def test_generic_train_matching_uses_current_results_only():
    trains = [{'no': '12646', 'name': 'MILLENNIUM EXP'}, {'no': '16318', 'name': 'HIMSAGAR EXPRESS'}]
    exact, candidate = match_train('Millennial exp', trains)
    assert exact is None and candidate['no'] == '12646'
    assert match_train('Millennium Express.', trains)[0]['no'] == '12646'
    assert match_train('Millennial exp', [trains[1]]) == (None, None)
    other = [{'no': '11111', 'name': 'AMRITSAR EXPRESS'}]
    assert match_train('Amritser Express', other)[1]['no'] == '11111'
    assert match_train('Express', trains) == (None, None)
    ambiguous = [{'no': '11111', 'name': 'TEST CITY EXPRESS'}, {'no': '22222', 'name': 'TEST CITY SPECIAL'}]
    assert match_train('Test City', ambiguous) == (None, None)


def test_reported_hindi_sequence_retains_memory_and_does_not_repeat_tools(monkeypatch):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session('hindi')
    coordinator.process_turn('hindi', 'GREET')
    assert 'कर सकती हूँ' in coordinator.process_turn('hindi', 'Hindi')
    trains = [{'no': '12646', 'name': 'MILLENNIUM EXP', 'classes': ['SL', '3A', '2A'],
               'src': 'Delhi', 'dst': 'Coimbatore', 'dep': '05:10'}]
    calls = []
    def find(*args, **kwargs):
        calls.append('find')
        return {'success': True, 'trains': trains}
    monkeypatch.setattr(fsm.irctc, 'find_trains', find)
    def brain(state, text, context):
        if state == 'INTENT':
            return {'intent': 'CHECK_SEAT' if 'seat' in text else 'FIND_TRAINS', 'language_detected': 'English'}
        if '3D' in text:
            # Even a model rewriting an already known slot must not lose the journey.
            return {'slots': {'source': 'New Delhi', 'date': '2030-01-01', 'class_code': '3A'}, 'next_question': 'What date?'}
        return {'slots': {'source': 'Delhi', 'destination': 'Coimbatore'}, 'next_question': 'Which date?'}
    monkeypatch.setattr(fsm, 'run_brain_step', brain)
    answer = coordinator.process_turn('hindi', 'क्या आप मुझे Delhi से Coimbatore की trains दिखा सकती हैं?')
    assert 'तारीख' in answer and 'Which date' not in answer
    before = session.slots.copy()
    assert coordinator.process_turn('hindi', 'uh') == '' and session.slots == before
    answer = coordinator.process_turn('hindi', 'मैं परसों travel करना चाहता हूं।')
    assert session.state == 'CONFIRM' and 'find trains' not in answer
    date = session.slots['date']
    answer = coordinator.process_turn('hindi', 'जी हां।')
    assert session.state == 'INTENT' and 'प्रस्थान' in answer and 'departs' not in answer
    assert coordinator.process_turn('hindi', 'हाँ') == answer
    assert calls == ['find']
    coordinator.process_turn('hindi', 'मेरे को seat availability बता दीजिए।')
    assert session.slots['date'] == date
    answer = coordinator.process_turn('hindi', 'Millennial exp')
    assert 'क्या आपका मतलब' in answer and session.slots['train_no'] is None
    answer = coordinator.process_turn('hindi', 'जी हाँ')
    assert session.slots['train_no'] == '12646' and 'श्रेणी' in answer
    coordinator.process_turn('hindi', 'AC 3D सही रहे।')
    assert session.state == 'CONFIRM' and session.slots['date'] == date
    assert session.slots['source'] == 'Delhi' and session.slots['class_code'] == '3A'
    monkeypatch.setattr(fsm.irctc, 'check_seat_availability', lambda **kw: {'success': True, 'status': 'WL 35', 'price': 2425})
    answer = coordinator.process_turn('hindi', 'जी हां। आगे बढ़िए please yes।')
    assert 'प्रतीक्षा सूची 35' in answer and 'पुष्ट सीट नहीं' in answer
    assert 'WL' not in answer and 'Fare' not in answer and session.dialect == 'Hindi'


def test_status_expansion_preserves_numbers_and_class():
    slots = {'train_no': '12345', 'class_code': '3A', 'date': '2026-10-20'}
    result = {'status': 'WL 3', 'price': 1000}
    answer = result_summary(result, slots, 'English')
    assert 'Waiting list 3' in answer and 'AC three tier' in answer
    assert result['status'] == 'WL 3'
    assert 'General waiting list 12' in spoken_text('GNWL 12', 'English')
    assert 'Reservation against cancellation 4' in spoken_text('RAC 4', 'English')
    assert 'प्रतीक्षा सूची 3' in spoken_text('WL 3', 'Hindi')
    assert 'Express' in spoken_text('CITY EXP', 'English')


def test_null_slots_and_wrong_followup_question_do_not_erase_memory(monkeypatch):
    coordinator = fsm.FSMCoordinator()
    session = coordinator.get_or_create_session('memory')
    session.intent = 'CHECK_SEAT'
    session.dialect = 'Hindi'
    session.slots.update(source='Delhi', destination='Mumbai', date=validation.normalize_date('tomorrow'))
    session.available_trains = [{'no': '12345', 'name': 'CITY EXP', 'classes': ['3A']}]
    session.search_key = tuple(session.slots[k] for k in ('source', 'destination', 'date'))
    result = coordinator._validate_collection(session, 'City Express', {'slots': {'source': None, 'date': None}, 'next_question': 'What is your date?'})
    assert session.slots['train_no'] == '12345'
    assert 'श्रेणी' in result['next_question'] and 'date' not in result['next_question']
