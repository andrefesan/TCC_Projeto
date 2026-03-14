"""Tipos de coluna compatíveis com SQLite e PostgreSQL."""
from sqlalchemy import JSON, Text
from app.database import is_sqlite

if is_sqlite():
    # SQLite: ARRAY → JSON, Vector → Text (nullable, preenchido depois)
    IntArrayType = JSON
    VectorType = Text
else:
    from sqlalchemy.dialects.postgresql import ARRAY
    from sqlalchemy import Integer
    from pgvector.sqlalchemy import Vector

    IntArrayType = ARRAY(Integer)
    VectorType = Vector(384)
