from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=3, max_overflow=5, pool_pre_ping=True)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# Enable WAL mode and performance pragmas for SQLite
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA busy_timeout=30000")  # 30s retry on lock
        cursor.close()

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
    # Importar todos os modelos para que Base.metadata conheça as tabelas
    import app.models.emenda  # noqa: F401
    import app.models.parlamentar  # noqa: F401
    import app.models.documento  # noqa: F401
    import app.models.beneficiario  # noqa: F401
    import app.models.classificacao  # noqa: F401
    import app.models.execucao  # noqa: F401
    import app.models.lookup  # noqa: F401
    import app.models.favorecido  # noqa: F401
    import app.models.sancao  # noqa: F401
    import app.models.convenio  # noqa: F401

    if not _is_sqlite:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    Base.metadata.create_all(bind=engine)
