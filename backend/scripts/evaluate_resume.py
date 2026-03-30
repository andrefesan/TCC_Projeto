"""Script para retomar avaliação, re-executando apenas consultas que falharam."""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
from app.services.cache import query_cache
from scripts.evaluate import (
    TODAS_CONSULTAS, avaliar_resultado, calcular_metricas_agregadas,
)
import structlog

logger = structlog.get_logger()

DELAY_ENTRE_CONSULTAS = 3  # segundos entre cada consulta


async def retomar_avaliacao(modo: str = "hibrido"):
    """Retoma avaliação, re-executando apenas as consultas que falharam."""
    output_path = Path(__file__).parent.parent / "tests" / "test_queries" / f"resultados_{modo}.json"

    # Carregar resultados existentes
    with open(output_path, "r", encoding="utf-8") as f:
        dados_existentes = json.load(f)

    # Separar sucessos e falhas
    resultados_ok = [r for r in dados_existentes["resultados"] if r.get("sucesso")]
    ids_ok = {r["id"] for r in resultados_ok}
    consultas_pendentes = [c for c in TODAS_CONSULTAS if c["id"] not in ids_ok]

    print(f"Consultas já concluídas: {len(resultados_ok)}", flush=True)
    print(f"Consultas pendentes: {len(consultas_pendentes)}", flush=True)

    if not consultas_pendentes:
        print("Nenhuma consulta pendente. Avaliação já completa.", flush=True)
        return dados_existentes

    db = SessionLocal()
    pipeline = RAGPipeline()
    novos_resultados = []

    try:
        for i, consulta_def in enumerate(consultas_pendentes):
            cid = consulta_def["id"]
            consulta = consulta_def["consulta"]

            print(f"[{i+1}/{len(consultas_pendentes)}] Avaliando {cid}: {consulta[:50]}...", flush=True)

            # Delay entre consultas para evitar 529
            if i > 0:
                await asyncio.sleep(DELAY_ENTRE_CONSULTAS)

            max_retries = 5
            for attempt in range(max_retries):
                inicio = time.time()
                try:
                    # Limpar cache para garantir execução limpa
                    cache_key = f"{modo}:{consulta}"
                    query_cache._cache.pop(cache_key, None)

                    resultado = await pipeline.processar(consulta, db, modo=modo)
                    latencia = int((time.time() - inicio) * 1000)

                    metricas = avaliar_resultado(resultado, consulta_def)

                    novos_resultados.append({
                        "id": cid,
                        "tipo": cid[0],
                        "consulta": consulta,
                        "latencia_ms": latencia,
                        "num_resultados": resultado["metadata"]["num_resultados"],
                        "modo": resultado["metadata"]["modo"],
                        "metricas": metricas,
                        "sucesso": True,
                    })

                    print(f"  OK: F1={metricas['f1_score']:.2f} NDCG={metricas['ndcg_at_5']:.2f} lat={latencia}ms", flush=True)
                    break

                except Exception as e:
                    is_overloaded = "529" in str(e) or "overloaded" in str(e).lower()
                    if is_overloaded and attempt < max_retries - 1:
                        wait = 2 ** (attempt + 2)  # 4, 8, 16, 32, 64s
                        print(f"  API sobrecarregada, tentativa {attempt+1}/{max_retries}, aguardando {wait}s...", flush=True)
                        await asyncio.sleep(wait)
                        continue
                    novos_resultados.append({
                        "id": cid, "tipo": cid[0], "consulta": consulta,
                        "sucesso": False, "erro": str(e),
                    })
                    print(f"  ERRO: {str(e)[:80]}", flush=True)
                    break

            # Salvar progresso parcial a cada 10 consultas
            if (i + 1) % 10 == 0:
                _salvar_resultados(resultados_ok + novos_resultados, modo, output_path)
                print(f"  [Progresso salvo: {len(resultados_ok) + len([r for r in novos_resultados if r.get('sucesso')])} sucessos]", flush=True)

    finally:
        db.close()

    # Salvar resultado final
    todos = resultados_ok + novos_resultados
    relatorio = _salvar_resultados(todos, modo, output_path)

    # Imprimir relatório
    geral = relatorio["geral"]
    tipos = relatorio["por_tipo"]
    total_ok = len([r for r in todos if r.get("sucesso")])
    total_fail = len([r for r in todos if not r.get("sucesso")])
    print(f"\n{'='*70}", flush=True)
    print(f"  RELATÓRIO FINAL — Modo: {modo.upper()}", flush=True)
    print(f"  Sucessos: {total_ok}/{len(todos)} | Falhas: {total_fail}", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"  {'Tipo':<8} {'P@5':>8} {'R@5':>8} {'F1':>8} {'NDCG':>8} {'MRR':>8} {'Lat(ms)':>10}", flush=True)
    print(f"  {'-'*60}", flush=True)
    for tipo, metricas in tipos.items():
        nome_tipo = {"A": "Factual", "B": "Semântico", "C": "Complexo", "D": "Benefic."}.get(tipo, tipo)
        print(f"  {nome_tipo:<8} "
              f"{metricas.get('precision_at_5', 0):>8.2%} "
              f"{metricas.get('recall_at_5', 0):>8.2%} "
              f"{metricas.get('f1_score', 0):>8.2%} "
              f"{metricas.get('ndcg_at_5', 0):>8.2%} "
              f"{metricas.get('mrr', 0):>8.2%} "
              f"{metricas.get('latencia_media_ms', 0):>10.0f}", flush=True)
    print(f"  {'-'*60}", flush=True)
    print(f"  {'GERAL':<8} "
          f"{geral.get('precision_at_5', 0):>8.2%} "
          f"{geral.get('recall_at_5', 0):>8.2%} "
          f"{geral.get('f1_score', 0):>8.2%} "
          f"{geral.get('ndcg_at_5', 0):>8.2%} "
          f"{geral.get('mrr', 0):>8.2%} "
          f"{geral.get('latencia_media_ms', 0):>10.0f}", flush=True)
    print(f"{'='*70}\n", flush=True)

    return relatorio


def _salvar_resultados(todos_resultados, modo, output_path):
    """Recalcula métricas e salva resultados."""
    # Ordenar por ID
    todos_resultados.sort(key=lambda r: (r["tipo"], int(r["id"][1:])))

    tipos = {}
    for tipo in ["A", "B", "C", "D"]:
        tipo_resultados = [r for r in todos_resultados if r["tipo"] == tipo]
        if tipo_resultados:
            tipos[tipo] = calcular_metricas_agregadas(tipo_resultados)

    geral = calcular_metricas_agregadas(todos_resultados)

    relatorio = {
        "modo": modo,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "geral": geral,
        "por_tipo": tipos,
        "resultados": todos_resultados,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)

    return relatorio


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="hibrido")
    args = parser.parse_args()
    asyncio.run(retomar_avaliacao(args.modo))
