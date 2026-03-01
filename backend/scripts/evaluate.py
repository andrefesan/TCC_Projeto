"""Script de avaliação com 30 consultas de teste."""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
import structlog

logger = structlog.get_logger()

CONSULTAS_TIPO_A = [
    {"id": "A1", "consulta": "Qual o valor total das emendas individuais do deputado Roberto Duarte em 2024?",
     "esperado": {"autor": "ROBERTO DUARTE", "ano": 2024}},
    {"id": "A2", "consulta": "Quantas emendas foram destinadas ao Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A3", "consulta": "Qual deputado do PT mais destinou emendas em 2024?",
     "esperado": {"partido": "PT", "ano": 2024, "operacao": "ranking"}},
    {"id": "A4", "consulta": "Quanto foi pago em emendas de bancada para o Amazonas em 2022?",
     "esperado": {"uf": "AM", "ano": 2022, "tipo_emenda": "bancada"}},
    {"id": "A5", "consulta": "Quantas emendas individuais foram empenhadas em 2020?",
     "esperado": {"ano": 2020, "tipo_emenda": "individual"}},
    {"id": "A6", "consulta": "Qual o valor total das emendas de comissão em 2024?",
     "esperado": {"ano": 2024, "tipo_emenda": "comissao"}},
    {"id": "A7", "consulta": "Quais parlamentares do Acre tiveram emendas em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A8", "consulta": "Qual o valor médio das emendas individuais em 2024?",
     "esperado": {"ano": 2024, "tipo_emenda": "individual", "operacao": "media"}},
    {"id": "A9", "consulta": "Quantos parlamentares distintos tiveram emendas em 2021?",
     "esperado": {"ano": 2021, "operacao": "contagem_distinta"}},
    {"id": "A10", "consulta": "Qual o total empenhado em emendas para Roraima em 2024?",
     "esperado": {"uf": "RR", "ano": 2024}},
]

