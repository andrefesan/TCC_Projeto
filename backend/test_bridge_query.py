import sys
import os
import asyncio
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup paths
os.chdir(r"c:\GitHub\TCC\TCC_Projeto\backend")
sys.path.insert(0, r"c:\GitHub\TCC\TCC_Projeto\backend")

# Load env from parent
from dotenv import load_dotenv
load_dotenv(r"c:\GitHub\TCC\TCC_Projeto\.env")

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline

async def main():
    db = SessionLocal()
    pipeline = RAGPipeline()

    query = "Quais emendas financiaram a construção de ponte sobre o Rio São Domingos em Buritis, Minas Gerais?"

    print("=" * 80)
    print("TESTE: Consulta sobre obra específica (ponte)")
    print(f"Query: {query}")
    print("=" * 80)

    # Test in hibrido mode
    print("\n--- MODO HÍBRIDO ---")
    try:
        result_h = await pipeline.processar(query, db, modo="hibrido")
        meta = result_h.get("metadata", {})
        print(f"Entidades: {json.dumps(meta.get('entidades', {}), ensure_ascii=False, indent=2)}")
        print(f"Estratégia: {meta.get('estrategia_hibrida')}")
        print(f"Num resultados: {meta.get('num_resultados')}")
        print(f"Latência: {meta.get('latencia_ms')}ms")
        print(f"Resposta (500 chars): {result_h.get('resposta', '')[:500]}")
    except Exception as e:
        print(f"ERRO hibrido: {e}")
        import traceback; traceback.print_exc()

    # Clear cache
    from app.services.cache import query_cache
    query_cache._cache.clear()

    # Test in sql_puro mode
    print("\n--- MODO SQL PURO ---")
    try:
        result_s = await pipeline.processar(query, db, modo="sql_puro")
        meta_s = result_s.get("metadata", {})
        print(f"Num resultados: {meta_s.get('num_resultados')}")
        print(f"Latência: {meta_s.get('latencia_ms')}ms")
        print(f"Resposta (500 chars): {result_s.get('resposta', '')[:500]}")
    except Exception as e:
        print(f"ERRO sql_puro: {e}")
        import traceback; traceback.print_exc()

    # Clear cache again
    query_cache._cache.clear()

    # Test in vetorial_puro mode
    print("\n--- MODO VETORIAL PURO ---")
    try:
        result_v = await pipeline.processar(query, db, modo="vetorial_puro")
        meta_v = result_v.get("metadata", {})
        print(f"Num resultados: {meta_v.get('num_resultados')}")
        print(f"Latência: {meta_v.get('latencia_ms')}ms")
        print(f"Resposta (500 chars): {result_v.get('resposta', '')[:500]}")
    except Exception as e:
        print(f"ERRO vetorial_puro: {e}")
        import traceback; traceback.print_exc()

    db.close()

asyncio.run(main())
