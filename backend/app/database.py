from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=3, max_overflow=5, pool_pre_ping=True)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def is_sqlite() -> bool:
    return _is_sqlite


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa o banco de dados (pgvector apenas para PostgreSQL)."""
    if not _is_sqlite:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    Base.metadata.create_all(bind=engine)
