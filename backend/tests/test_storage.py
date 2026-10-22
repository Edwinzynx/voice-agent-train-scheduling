import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.database import Base, build_engine
from app.models import Call, CallLog, EvalRun
from scripts.migrate_sqlite import copy_records, open_snapshot


def test_postgres_url_uses_installed_driver_and_preserves_options():
    for scheme in ('postgres', 'postgresql', 'postgresql+psycopg'):
        engine = build_engine(f'{scheme}://user:secret@localhost/history?sslmode=require')
        assert engine.url.drivername == 'postgresql+psycopg'
        assert engine.url.query['sslmode'] == 'require'
        assert engine.pool._pre_ping is True
        engine.dispose()


def seed(engine):
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Call(id='saved-call', status='completed', duration_seconds=12, transcription='Test journey'))
        db.flush()
        db.add(CallLog(id=41, call_id='saved-call', direction='outbound', text='Example response'))
        db.add(EvalRun(id='saved-eval', overall_success_rate=75))
        db.commit()


def verify_import(source, target):
    assert copy_records(source, target) == {'calls': 1, 'call_logs': 1, 'eval_runs': 1}
    with Session(target) as db:
        assert db.get(Call, 'saved-call').transcription == 'Test journey'
        assert db.get(EvalRun, 'saved-eval').overall_success_rate == 75
        log = CallLog(call_id='saved-call', text='Next turn')
        db.add(log)
        db.commit()
        assert log.id > 41
    with pytest.raises(ValueError, match='empty database'):
        copy_records(source, target)


def test_history_survives_engine_restart_and_migration_is_non_destructive(tmp_path):
    path = tmp_path / 'history.db'
    original = build_engine(f'sqlite:///{path.as_posix()}')
    seed(original)
    original.dispose()
    snapshot = open_snapshot(path)
    target = build_engine(f'sqlite:///{(tmp_path / "target.db").as_posix()}')
    verify_import(snapshot, target)
    with snapshot.connect() as connection:
        assert len(connection.execute(select(CallLog)).all()) == 1
    snapshot.dispose()
    target.dispose()
    reopened = build_engine(f'sqlite:///{(tmp_path / "target.db").as_posix()}')
    with Session(reopened) as db:
        assert db.get(Call, 'saved-call').status == 'completed'
    reopened.dispose()


@pytest.mark.skipif(not os.getenv('TEST_POSTGRES_URL'), reason='Requires disposable PostgreSQL test database')
def test_postgres_migration_and_restart(tmp_path):
    # Use a unique schema so a test never clears existing database records.
    import uuid
    from sqlalchemy import text
    schema = 'test_' + uuid.uuid4().hex
    control = build_engine(os.environ['TEST_POSTGRES_URL'])
    with control.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    url = control.url.update_query_dict({'options': f'-csearch_path={schema}'})
    target = build_engine(url)
    source = create_engine('sqlite://')
    try:
        seed(source)
        verify_import(source, target)
        target.dispose()
        target = build_engine(url)
        with Session(target) as db:
            assert db.get(Call, 'saved-call').duration_seconds == 12
    finally:
        source.dispose()
        target.dispose()
        with control.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        control.dispose()
