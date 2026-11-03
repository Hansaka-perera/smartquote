import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("SMARTQUOTE_DATA", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
# PostgreSQL later: set DATABASE_URL=postgresql+psycopg://user:pw@host/db (models use portable types only)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'smartquote.db').as_posix()}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
