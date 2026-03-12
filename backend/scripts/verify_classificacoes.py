"""Verifica dados na tabela classificacao_orcamentaria."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal


def verify():
    db = SessionLocal()
    try:
        total = db.execute(
            text("SELECT COUNT(*) FROM classificacao_orcamentaria")
        ).scalar()
        print(f"Total de registros: {total}")

        funcoes = db.execute(text(
            "SELECT COUNT(DISTINCT funcao) FROM classificacao_orcamentaria"
        )).scalar()
        print(f"Funções distintas: {funcoes}")

        subfuncoes = db.execute(text(
            "SELECT COUNT(*) FROM classificacao_orcamentaria WHERE subfuncao IS NOT NULL"
        )).scalar()
        print(f"Registros com subfunção: {subfuncoes}")

        com_embedding = db.execute(text(
            "SELECT COUNT(*) FROM classificacao_orcamentaria WHERE embedding IS NOT NULL"
        )).scalar()
        print(f"Com embedding: {com_embedding}")

        print("\nAmostra (primeiros 10):")
        rows = db.execute(text(
            "SELECT funcao, funcao_nome, subfuncao, subfuncao_nome "
            "FROM classificacao_orcamentaria ORDER BY funcao, subfuncao LIMIT 10"
        )).fetchall()
        for r in rows:
            sub = f" > {r.subfuncao} - {r.subfuncao_nome}" if r.subfuncao else ""
            print(f"  {r.funcao} - {r.funcao_nome}{sub}")

    finally:
        db.close()


if __name__ == "__main__":
    verify()
