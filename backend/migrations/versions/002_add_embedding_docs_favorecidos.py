"""Add embedding columns to documentos_emenda and favorecidos.

Revision ID: 002
Revises: 001
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Embedding para documentos de emenda (observações + favorecido + classificação)
    op.add_column("documentos_emenda",
                  sa.Column("embedding", Vector(384)))

    # Embedding para favorecidos (busca semântica por nome)
    op.add_column("favorecidos",
                  sa.Column("embedding", Vector(384)))

    # Índices HNSW para busca vetorial eficiente
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documentos_emenda_embedding
        ON documentos_emenda
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorecidos_embedding
        ON favorecidos
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_favorecidos_embedding")
    op.execute("DROP INDEX IF EXISTS idx_documentos_emenda_embedding")
    op.drop_column("favorecidos", "embedding")
    op.drop_column("documentos_emenda", "embedding")
