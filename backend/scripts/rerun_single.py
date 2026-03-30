"""Re-executa uma única consulta e atualiza o JSON de resultados."""
import asyncio
import io
import json
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
from app.services.cache import query_cache
from scripts.evaluate import TODAS_CONSULTAS, avaliar_resultado, calcular_metricas_agregadas

QUERY_ID = sys.argv[1] if len(sys.argv) > 1 else "D20"
MODO = sys.argv[2] if len(sys.argv) > 2 else "hibrido"

async def main():
    # Encontrar a consulta
    consulta_def = next(c for c in TODAS_CONSULTAS if c["id"] == QUERY_ID)
    consulta = consulta_def["consulta"]
    print(f"Re-executando {QUERY_ID} no modo {MODO}: {consulta}")

    db = SessionLocal()
    pipeline = RAGPipeline()
    query_cache.clear()

    try:
        inicio = time.time()
        resultado = await pipeline.processar(consulta, db, modo=MODO)
        latencia = int((time.time() - inicio) * 1000)

        metricas = avaliar_resultado(resultado, consulta_def)

        novo_resultado = {
            "id": QUERY_ID,
            "tipo": QUERY_ID[0],
            "consulta": consulta,
            "latencia_ms": latencia,
            "num_resultados": resultado["metadata"]["num_resultados"],
            "modo": resultado["metadata"]["modo"],
            "estrategia_hibrida": resultado["metadata"].get("estrategia_hibrida"),
            "metricas": metricas,
            "sucesso": True,
        }

        print(f"  Latência: {latencia}ms")
        print(f"  Resultados: {resultado['metadata']['num_resultados']}")
        print(f"  Estratégia: {resultado['metadata'].get('estrategia_hibrida')}")
        print(f"  F1: {metricas['f1_score']:.4f}")
        print(f"  NDCG@5: {metricas['ndcg_at_5']:.4f}")
        print(f"  Entity acc: {metricas['entity_accuracy']:.4f}")

        # Atualizar JSON
        modo_filename = {"hibrido": "hibrido", "sql_puro": "sql_puro", "vetorial_puro": "vetorial_puro"}
        json_path = Path(__file__).parent.parent / "tests" / "test_queries" / f"resultados_{modo_filename[MODO]}.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Substituir resultado
        for i, r in enumerate(data["resultados"]):
            if r["id"] == QUERY_ID:
                data["resultados"][i] = novo_resultado
                print(f"\n  Substituído resultado #{i} no JSON")
                break

        # Recalcular agregados
        tipos = {}
        for tipo in ["A", "B", "C", "D"]:
            tipo_resultados = [r for r in data["resultados"] if r["tipo"] == tipo]
            if tipo_resultados:
                tipos[tipo] = calcular_metricas_agregadas(tipo_resultados)
        data["por_tipo"] = tipos
        data["geral"] = calcular_metricas_agregadas(data["resultados"])

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Salvo: {json_path}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
