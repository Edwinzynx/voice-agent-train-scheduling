from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import config_manager

def build_engine(database_url):
    url = make_url(database_url)
    # Render emits postgres:// URLs; use the installed Psycopg 3 driver.
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+psycopg")
    if url.get_backend_name() == "sqlite":
        return create_engine(url, connect_args={"check_same_thread": False})
    if url.get_backend_name() != "postgresql":
        raise ValueError("DATABASE_URL must use PostgreSQL or SQLite.")
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5,
                         pool_recycle=300, connect_args={"connect_timeout": 10},
                         hide_parameters=True)


engine = build_engine(config_manager.settings.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
