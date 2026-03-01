"""Conjunto de avaliação com 30 consultas tipadas."""
import pytest

CONSULTAS_TIPO_A = [
    {"id": "A1", "consulta": "Qual o valor total das emendas individuais do deputado Roberto Duarte em 2024?",
     "esperado": {"autor": "ROBERTO DUARTE", "ano": 2024}},
    {"id": "A2", "consulta": "Quantas emendas foram destinadas ao Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A3", "consulta": "Qual deputado do PT mais destinou emendas em 2024?",
     "esperado": {"partido": "PT", "ano": 2024}},
    {"id": "A4", "consulta": "Quanto foi pago em emendas de bancada para o Amazonas em 2022?",
     "esperado": {"uf": "AM", "ano": 2022, "tipo_emenda": "bancada"}},
    {"id": "A5", "consulta": "Quantas emendas individuais foram empenhadas em 2020?",
     "esperado": {"ano": 2020, "tipo_emenda": "individual"}},
    {"id": "A6", "consulta": "Qual o valor total das emendas de comissão em 2024?",
     "esperado": {"ano": 2024, "tipo_emenda": "comissao"}},
    {"id": "A7", "consulta": "Quais parlamentares do Acre tiveram emendas em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A8", "consulta": "Qual o valor médio das emendas individuais em 2024?",
     "esperado": {"ano": 2024, "tipo_emenda": "individual"}},
    {"id": "A9", "consulta": "Quantos parlamentares distintos tiveram emendas em 2021?",
     "esperado": {"ano": 2021}},
    {"id": "A10", "consulta": "Qual o total empenhado em emendas para Roraima em 2024?",
     "esperado": {"uf": "RR", "ano": 2024}},
]

CONSULTAS_TIPO_B = [
    {"id": "B1", "consulta": "Quais emendas para saúde foram executadas no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023}},
    {"id": "B2", "consulta": "Qual partido destinou mais recursos para educação na região Norte?",
     "esperado": {"area": "educacao", "uf": "norte"}},
    {"id": "B3", "consulta": "Quanto foi investido em segurança pública em São Paulo em 2024?",
     "esperado": {"area": "seguranca", "uf": "SP", "ano": 2024}},
    {"id": "B4", "consulta": "Quais emendas para transporte foram pagas no Pará?",
     "esperado": {"area": "transporte", "uf": "PA"}},
    {"id": "B5", "consulta": "Qual deputado mais investiu em meio ambiente em 2023?",
     "esperado": {"area": "meio ambiente", "ano": 2023}},
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
     "esperado": {"area": "educacao", "ano": 2024}},
    {"id": "C3", "consulta": "Qual a tendência das emendas para saúde no Acre de 2020 a 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024}},
    {"id": "C4", "consulta": "Quais estados do Nordeste mais receberam emendas para educação em 2023?",
     "esperado": {"area": "educacao", "uf": "nordeste", "ano": 2023}},
    {"id": "C5", "consulta": "Como evoluíram as emendas de bancada vs individuais entre 2020 e 2024?",
     "esperado": {"ano_inicio": 2020, "ano_fim": 2024}},
    {"id": "C6", "consulta": "Top 3 deputados do PSDB que mais destinaram para saúde no Sudeste?",
     "esperado": {"partido": "PSDB", "area": "saude", "uf": "sudeste"}},
    {"id": "C7", "consulta": "As emendas para segurança pública cresceram no RJ entre 2021 e 2024?",
     "esperado": {"area": "seguranca", "uf": "RJ", "ano_inicio": 2021, "ano_fim": 2024}},
    {"id": "C8", "consulta": "Compare os investimentos em transporte entre Norte e Sudeste em 2023.",
     "esperado": {"area": "transporte", "ano": 2023}},
    {"id": "C9", "consulta": "Quais áreas tiveram mais crescimento em emendas no Amazonas de 2020 a 2024?",
     "esperado": {"uf": "AM", "ano_inicio": 2020, "ano_fim": 2024}},
    {"id": "C10", "consulta": "Qual a proporção entre valor empenhado e valor pago nas emendas de 2024?",
     "esperado": {"ano": 2024}},
]


def test_consultas_tipo_a_definidas():
    assert len(CONSULTAS_TIPO_A) == 10


def test_consultas_tipo_b_definidas():
    assert len(CONSULTAS_TIPO_B) == 10


def test_consultas_tipo_c_definidas():
    assert len(CONSULTAS_TIPO_C) == 10


def test_total_30_consultas():
    assert len(CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C) == 30
