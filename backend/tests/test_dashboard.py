from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Call, EvalRun
from app.routers.dashboard import get_stats


def test_missing_measurements_are_not_reported_as_zero():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        stats = get_stats(db)
        assert stats['total_calls'] == 0
        assert stats['completed_calls'] == 0
        for field in ('avg_p50_ms', 'avg_p90_ms', 'avg_duration_seconds', 'latest_eval_accuracy'):
            assert stats[field] is None
        db.add(Call(id='no-turns', status='completed', duration_seconds=2))
        db.commit()
        stats = get_stats(db)
        assert stats['avg_p50_ms'] is None
        assert stats['avg_duration_seconds'] == 2
    engine.dispose()


def test_recorded_measurements_and_real_zero_eval_are_preserved():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            Call(id='measured', status='completed', duration_seconds=20, p50_latency_ms=120, p90_latency_ms=300),
            Call(id='no-turns', status='completed', duration_seconds=2),
            Call(id='active', status='active'),
            EvalRun(id='evaluation', overall_success_rate=0),
        ])
        db.commit()
        stats = get_stats(db)
        assert stats['total_calls'] == 3
        assert stats['completed_calls'] == 2
        assert stats['avg_p50_ms'] == 120
        assert stats['avg_p90_ms'] == 300
        assert stats['avg_duration_seconds'] == 11
        assert stats['latest_eval_accuracy'] == 0
    engine.dispose()
