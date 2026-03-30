"""Gera exemplo qualitativo completo para o artigo.
Executa uma consulta e captura todos os passos intermediários do pipeline.
Também roda N repetições de uma amostra para medir variância.
"""
import asyncio
import json
import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
from app.services.cache import query_cache

# ============================================================
# Parte 1: Exemplo qualitativo completo
# ============================================================
CONSULTA_EXEMPLO = "Qual o valor total das emendas individuais da deputada Fernanda Melchionna em 2024?"

async def run_qualitative():
    pipeline = RAGPipeline()
    db = SessionLocal()
    try:
        # Limpar cache para garantir execução real
        query_cache._cache.clear()

        print("=" * 80)
        print("  EXEMPLO QUALITATIVO COMPLETO")
        print(f"  Consulta: {CONSULTA_EXEMPLO}")
        print("=" * 80)

        inicio = time.time()

        # Etapa 1: Interpretação
        print("\n--- Etapa 1: Interpretação ---")
        entidades = await pipeline.interpreter.interpretar(CONSULTA_EXEMPLO)
        t1 = time.time() - inicio
        print(f"  Entidades extraídas ({t1:.2f}s):")
        for k, v in entidades.items():
            if v is not None:
                print(f"    {k}: {v}")

        # Etapa 2: Planejamento + Decomposição
        print("\n--- Etapa 2: Planejamento + Decomposição ---")
        plano, decomposicao = await asyncio.gather(
            pipeline.planner.planejar(CONSULTA_EXEMPLO, entidades),
            asyncio.to_thread(pipeline.decomposer.decompor, entidades, db),
        )
        t2 = time.time() - inicio
        print(f"  Plano ({t2:.2f}s):")
        print(f"    Estratégia recomendada: {plano.get('estrategia', 'N/A')}")
        print(f"    Justificativa: {plano.get('justificativa', 'N/A')}")
        print(f"  Decomposição:")
        print(f"    Operação: {decomposicao.get('operacao', 'N/A')}")
        print(f"    Filtros SQL: {json.dumps(decomposicao.get('filtros_sql', {}), ensure_ascii=False, indent=6)}")

        # Etapa 3: Recuperação (executar pipeline completo)
        print("\n--- Etapa 3+4: Recuperação + Síntese ---")
        query_cache._cache.clear()  # Limpar novamente
        resultado = await pipeline.processar(CONSULTA_EXEMPLO, db, modo="hibrido")
        t_total = time.time() - inicio

        print(f"  Estratégia utilizada: {resultado.get('metadata', {}).get('estrategia', 'N/A')}")
        print(f"  Modo: {resultado.get('metadata', {}).get('modo', 'N/A')}")
        print(f"  Num resultados: {resultado.get('metadata', {}).get('num_resultados', 'N/A')}")
        print(f"  Latência total: {resultado.get('metadata', {}).get('latencia_ms', t_total*1000):.0f} ms")

        print("\n--- Resposta gerada ---")
        resposta = resultado.get("resposta", "")
        # Truncar se muito longa
        if len(resposta) > 1000:
            print(resposta[:1000] + "\n  [... truncada ...]")
        else:
            print(resposta)

        fontes = resultado.get("fontes", [])
        if fontes:
            print(f"\n  Fontes ({len(fontes)}):")
            for f in fontes[:5]:
                print(f"    - {f}")

        return resultado

    finally:
        db.close()

# ============================================================
# Parte 2: Teste de variância (amostra pequena, 3 repetições)
# ============================================================
AMOSTRA_VARIANCIA = [
    "Quantas emendas individuais o deputado Tasso Jereissati destinou ao Ceará em 2022?",
    "Quais emendas foram destinadas à saúde no Rio de Janeiro em 2023?",
    "Compare as emendas para educação entre 2022 e 2024",
    "Quais instituições receberam recursos de emendas do deputado Zeca Dirceu em 2023?",
    "Qual o valor total das emendas de bancada para o Amazonas em 2024?",
]
N_REPETICOES = 3

async def run_variance():
    pipeline = RAGPipeline()
    db = SessionLocal()
    try:
        print("\n\n" + "=" * 80)
        print(f"  TESTE DE VARIÂNCIA ({N_REPETICOES} repetições, {len(AMOSTRA_VARIANCIA)} consultas)")
        print("=" * 80)

        resultados = {}
        for i, consulta in enumerate(AMOSTRA_VARIANCIA):
            resultados[i] = {"consulta": consulta, "repeticoes": []}
            print(f"\n  Consulta {i+1}: {consulta[:60]}...")
            for rep in range(N_REPETICOES):
                query_cache._cache.clear()
                resultado = await pipeline.processar(consulta, db, modo="hibrido")
                meta = resultado.get("metadata", {})
                entidades = meta.get("entidades", {})
                resposta = resultado.get("resposta", "")[:200]
                latencia = meta.get("latencia_ms", 0)

                resultados[i]["repeticoes"].append({
                    "rep": rep + 1,
                    "latencia_ms": latencia,
                    "num_resultados": meta.get("num_resultados", 0),
                    "estrategia": meta.get("estrategia", "N/A"),
                    "resposta_hash": hash(resposta),  # Para comparar se respostas são idênticas
                    "resposta_preview": resposta[:100],
                })
                print(f"    Rep {rep+1}: {latencia:.0f}ms, {meta.get('num_resultados', 0)} resultados, estrategia={meta.get('estrategia', 'N/A')}")

            # Verificar se respostas são idênticas
            hashes = [r["resposta_hash"] for r in resultados[i]["repeticoes"]]
            identical = len(set(hashes)) == 1
            latencias = [r["latencia_ms"] for r in resultados[i]["repeticoes"]]
            print(f"    Respostas idênticas: {'SIM' if identical else 'NAO'}")
            print(f"    Latência: média={sum(latencias)/len(latencias):.0f}ms, "
                  f"min={min(latencias):.0f}ms, max={max(latencias):.0f}ms, "
                  f"desvio={(sum((x-sum(latencias)/len(latencias))**2 for x in latencias)/len(latencias))**0.5:.0f}ms")

        return resultados
    finally:
        db.close()

async def main():
    result = await run_qualitative()
    variance_results = await run_variance()

if __name__ == "__main__":
    asyncio.run(main())
