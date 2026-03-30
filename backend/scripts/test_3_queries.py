"""Teste rápido: consultas complexas nos 3 modos + validação das 3 estratégias do planner."""
import asyncio
import io
import json
import sys
import time
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
from app.services.cache import query_cache


TESTES = [
    # --- Modo híbrido: testar as 3 estratégias do planner ---
    {
        "modo": "hibrido",
        "consulta": "Quantas emendas individuais o deputado Tasso Jereissati destinou ao Ceará em 2022?",
        "descricao": "Planner deve escolher sql_only (autor+uf+ano, sem componente semântico)",
        "estrategia_esperada": "sql_only",
    },
    {
        "modo": "hibrido",
        "consulta": "Emendas para assistência social no Rio Grande do Sul em 2022?",
        "descricao": "Planner deve escolher sql_first ou rrf (área semântica + UF + ano)",
        "estrategia_esperada": "sql_first|rrf",
    },
    {
        "modo": "hibrido",
        "consulta": "Quais emendas financiaram construção de pontes no Pará em 2023?",
        "descricao": "Planner deve escolher rrf + precisa_busca_documentos (obra específica)",
        "estrategia_esperada": "rrf",
    },
    # --- Modo SQL puro: consulta complexa com múltiplos filtros ---
    {
        "modo": "sql_puro",
        "consulta": "Qual deputado do PT mais destinou emendas para saúde na Bahia em 2024?",
        "descricao": "SQL puro: agregação ranking com partido+area+uf+ano",
        "estrategia_esperada": None,
    },
    # --- Modo vetorial puro: busca semântica ---
    {
        "modo": "vetorial_puro",
        "consulta": "Emendas para combate à seca e abastecimento de água no Nordeste?",
        "descricao": "Vetorial puro: busca semântica por tema amplo",
        "estrategia_esperada": None,
    },
]


async def main():
    db = SessionLocal()
    pipeline = RAGPipeline()
    ok_count = 0
    total_checks = 0

    try:
        for i, t in enumerate(TESTES, 1):
            query_cache.clear()
            modo = t["modo"]
            consulta = t["consulta"]

            print(f"\n{'='*70}")
            print(f"  TESTE {i}/{len(TESTES)} — Modo: {modo.upper()}")
            print(f"  Consulta: {consulta}")
            print(f"  Objetivo: {t['descricao']}")
            print(f"{'='*70}")

            inicio = time.time()
            try:
                resultado = await pipeline.processar(consulta, db, modo=modo)
                latencia = int((time.time() - inicio) * 1000)

                meta = resultado.get("metadata", {})
                estrategia = meta.get("estrategia_hibrida")
                num_res = meta.get("num_resultados", 0)

                print(f"\n  Latência:          {latencia}ms")
                print(f"  Resultados:        {num_res}")
                print(f"  Estratégia:        {estrategia}")
                print(f"  Total no banco:    {meta.get('total_no_banco')}")
                print(f"  Dados completos:   {meta.get('dados_completos')}")

                # Entidades
                entidades = meta.get("entidades", {})
                ent_str = ", ".join(f"{k}={v}" for k, v in entidades.items() if v)
                print(f"  Entidades:         {ent_str}")

                # Verificar doc_observacao
                dados = resultado.get("dados", [])
                docs_com_obs = [d for d in dados if d.get("doc_observacao")]
                if docs_com_obs:
                    print(f"  doc_observacao:    {len(docs_com_obs)}/{len(dados)} resultados")
                    for d in docs_com_obs[:2]:
                        print(f"    → {d['doc_observacao'][:90]}...")

                # Resumo
                resumo = resultado.get("resumo", "")
                if resumo:
                    print(f"  Resumo:            {resumo[:150]}...")

                # --- CHECKS ---
                print(f"\n  Verificações:")

                # Check 1: tem resultados
                total_checks += 1
                if num_res > 0:
                    ok_count += 1
                    print(f"    ✓ Retornou {num_res} resultados")
                else:
                    print(f"    ✗ ZERO resultados!")

                # Check 2: estratégia correta (só para híbrido)
                esperada = t["estrategia_esperada"]
                if esperada:
                    total_checks += 1
                    opcoes = esperada.split("|")
                    if estrategia in opcoes:
                        ok_count += 1
                        print(f"    ✓ Estratégia '{estrategia}' está entre as esperadas ({esperada})")
                    else:
                        print(f"    ✗ Estratégia '{estrategia}' NÃO corresponde ao esperado ({esperada})")

                # Check 3: doc_observacao presente quando rrf+documentos
                if esperada == "rrf" and "ponte" in consulta.lower():
                    total_checks += 1
                    if docs_com_obs:
                        ok_count += 1
                        print(f"    ✓ doc_observacao presente em {len(docs_com_obs)} resultados")
                    else:
                        print(f"    ✗ doc_observacao AUSENTE (busca em documentos não funcionou?)")

            except Exception as e:
                print(f"\n  ERRO: {e}")
                import traceback
                traceback.print_exc()

    finally:
        db.close()

    print(f"\n{'='*70}")
    print(f"  RESULTADO FINAL: {ok_count}/{total_checks} checks passaram")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
