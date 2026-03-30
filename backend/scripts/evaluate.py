"""Script de avaliação expandido com métricas robustas.

Métricas implementadas:
- Precision@K, Recall@K, F1-Score
- NDCG@K (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)
- Correção factual (entity extraction accuracy)
- Latência média por tipo
"""
import asyncio
import json
import math
import sys
import time
import unicodedata
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
from app.services.cache import query_cache
import structlog

logger = structlog.get_logger()

# Importar consultas do arquivo de testes
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
from test_queries.test_evaluation import (
    CONSULTAS_TIPO_A, CONSULTAS_TIPO_B, CONSULTAS_TIPO_C,
)

# Importar tipo D se disponível
try:
    from test_queries.test_evaluation import CONSULTAS_TIPO_D
except ImportError:
    CONSULTAS_TIPO_D = []

TODAS_CONSULTAS = CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C + CONSULTAS_TIPO_D


# ============================================
# Funções de métricas
# ============================================

def _normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza para comparação."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


_CAMPOS_CONTROLE = {"busca_documentos", "busca_beneficiario", "operacao",
                     "ano_inicio", "ano_fim"}


def verificar_entidades(extraidas: dict, esperado: dict) -> dict:
    """Verifica se as entidades extraídas correspondem ao esperado.

    Campos de controle (operacao, busca_documentos, etc.) são excluídos
    da contagem pois são instruções de processamento, não entidades.
    """
    esperado_filtrado = {k: v for k, v in esperado.items()
                         if k not in _CAMPOS_CONTROLE}
    acertos = 0
    total = len(esperado_filtrado)
    detalhes = {}

    for campo, valor_esperado in esperado_filtrado.items():
        valor_extraido = extraidas.get(campo)
        if valor_extraido is not None:
            if isinstance(valor_esperado, str):
                match = _normalizar_texto(valor_esperado) in _normalizar_texto(str(valor_extraido))
            else:
                match = str(valor_esperado) == str(valor_extraido)
            if match:
                acertos += 1
            detalhes[campo] = {"esperado": valor_esperado, "extraido": valor_extraido, "ok": match}
        else:
            detalhes[campo] = {"esperado": valor_esperado, "extraido": None, "ok": False}

    return {
        "acertos": acertos,
        "total": total,
        "precisao": acertos / total if total else 0,
        "detalhes": detalhes,
    }


def calcular_precision_at_k(resultados_relevantes: list[bool], k: int = 5) -> float:
    """Precision@K: proporção de resultados relevantes nos top-K.

    Sempre divide por K (não por len(top_k)), penalizando sistemas
    que retornam menos de K resultados.
    """
    top_k = resultados_relevantes[:k]
    return sum(top_k) / k


def calcular_recall_at_k(resultados_relevantes: list[bool], total_relevantes: int, k: int = 5) -> float:
    """Recall@K: proporção de resultados relevantes recuperados nos top-K."""
    if total_relevantes == 0:
        return 0.0
    top_k = resultados_relevantes[:k]
    return sum(top_k) / total_relevantes


