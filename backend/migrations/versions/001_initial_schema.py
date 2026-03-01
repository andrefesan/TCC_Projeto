"""Initial schema with all tables and indices.

Revision ID: 001
Revises:
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Parlamentares
    op.create_table(
        "parlamentares",
        sa.Column("cod_autor", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("nome_civil", sa.String(200)),
        sa.Column("partido", sa.String(20)),
        sa.Column("uf", sa.String(2)),
        sa.Column("legislaturas", sa.ARRAY(sa.Integer())),
        sa.Column("url_foto", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("idx_parlamentares_partido", "parlamentares", ["partido"])
    op.create_index("idx_parlamentares_uf", "parlamentares", ["uf"])
    op.execute(
        "CREATE INDEX idx_parlamentares_nome ON parlamentares "
        "USING gin(to_tsvector('portuguese', nome))"
    )

    # Classificação orçamentária
    op.create_table(
        "classificacao_orcamentaria",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("funcao", sa.String(5), nullable=False),
        sa.Column("funcao_nome", sa.String(100)),
        sa.Column("subfuncao", sa.String(5)),
        sa.Column("subfuncao_nome", sa.String(100)),
        sa.Column("programa", sa.String(10)),
        sa.Column("programa_nome", sa.String(200)),
        sa.Column("descricao", sa.Text()),
        sa.Column("embedding", Vector(384)),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("idx_classif_funcao", "classificacao_orcamentaria", ["funcao"])
    op.create_index("idx_classif_subfuncao", "classificacao_orcamentaria", ["subfuncao"])
    op.execute(
        "CREATE INDEX idx_classif_embedding ON classificacao_orcamentaria "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )

    # Emendas
    op.create_table(
        "emendas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("codigo_emenda", sa.String(50), unique=True),
        sa.Column("cod_autor", sa.Integer(), sa.ForeignKey("parlamentares.cod_autor")),
        sa.Column("nome_autor", sa.String(200)),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("tipo_emenda", sa.String(50)),
        sa.Column("funcao", sa.String(5)),
        sa.Column("funcao_nome", sa.String(100)),
        sa.Column("subfuncao", sa.String(5)),
        sa.Column("subfuncao_nome", sa.String(100)),
        sa.Column("programa", sa.String(10)),
        sa.Column("acao", sa.String(20)),
        sa.Column("localidade", sa.String(200)),
        sa.Column("uf", sa.String(2)),
        sa.Column("valor_empenhado", sa.Numeric(15, 2), server_default="0"),
        sa.Column("valor_liquidado", sa.Numeric(15, 2), server_default="0"),
        sa.Column("valor_pago", sa.Numeric(15, 2), server_default="0"),
        sa.Column("descricao", sa.Text()),
        sa.Column("embedding", Vector(384)),
        sa.Column("fonte", sa.String(50), server_default="Portal da Transparência"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("idx_emendas_ano", "emendas", ["ano"])
    op.create_index("idx_emendas_uf", "emendas", ["uf"])
    op.create_index("idx_emendas_cod_autor", "emendas", ["cod_autor"])
    op.create_index("idx_emendas_funcao", "emendas", ["funcao"])
    op.create_index("idx_emendas_subfuncao", "emendas", ["subfuncao"])
    op.create_index("idx_emendas_tipo", "emendas", ["tipo_emenda"])
    op.execute(
        "CREATE INDEX idx_emendas_tsv ON emendas "
        "USING gin(to_tsvector('portuguese', "
        "coalesce(nome_autor, '') || ' ' || "
        "coalesce(funcao_nome, '') || ' ' || "
        "coalesce(subfuncao_nome, '') || ' ' || "
        "coalesce(descricao, '')))"
    )
    op.execute(
        "CREATE INDEX idx_emendas_embedding ON emendas "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )

    # Execução
    op.create_table(
        "execucao",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("emenda_id", sa.Integer(), sa.ForeignKey("emendas.id", ondelete="CASCADE")),
        sa.Column("data_movimento", sa.Date()),
        sa.Column("valor", sa.Numeric(15, 2)),
        sa.Column("fase", sa.String(20)),
        sa.Column("documento", sa.String(50)),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("idx_execucao_emenda", "execucao", ["emenda_id"])
    op.create_index("idx_execucao_fase", "execucao", ["fase"])
    op.create_index("idx_execucao_data", "execucao", ["data_movimento"])

    # Consultas log
    op.create_table(
        "consultas_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("consulta_nl", sa.Text(), nullable=False),
        sa.Column("entidades_json", sa.JSON()),
        sa.Column("sql_gerada", sa.Text()),
        sa.Column("modo_busca", sa.String(20)),
        sa.Column("num_resultados", sa.Integer()),
        sa.Column("latencia_ms", sa.Integer()),
        sa.Column("sucesso", sa.Boolean(), server_default="true"),
        sa.Column("erro", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    op.create_index("idx_log_created", "consultas_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("consultas_log")
    op.drop_table("execucao")
    op.drop_table("emendas")
    op.drop_table("classificacao_orcamentaria")
    op.drop_table("parlamentares")