CONSULTAS_TIPO_B = [
    {"id": "B1", "consulta": "Quais emendas para saúde foram executadas no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023}},
    {"id": "B2", "consulta": "Qual partido destinou mais recursos para educação na região Norte?",
     "esperado": {"area": "educacao", "uf": "norte", "operacao": "ranking"}},
    {"id": "B3", "consulta": "Quanto foi investido em segurança pública em São Paulo em 2024?",
     "esperado": {"area": "seguranca", "uf": "SP", "ano": 2024}},
    {"id": "B4", "consulta": "Quais emendas para transporte foram pagas no Pará?",
     "esperado": {"area": "transporte", "uf": "PA"}},
    {"id": "B5", "consulta": "Qual deputado mais investiu em meio ambiente em 2023?",
     "esperado": {"area": "meio ambiente", "ano": 2023, "operacao": "ranking"}},
    {"id": "B6", "consulta": "Emendas para assistência social no Nordeste em 2022?",
     "esperado": {"area": "assistencia social", "uf": "nordeste", "ano": 2022}},
    {"id": "B7", "consulta": "Quanto foi pago em emendas para cultura no Rio de Janeiro?",
     "esperado": {"area": "cultura", "uf": "RJ"}},
    {"id": "B8", "consulta": "Quais parlamentares destinaram emendas para agricultura no Sul?",
     "esperado": {"area": "agricultura", "uf": "sul"}},
    {"id": "B9", "consulta": "Valor total das emendas para habitação em Minas Gerais em 2024?",
     "esperado": {"area": "habitacao", "uf": "MG", "ano": 2024}},
    {"id": "B10", "consulta": "Emendas para saneamento básico na região Centro-Oeste?",
     "esperado": {"area": "saneamento basico", "uf": "centro-oeste"}},
]

CONSULTAS_TIPO_C = [
    {"id": "C1", "consulta": "Houve aumento nas emendas para saneamento básico no Norte entre 2022 e 2024?",
     "esperado": {"area": "saneamento", "uf": "norte", "ano_inicio": 2022, "ano_fim": 2024}},
    {"id": "C2", "consulta": "Compare as emendas para educação entre PT e PL em 2024.",
     "esperado": {"area": "educacao", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C3", "consulta": "Qual a tendência das emendas para saúde no Acre de 2020 a 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C4", "consulta": "Quais estados do Nordeste mais receberam emendas para educação em 2023?",
     "esperado": {"area": "educacao", "uf": "nordeste", "ano": 2023, "operacao": "ranking"}},
    {"id": "C5", "consulta": "Como evoluíram as emendas de bancada vs individuais entre 2020 e 2024?",
     "esperado": {"ano_inicio": 2020, "ano_fim": 2024, "operacao": "comparacao"}},
    {"id": "C6", "consulta": "Top 3 deputados do PSDB que mais destinaram para saúde no Sudeste?",
     "esperado": {"partido": "PSDB", "area": "saude", "uf": "sudeste", "operacao": "ranking"}},
    {"id": "C7", "consulta": "As emendas para segurança pública cresceram no Rio de Janeiro entre 2021 e 2024?",
     "esperado": {"area": "seguranca", "uf": "RJ", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C8", "consulta": "Compare os investimentos em transporte entre Norte e Sudeste em 2023.",
     "esperado": {"area": "transporte", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C9", "consulta": "Quais áreas tiveram mais crescimento em emendas no Amazonas de 2020 a 2024?",
     "esperado": {"uf": "AM", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C10", "consulta": "Qual a proporção entre valor empenhado e valor pago nas emendas de 2024?",
     "esperado": {"ano": 2024, "operacao": "comparacao"}},
]

TODAS_CONSULTAS = CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C


def verificar_entidades(extraidas: dict, esperado: dict) -> dict:
    """Verifica se as entidades extraídas correspondem ao esperado."""
    acertos = 0
    total = len(esperado)
    detalhes = {}

    for campo, valor_esperado in esperado.items():
        valor_extraido = extraidas.get(campo)
        if valor_extraido is not None:
            if isinstance(valor_esperado, str):
                match = valor_esperado.lower() in str(valor_extraido).lower()
            else:
                match = str(valor_esperado) == str(valor_extraido)
            if match:
                acertos += 1
            detalhes[campo] = {"esperado": valor_esperado, "extraido": valor_extraido, "ok": match}
        else:
            detalhes[campo] = {"esperado": valor_esperado, "extraido": None, "ok": False}

    return {"acertos": acertos, "total": total, "precisao": acertos / total if total else 0, "detalhes": detalhes}


async def main():
    logger.info("iniciando_avaliacao", total_consultas=len(TODAS_CONSULTAS))

    db = SessionLocal()
    pipeline = RAGPipeline()
    resultados = []

    try:
        for consulta_def in TODAS_CONSULTAS:
            cid = consulta_def["id"]
            consulta = consulta_def["consulta"]
            esperado = consulta_def["esperado"]

            logger.info("avaliando", id=cid, consulta=consulta[:50])
            inicio = time.time()

            try:
                resultado = await pipeline.processar(consulta, db)
                latencia = int((time.time() - inicio) * 1000)

                entidades = resultado.get("metadata", {}).get("entidades", {})
                verificacao = verificar_entidades(entidades, esperado)

                resultados.append({
                    "id": cid,
                    "consulta": consulta,
                    "latencia_ms": latencia,
                    "num_resultados": resultado["metadata"]["num_resultados"],
                    "modo": resultado["metadata"]["modo"],
                    "precisao_entidades": verificacao["precisao"],
                    "detalhes": verificacao["detalhes"],
                    "sucesso": True,
                })
                logger.info("consulta_avaliada", id=cid,
                             precisao=verificacao["precisao"], latencia_ms=latencia)

            except Exception as e:
                resultados.append({
                    "id": cid, "consulta": consulta,
                    "sucesso": False, "erro": str(e),
                })
                logger.error("erro_avaliacao", id=cid, erro=str(e))

        # Relatório
        tipo_a = [r for r in resultados if r["id"].startswith("A") and r["sucesso"]]
        tipo_b = [r for r in resultados if r["id"].startswith("B") and r["sucesso"]]
        tipo_c = [r for r in resultados if r["id"].startswith("C") and r["sucesso"]]

        def media_precisao(lista):
            return sum(r["precisao_entidades"] for r in lista) / len(lista) if lista else 0

        def media_latencia(lista):
            return sum(r["latencia_ms"] for r in lista) / len(lista) if lista else 0

        relatorio = {
            "total": len(resultados),
            "sucessos": sum(1 for r in resultados if r["sucesso"]),
            "tipo_a": {"precisao": media_precisao(tipo_a), "latencia_media_ms": media_latencia(tipo_a)},
            "tipo_b": {"precisao": media_precisao(tipo_b), "latencia_media_ms": media_latencia(tipo_b)},
            "tipo_c": {"precisao": media_precisao(tipo_c), "latencia_media_ms": media_latencia(tipo_c)},
            "resultados": resultados,
        }

        output_path = Path(__file__).parent.parent / "tests" / "test_queries" / "resultados_avaliacao.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"RELATÓRIO DE AVALIAÇÃO")
        print(f"{'='*60}")
        print(f"Total: {relatorio['total']} | Sucessos: {relatorio['sucessos']}")
        print(f"Tipo A (SQL direto):    Precisão {relatorio['tipo_a']['precisao']:.2%} | Latência {relatorio['tipo_a']['latencia_media_ms']:.0f}ms")
        print(f"Tipo B (Semântico):     Precisão {relatorio['tipo_b']['precisao']:.2%} | Latência {relatorio['tipo_b']['latencia_media_ms']:.0f}ms")
        print(f"Tipo C (Complexo):      Precisão {relatorio['tipo_c']['precisao']:.2%} | Latência {relatorio['tipo_c']['latencia_media_ms']:.0f}ms")
        print(f"{'='*60}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