def calcular_f1(precision: float, recall: float) -> float:
    """F1-Score: média harmônica de precision e recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def calcular_ndcg_at_k(relevancia_scores: list[float], k: int = 5,
                       ideal_scores: list[float] = None) -> float:
    """NDCG@K: Normalized Discounted Cumulative Gain.

    Avalia a qualidade do ranking dos resultados.
    Se ideal_scores for fornecido, usa como base para IDCG (coleção completa).
    Caso contrário, usa os próprios scores retornados (fallback).
    """
    top_k = relevancia_scores[:k]
    if not top_k:
        return 0.0

    # DCG dos resultados retornados
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(top_k))

    # IDCG: ideal da coleção (se disponível) ou dos retornados
    if ideal_scores is not None:
        ideal = sorted(ideal_scores, reverse=True)[:k]
    else:
        ideal = sorted(relevancia_scores, reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))

    if idcg == 0:
        return 0.0
    return dcg / idcg


def _calcular_max_score(esperado: dict) -> float:
    """Score máximo possível para um resultado que corresponde perfeitamente à consulta.

    Usado para estimar o IDCG da coleção: todos os registros matching
    os filtros SQL teriam este score (pois casam UF, ano, area, etc.).
    """
    score = 0.0
    if esperado.get("uf"): score += 0.4
    if esperado.get("ano") or (esperado.get("ano_inicio") and esperado.get("ano_fim")): score += 0.2
    if esperado.get("autor"): score += 0.4
    if esperado.get("partido"): score += 0.3
    if esperado.get("tipo_emenda"): score += 0.2
    if esperado.get("area"): score += 0.3
    if esperado.get("busca_beneficiario"): score += 0.3
    if esperado.get("beneficiario"): score += 0.2
    return score


def calcular_mrr(resultados_relevantes: list[bool]) -> float:
    """MRR: Mean Reciprocal Rank — posição do primeiro resultado correto."""
    for i, relevante in enumerate(resultados_relevantes):
        if relevante:
            return 1.0 / (i + 1)
    return 0.0


def _calcular_score_relevancia(d: dict, esperado: dict) -> float:
    """Calcula score de relevância de um resultado baseado em correspondência de campos.

    Pesos: UF(0.4), ano(0.2), autor(0.4), partido(0.3), tipo_emenda(0.2),
           area(0.3), beneficiario(0.3). Threshold de relevância: >= 0.4.
    """
    score = 0.0
    if esperado.get("uf") and d.get("uf") == esperado.get("uf"):
        score += 0.4
    if esperado.get("ano") and str(d.get("ano", "")) == str(esperado.get("ano", "")):
        score += 0.2
    if esperado.get("autor") and esperado["autor"].lower() in str(d.get("nome_autor", "")).lower():
        score += 0.4
    if esperado.get("partido") and str(esperado["partido"]).upper() == str(d.get("partido", "")).upper():
        score += 0.3
    if esperado.get("tipo_emenda") and esperado["tipo_emenda"].lower() in str(d.get("tipo_emenda", "")).lower():
        score += 0.2
    # Verificar área temática via funcao_nome (com guard contra string vazia)
    if esperado.get("area") and d.get("funcao_nome"):
        area_val = _normalizar_texto(esperado["area"])
        funcao_nome = _normalizar_texto(str(d["funcao_nome"]))
        if funcao_nome and (area_val in funcao_nome or funcao_nome in area_val):
            score += 0.3
    # Verificar beneficiário (Type D queries)
    if esperado.get("busca_beneficiario"):
        beneficiario_nome = str(d.get("beneficiario_nome") or d.get("favorecido_nome") or "")
        if beneficiario_nome.strip():
            score += 0.3  # resultado tem dados de beneficiário
            if esperado.get("beneficiario"):
                benef_esperado = _normalizar_texto(esperado["beneficiario"])
                if benef_esperado in _normalizar_texto(beneficiario_nome):
                    score += 0.2  # beneficiário específico encontrado
    return score


def avaliar_resultado(resultado: dict, consulta_def: dict) -> dict:
    """Avalia um resultado individual com todas as métricas.

    Métricas:
    - P@5: sempre divide por K=5 (penaliza <5 resultados)
    - R@5: denominador = total_no_banco (ground truth)
    - NDCG@5: IDCG calculado sobre coleção ideal (max_score × total_no_banco)
    - Threshold de relevância: score >= 0.4
    """
    entidades = resultado.get("metadata", {}).get("entidades", {})
    verificacao = verificar_entidades(entidades, consulta_def["esperado"])

    dados = resultado.get("dados", [])
    esperado = consulta_def["esperado"]
    operacao = esperado.get("operacao", "busca")
    total_no_banco = resultado.get("metadata", {}).get("total_no_banco")

    # IDCG ideal da coleção: max_score replicado por min(total_no_banco, 20)
    max_score = _calcular_max_score(esperado)
    n_ideal = min(total_no_banco or 0, 20)
    ideal_scores = [max_score] * n_ideal if n_ideal > 0 else None

    # Para agregações (soma, contagem, ranking, media):
    # Avaliar pela correspondência de campos nos dados retornados,
    # não pela mera presença de resultado.
    if operacao in ("soma", "contagem", "ranking", "media", "contagem_distinta"):
        if not dados:
            return {
                "entity_accuracy": verificacao["precisao"],
                "entity_details": verificacao["detalhes"],
                "precision_at_5": 0.0,
                "recall_at_5": 0.0,
                "f1_score": 0.0,
                "ndcg_at_5": 0.0,
                "mrr": 0.0,
            }
        # Avaliar relevância dos dados retornados pela agregação
        # Rankings retornam múltiplos registros; soma/contagem retornam 1
        relevancia = []
        relevancia_scores = []
        for d in dados[:5]:
            score = _calcular_score_relevancia(d, esperado)
            relevancia.append(score >= 0.4)
            relevancia_scores.append(score)

        # Se nenhum campo estruturado pôde ser verificado (e.g., soma retorna
        # só valor agregado), métricas de retrieval ficam indefinidas.
        # Reportar entity_accuracy separadamente; retrieval = 0 (conservador).
        if not relevancia or (all(s == 0.0 for s in relevancia_scores)):
            return {
                "entity_accuracy": verificacao["precisao"],
                "entity_details": verificacao["detalhes"],
                "precision_at_5": 0.0,
                "recall_at_5": 0.0,
                "f1_score": 0.0,
                "ndcg_at_5": 0.0,
                "mrr": 0.0,
            }

        p_at_5 = calcular_precision_at_k(relevancia, k=5)
        ndcg = calcular_ndcg_at_k(relevancia_scores, k=5, ideal_scores=ideal_scores)
        mrr = calcular_mrr(relevancia)
        # Recall para agregações: total_no_banco é o ground truth (registros no banco)
        total_rel = total_no_banco if total_no_banco and total_no_banco > 0 else 0
        r_at_5 = calcular_recall_at_k(relevancia, total_rel, k=5)
        f1 = calcular_f1(p_at_5, r_at_5)

        return {
            "entity_accuracy": verificacao["precisao"],
            "entity_details": verificacao["detalhes"],
            "precision_at_5": p_at_5,
            "recall_at_5": r_at_5,
            "f1_score": f1,
            "ndcg_at_5": ndcg,
            "mrr": mrr,
        }

    # Para busca: scoring por correspondência de campos
    relevancia = []
    relevancia_scores = []
    for d in dados[:20]:
        score = _calcular_score_relevancia(d, esperado)
        relevancia.append(score >= 0.4)
        relevancia_scores.append(score)

    # Recall@5: denominador = total de registros no banco (ground truth)
    total_relevantes = total_no_banco if total_no_banco and total_no_banco > 0 else 0
    p_at_5 = calcular_precision_at_k(relevancia, k=5)
    r_at_5 = calcular_recall_at_k(relevancia, total_relevantes, k=5)
    f1 = calcular_f1(p_at_5, r_at_5)
    ndcg = calcular_ndcg_at_k(relevancia_scores, k=5, ideal_scores=ideal_scores)
    mrr = calcular_mrr(relevancia)

    return {
        "entity_accuracy": verificacao["precisao"],
        "entity_details": verificacao["detalhes"],
        "precision_at_5": p_at_5,
        "recall_at_5": r_at_5,
        "f1_score": f1,
        "ndcg_at_5": ndcg,
        "mrr": mrr,
    }


def calcular_metricas_agregadas(resultados: list[dict]) -> dict:
    """Calcula métricas agregadas para um conjunto de resultados."""
    if not resultados:
        return {}

    sucessos = [r for r in resultados if r.get("sucesso")]
    if not sucessos:
        return {"total": len(resultados), "sucessos": 0}

    metricas_keys = ["entity_accuracy", "precision_at_5", "recall_at_5",
                     "f1_score", "ndcg_at_5", "mrr"]
    agregadas = {}
    for key in metricas_keys:
        valores = [r["metricas"][key] for r in sucessos if "metricas" in r]
        agregadas[key] = sum(valores) / len(valores) if valores else 0

    agregadas["latencia_media_ms"] = sum(r["latencia_ms"] for r in sucessos) / len(sucessos)
    agregadas["total"] = len(resultados)
    agregadas["sucessos"] = len(sucessos)

    return agregadas


async def executar_avaliacao(modo: str = "hibrido"):
    """Executa avaliação completa.

    Args:
        modo: "hibrido" (padrão), "sql_puro", ou "vetorial_puro"
    """
    logger.info("iniciando_avaliacao", total=len(TODAS_CONSULTAS), modo=modo)

    db = SessionLocal()
    pipeline = RAGPipeline()
    resultados = []

    try:
        for consulta_def in TODAS_CONSULTAS:
            cid = consulta_def["id"]
            consulta = consulta_def["consulta"]

            logger.info("avaliando", id=cid, consulta=consulta[:50])

            max_retries = 5
            for attempt in range(max_retries):
                inicio = time.time()
                try:
                    resultado = await pipeline.processar(consulta, db, modo=modo)
                    latencia = int((time.time() - inicio) * 1000)

                    metricas = avaliar_resultado(resultado, consulta_def)

                    resultados.append({
                        "id": cid,
                        "tipo": cid[0],
                        "consulta": consulta,
                        "latencia_ms": latencia,
                        "num_resultados": resultado["metadata"]["num_resultados"],
                        "modo": resultado["metadata"]["modo"],
                        "estrategia_hibrida": resultado["metadata"].get("estrategia_hibrida"),
                        "metricas": metricas,
                        "sucesso": True,
                    })

                    logger.info("consulta_avaliada", id=cid,
                                 f1=f"{metricas['f1_score']:.2f}",
                                 ndcg=f"{metricas['ndcg_at_5']:.2f}",
                                 latencia_ms=latencia)
                    break  # sucesso, sair do loop de retry

                except Exception as e:
                    is_overloaded = "529" in str(e) or "overloaded" in str(e).lower()
                    if is_overloaded and attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32s
                        logger.warning("api_overloaded_retry", id=cid,
                                        attempt=attempt + 1, wait_s=wait)
                        await asyncio.sleep(wait)
                        # Limpar cache para retentar
                        cache_key = f"{modo}:{consulta}"
                        query_cache._cache.pop(cache_key, None)
                        continue
                    resultados.append({
                        "id": cid, "tipo": cid[0], "consulta": consulta,
                        "sucesso": False, "erro": str(e),
                    })
                    logger.error("erro_avaliacao", id=cid, erro=str(e))
                    break

        # Relatório por tipo
        tipos = {}
        for tipo in ["A", "B", "C", "D"]:
            tipo_resultados = [r for r in resultados if r["tipo"] == tipo]
            if tipo_resultados:
                tipos[tipo] = calcular_metricas_agregadas(tipo_resultados)

        # Relatório geral
        geral = calcular_metricas_agregadas(resultados)

        relatorio = {
            "modo": modo,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "geral": geral,
            "por_tipo": tipos,
            "resultados": resultados,
        }

        # Salvar resultados
        output_path = Path(__file__).parent.parent / "tests" / "test_queries" / f"resultados_{modo}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

        # Imprimir relatório
        print(f"\n{'='*70}")
        print(f"  RELATÓRIO DE AVALIAÇÃO — Modo: {modo.upper()}")
        print(f"{'='*70}")
        print(f"  Total: {geral.get('total', 0)} | Sucessos: {geral.get('sucessos', 0)}")
        print(f"{'='*70}")
        print(f"  {'Tipo':<8} {'P@5':>8} {'R@5':>8} {'F1':>8} {'NDCG':>8} {'MRR':>8} {'Lat(ms)':>10}")
        print(f"  {'-'*60}")

        for tipo, metricas in tipos.items():
            nome_tipo = {"A": "Factual", "B": "Semântico", "C": "Complexo", "D": "Benefic."}.get(tipo, tipo)
            print(f"  {nome_tipo:<8} "
                  f"{metricas.get('precision_at_5', 0):>8.2%} "
                  f"{metricas.get('recall_at_5', 0):>8.2%} "
                  f"{metricas.get('f1_score', 0):>8.2%} "
                  f"{metricas.get('ndcg_at_5', 0):>8.2%} "
                  f"{metricas.get('mrr', 0):>8.2%} "
                  f"{metricas.get('latencia_media_ms', 0):>10.0f}")

        print(f"  {'-'*60}")
        print(f"  {'GERAL':<8} "
              f"{geral.get('precision_at_5', 0):>8.2%} "
              f"{geral.get('recall_at_5', 0):>8.2%} "
              f"{geral.get('f1_score', 0):>8.2%} "
              f"{geral.get('ndcg_at_5', 0):>8.2%} "
              f"{geral.get('mrr', 0):>8.2%} "
              f"{geral.get('latencia_media_ms', 0):>10.0f}")

        # Distribuição de estratégias do planner (modo híbrido)
        strat_counts = {}
        for r in resultados:
            s = r.get("estrategia_hibrida") or "N/A"
            strat_counts[s] = strat_counts.get(s, 0) + 1
        if any(s != "N/A" for s in strat_counts):
            print(f"\n  Distribuição de estratégias do planner:")
            for s, c in sorted(strat_counts.items()):
                print(f"    {s}: {c} ({c/len(resultados):.0%})")
            # Breakdown por tipo
            for tipo in ["A", "B", "C", "D"]:
                tipo_strats = {}
                for r in resultados:
                    if r["tipo"] == tipo:
                        s = r.get("estrategia_hibrida") or "N/A"
                        tipo_strats[s] = tipo_strats.get(s, 0) + 1
                if tipo_strats:
                    parts = ", ".join(f"{s}:{c}" for s, c in sorted(tipo_strats.items()))
                    print(f"      Tipo {tipo}: {parts}")

        print(f"{'='*70}\n")

        return relatorio

    finally:
        db.close()


async def main():
    """Executa avaliação nos 3 modos para comparação."""
    import argparse
    parser = argparse.ArgumentParser(description="Avaliação de consultas")
    parser.add_argument("--modo", default="hibrido",
                        choices=["hibrido", "sql_puro", "vetorial_puro", "todos"],
                        help="Modo de avaliação")
    args = parser.parse_args()

    if args.modo == "todos":
        for modo in ["hibrido", "sql_puro", "vetorial_puro"]:
            query_cache.clear()
            await executar_avaliacao(modo)
    else:
        await executar_avaliacao(args.modo)


if __name__ == "__main__":
    asyncio.run(main())
