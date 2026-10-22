from app.main import app
from app.database import get_db
from app.models import Call


def test_public_summary_empty_and_private_routes_stay_protected(client):
    response = client.get('/performance/summary')
    assert response.status_code == 200
    assert response.json()['completed_sessions'] == 0
    assert response.json()['avg_session_p50_ms'] is None
    assert client.get('/dashboard/calls').status_code in (401, 503)


def test_summary_contains_only_completed_aggregate_measurements(client):
    with next(app.dependency_overrides[get_db]()) as db:
        db.add_all([
            Call(id='private-a', status='completed', transcription='private words',
                 duration_seconds=10, p50_latency_ms=100, p90_latency_ms=200),
            Call(id='private-b', status='completed', duration_seconds=30,
                 p50_latency_ms=300, p90_latency_ms=600),
            Call(id='empty', status='completed', duration_seconds=20),
            Call(id='active', status='active', p50_latency_ms=9000),
        ])
        db.commit()
    response = client.get('/performance/summary')
    data = response.json()
    assert set(data) == {'completed_sessions', 'measured_sessions', 'avg_session_p50_ms',
                         'avg_session_p90_ms', 'avg_session_duration_seconds', 'updated_at'}
    assert data['completed_sessions'] == 3
    assert data['measured_sessions'] == 2
    assert data['avg_session_p50_ms'] == 200
    assert data['avg_session_p90_ms'] == 400
    assert data['avg_session_duration_seconds'] == 20
    assert 'private' not in response.text
