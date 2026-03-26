"""Conjunto de avaliação com 120 consultas tipadas (30 por tipo).

Todas as consultas foram projetadas para o contexto da base de dados
disponível: emendas parlamentares do estado do Acre (2020–2024),
com 607 emendas, 915 parlamentares, 371 beneficiários e
136 classificações orçamentárias.
"""
import pytest

# ============================================
# TIPO A — Consultas factuais diretas
# Filtro único/simples, resposta objetiva
# ============================================
CONSULTAS_TIPO_A = [
    {"id": "A1", "consulta": "Qual o valor total das emendas individuais do deputado Roberto Duarte em 2024?",
     "esperado": {"autor": "ROBERTO DUARTE", "ano": 2024}},
    {"id": "A2", "consulta": "Quantas emendas foram destinadas ao Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A3", "consulta": "Qual deputado do PT mais destinou emendas ao Acre em 2024?",
     "esperado": {"partido": "PT", "uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "A4", "consulta": "Quanto foi pago em emendas de bancada para o Acre em 2022?",
     "esperado": {"uf": "AC", "ano": 2022, "tipo_emenda": "bancada"}},
    {"id": "A5", "consulta": "Quantas emendas individuais foram empenhadas no Acre em 2020?",
     "esperado": {"uf": "AC", "ano": 2020, "tipo_emenda": "individual"}},
    {"id": "A6", "consulta": "Qual o valor total das emendas de comissão no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "tipo_emenda": "comissao"}},
    {"id": "A7", "consulta": "Quais parlamentares do Acre tiveram emendas em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A8", "consulta": "Qual o valor médio das emendas individuais no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "tipo_emenda": "individual", "operacao": "media"}},
    {"id": "A9", "consulta": "Quantos parlamentares distintos tiveram emendas no Acre em 2021?",
     "esperado": {"uf": "AC", "ano": 2021, "operacao": "contagem_distinta"}},
    {"id": "A10", "consulta": "Qual o total empenhado em emendas para o Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024}},
    {"id": "A11", "consulta": "Qual o valor pago em emendas da deputada Jéssica Sales em 2023?",
     "esperado": {"autor": "JESSICA SALES", "ano": 2023}},
    {"id": "A12", "consulta": "Quantas emendas de bancada existem no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "tipo_emenda": "bancada"}},
    {"id": "A13", "consulta": "Quais emendas foram destinadas ao Acre em 2020?",
     "esperado": {"uf": "AC", "ano": 2020}},
    {"id": "A14", "consulta": "Qual o total empenhado em emendas para o Acre em 2022?",
     "esperado": {"uf": "AC", "ano": 2022}},
    {"id": "A15", "consulta": "Quais deputados do PL tiveram emendas no Acre em 2023?",
     "esperado": {"partido": "PL", "uf": "AC", "ano": 2023}},
    {"id": "A16", "consulta": "Qual o valor liquidado em emendas individuais do Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "tipo_emenda": "individual"}},
    {"id": "A17", "consulta": "Quantas emendas foram pagas no Acre em 2021?",
     "esperado": {"uf": "AC", "ano": 2021}},
    {"id": "A18", "consulta": "Qual deputado do MDB mais destinou emendas ao Acre em 2022?",
     "esperado": {"partido": "MDB", "uf": "AC", "ano": 2022, "operacao": "ranking"}},
    {"id": "A19", "consulta": "Qual o total empenhado em emendas de relator no Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023, "tipo_emenda": "relator"}},
    {"id": "A20", "consulta": "Quantas emendas foram destinadas ao Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024}},
    {"id": "A21", "consulta": "Qual o valor total das emendas do deputado Alan Rick em 2024?",
     "esperado": {"autor": "ALAN RICK", "ano": 2024}},
    {"id": "A22", "consulta": "Quanto foi empenhado em emendas para o Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023}},
    {"id": "A23", "consulta": "Quais parlamentares do UNIÃO tiveram emendas no Acre em 2024?",
     "esperado": {"partido": "UNIAO", "uf": "AC", "ano": 2024}},
    {"id": "A24", "consulta": "Qual o valor pago em emendas individuais no Acre em 2022?",
     "esperado": {"uf": "AC", "ano": 2022, "tipo_emenda": "individual"}},
    {"id": "A25", "consulta": "Quantas emendas de comissão existem no Acre em 2021?",
     "esperado": {"uf": "AC", "ano": 2021, "tipo_emenda": "comissao"}},
    {"id": "A26", "consulta": "Qual deputado do PP mais destinou emendas ao Acre em 2024?",
     "esperado": {"partido": "PP", "uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "A27", "consulta": "Qual o total empenhado em emendas da deputada Perpétua Almeida em 2023?",
     "esperado": {"autor": "PERPETUA ALMEIDA", "ano": 2023}},
    {"id": "A28", "consulta": "Quantas emendas foram destinadas ao Acre em 2022?",
     "esperado": {"uf": "AC", "ano": 2022}},
    {"id": "A29", "consulta": "Qual o valor médio das emendas de bancada no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "tipo_emenda": "bancada", "operacao": "media"}},
    {"id": "A30", "consulta": "Quanto foi pago em emendas do deputado Flaviano Melo no Acre em 2024?",
     "esperado": {"autor": "FLAVIANO MELO", "uf": "AC", "ano": 2024}},
]

# ============================================
# TIPO B — Cruzamento de fontes / mapeamento semântico
# Requerem mapeamento de área temática via dicionário
# ============================================
CONSULTAS_TIPO_B = [
    {"id": "B1", "consulta": "Quais emendas para saúde foram executadas no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023}},
    {"id": "B2", "consulta": "Qual partido destinou mais recursos para educação no Acre?",
     "esperado": {"area": "educacao", "uf": "AC", "operacao": "ranking"}},
    {"id": "B3", "consulta": "Quanto foi investido em segurança pública no Acre em 2024?",
     "esperado": {"area": "seguranca", "uf": "AC", "ano": 2024}},
    {"id": "B4", "consulta": "Quais emendas para transporte foram pagas no Acre?",
     "esperado": {"area": "transporte", "uf": "AC"}},
    {"id": "B5", "consulta": "Qual deputado mais investiu em meio ambiente no Acre em 2023?",
     "esperado": {"area": "meio ambiente", "uf": "AC", "ano": 2023, "operacao": "ranking"}},
    {"id": "B6", "consulta": "Emendas para assistência social no Acre em 2022?",
     "esperado": {"area": "assistencia social", "uf": "AC", "ano": 2022}},
    {"id": "B7", "consulta": "Quanto foi pago em emendas para cultura no Acre?",
     "esperado": {"area": "cultura", "uf": "AC"}},
    {"id": "B8", "consulta": "Quais parlamentares destinaram emendas para agricultura no Acre?",
     "esperado": {"area": "agricultura", "uf": "AC"}},
    {"id": "B9", "consulta": "Valor total das emendas para habitação no Acre em 2024?",
     "esperado": {"area": "habitacao", "uf": "AC", "ano": 2024}},
    {"id": "B10", "consulta": "Emendas para saneamento básico no Acre em 2023?",
     "esperado": {"area": "saneamento basico", "uf": "AC", "ano": 2023}},
    {"id": "B11", "consulta": "Quanto foi empenhado em emendas para ciência e tecnologia no Acre em 2024?",
     "esperado": {"area": "ciencia e tecnologia", "uf": "AC", "ano": 2024}},
    {"id": "B12", "consulta": "Quais emendas para defesa nacional foram pagas no Acre em 2023?",
     "esperado": {"area": "defesa nacional", "uf": "AC", "ano": 2023}},
    {"id": "B13", "consulta": "Qual deputado mais investiu em educação no Acre em 2024?",
     "esperado": {"area": "educacao", "uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "B14", "consulta": "Emendas para trabalho e emprego no Acre em 2023?",
     "esperado": {"area": "trabalho", "uf": "AC", "ano": 2023}},
    {"id": "B15", "consulta": "Valor das emendas para desporto e lazer no Acre em 2022?",
     "esperado": {"area": "desporto e lazer", "uf": "AC", "ano": 2022}},
    {"id": "B16", "consulta": "Quais emendas de saúde foram pagas no Acre em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024}},
    {"id": "B17", "consulta": "Quanto foi investido em comunicações no Acre em 2023?",
     "esperado": {"area": "comunicacoes", "uf": "AC", "ano": 2023}},
    {"id": "B18", "consulta": "Emendas para urbanismo no Acre em 2024?",
     "esperado": {"area": "urbanismo", "uf": "AC", "ano": 2024}},
    {"id": "B19", "consulta": "Qual partido mais investiu em saúde no Acre em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "B20", "consulta": "Emendas para previdência social no Acre em 2023?",
     "esperado": {"area": "previdencia social", "uf": "AC", "ano": 2023}},
    {"id": "B21", "consulta": "Quanto o PL investiu em educação no Acre em 2024?",
     "esperado": {"partido": "PL", "area": "educacao", "uf": "AC", "ano": 2024}},
    {"id": "B22", "consulta": "Emendas para direitos da cidadania no Acre em 2023?",
     "esperado": {"area": "direitos da cidadania", "uf": "AC", "ano": 2023}},
    {"id": "B23", "consulta": "Qual deputado do MDB mais investiu em transporte no Acre em 2022?",
     "esperado": {"partido": "MDB", "area": "transporte", "uf": "AC", "ano": 2022, "operacao": "ranking"}},
    {"id": "B24", "consulta": "Emendas para segurança pública no Acre em 2024?",
     "esperado": {"area": "seguranca", "uf": "AC", "ano": 2024}},
    {"id": "B25", "consulta": "Valor das emendas para saúde no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023}},
    {"id": "B26", "consulta": "Quanto foi pago em emendas para educação no Acre em 2024?",
     "esperado": {"area": "educacao", "uf": "AC", "ano": 2024}},
    {"id": "B27", "consulta": "Emendas para agricultura no Acre em 2022?",
     "esperado": {"area": "agricultura", "uf": "AC", "ano": 2022}},
    {"id": "B28", "consulta": "Qual deputado mais investiu em saneamento no Acre em 2023?",
     "esperado": {"area": "saneamento", "uf": "AC", "ano": 2023, "operacao": "ranking"}},
    {"id": "B29", "consulta": "Emendas para meio ambiente no Acre em 2024?",
     "esperado": {"area": "meio ambiente", "uf": "AC", "ano": 2024}},
    {"id": "B30", "consulta": "Quanto foi empenhado em assistência social no Acre em 2023?",
     "esperado": {"area": "assistencia social", "uf": "AC", "ano": 2023}},
]

# ============================================
# TIPO C — Comparação temporal / análise de tendências
# Requerem raciocínio sobre dados, múltiplos anos ou comparações
# ============================================
CONSULTAS_TIPO_C = [
    {"id": "C1", "consulta": "Houve aumento nas emendas para saneamento básico no Acre entre 2022 e 2024?",
     "esperado": {"area": "saneamento", "uf": "AC", "ano_inicio": 2022, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C2", "consulta": "Compare as emendas para educação entre PT e PL no Acre em 2024.",
     "esperado": {"area": "educacao", "uf": "AC", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C3", "consulta": "Qual a tendência das emendas para saúde no Acre de 2020 a 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C4", "consulta": "Quais áreas temáticas mais receberam emendas no Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "ranking"}},
    {"id": "C5", "consulta": "Como evoluíram as emendas de bancada vs individuais no Acre entre 2020 e 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "comparacao"}},
    {"id": "C6", "consulta": "Top 3 deputados que mais destinaram para saúde no Acre em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "C7", "consulta": "As emendas para segurança pública cresceram no Acre entre 2021 e 2024?",
     "esperado": {"area": "seguranca", "uf": "AC", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C8", "consulta": "Compare os investimentos em transporte e saúde no Acre em 2023.",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C9", "consulta": "Quais áreas tiveram mais crescimento em emendas no Acre de 2020 a 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C10", "consulta": "Qual a proporção entre valor empenhado e valor pago nas emendas do Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C11", "consulta": "Como evoluiu o investimento em saúde no Acre entre 2020 e 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C12", "consulta": "Compare as emendas para educação e saúde no Acre em 2023.",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C13", "consulta": "Quais partidos mais aumentaram investimento em saúde no Acre de 2021 a 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C14", "consulta": "Top 5 deputados que mais receberam emendas no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "C15", "consulta": "A taxa de execução (pago/empenhado) melhorou no Acre entre 2022 e 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2022, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C16", "consulta": "Compare o investimento em agricultura e urbanismo no Acre em 2023.",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C17", "consulta": "Quais deputados do Acre mais aumentaram suas emendas entre 2020 e 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C18", "consulta": "Houve crescimento nas emendas de meio ambiente no Acre de 2021 a 2024?",
     "esperado": {"area": "meio ambiente", "uf": "AC", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C19", "consulta": "Compare as emendas para segurança e educação no Acre em 2024.",
     "esperado": {"uf": "AC", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C20", "consulta": "Qual partido teve maior crescimento em emendas de educação no Acre de 2020 a 2024?",
     "esperado": {"area": "educacao", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C21", "consulta": "Top 3 partidos que mais investiram em transporte no Acre em 2023?",
     "esperado": {"area": "transporte", "uf": "AC", "ano": 2023, "operacao": "ranking"}},
    {"id": "C22", "consulta": "Como evoluíram as emendas para cultura no Acre entre 2020 e 2024?",
     "esperado": {"area": "cultura", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C23", "consulta": "Compare emendas individuais vs de comissão no Acre em 2024.",
     "esperado": {"uf": "AC", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C24", "consulta": "Quais deputados mais investiram em saúde no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023, "operacao": "ranking"}},
    {"id": "C25", "consulta": "A participação do PT em emendas de educação no Acre cresceu de 2020 a 2024?",
     "esperado": {"partido": "PT", "area": "educacao", "uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C26", "consulta": "Compare emendas de saúde no Acre entre primeiro e segundo semestre de 2024.",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C27", "consulta": "Quais as 5 áreas com mais emendas empenhadas no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "operacao": "ranking"}},
    {"id": "C28", "consulta": "Houve mudança na distribuição de emendas por tipo no Acre entre 2021 e 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "comparacao"}},
    {"id": "C29", "consulta": "Compare investimentos em habitação e saneamento no Acre em 2023.",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C30", "consulta": "Qual a evolução do valor médio por emenda no Acre de 2020 a 2024?",
     "esperado": {"uf": "AC", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
]

# ============================================
# TIPO D — Consultas de beneficiários (NOVO)
# Requerem dados das tabelas documentos_emenda e beneficiarios
# ============================================
CONSULTAS_TIPO_D = [
    # D1-D10: Por nome de beneficiário
    {"id": "D1", "consulta": "Quais recursos a UFAC recebeu via emendas parlamentares?",
     "esperado": {"beneficiario": "UFAC", "busca_beneficiario": True}},
    {"id": "D2", "consulta": "A Prefeitura de Rio Branco recebeu emendas em 2024?",
     "esperado": {"beneficiario": "Prefeitura de Rio Branco", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D3", "consulta": "Quais emendas foram destinadas ao IFAC?",
     "esperado": {"beneficiario": "IFAC", "busca_beneficiario": True}},
    {"id": "D4", "consulta": "A Santa Casa de Misericórdia recebeu recursos de emendas em 2023?",
     "esperado": {"beneficiario": "Santa Casa", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D5", "consulta": "Quais hospitais receberam emendas no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D6", "consulta": "A FUNAI recebeu recursos via emendas parlamentares no Acre em 2023?",
     "esperado": {"beneficiario": "FUNAI", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D7", "consulta": "Quais emendas foram destinadas ao IFAC em 2024?",
     "esperado": {"beneficiario": "IFAC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D8", "consulta": "A Prefeitura de Cruzeiro do Sul recebeu emendas em 2024?",
     "esperado": {"beneficiario": "Prefeitura de Cruzeiro do Sul", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D9", "consulta": "Quais ONGs receberam emendas para assistência social no Acre em 2023?",
     "esperado": {"area": "assistencia social", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D10", "consulta": "O SESC recebeu recursos de emendas parlamentares no Acre em 2024?",
     "esperado": {"beneficiario": "SESC", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},

    # D11-D20: Por tipo de beneficiário
    {"id": "D11", "consulta": "Quais empresas receberam emendas de saúde no Acre em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D12", "consulta": "Quais prefeituras do Acre receberam mais recursos de emendas em 2023?",
     "esperado": {"uf": "AC", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D13", "consulta": "Quais instituições de ensino receberam emendas de educação no Acre em 2024?",
     "esperado": {"area": "educacao", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D14", "consulta": "Quais entidades receberam emendas de cultura no Acre em 2023?",
     "esperado": {"area": "cultura", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D15", "consulta": "Quais fundações receberam recursos via emendas no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D16", "consulta": "Quais institutos federais receberam emendas para educação no Acre em 2023?",
     "esperado": {"area": "educacao", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D17", "consulta": "Quais municípios do Acre receberam emendas de saúde em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D18", "consulta": "Quais cooperativas receberam emendas de agricultura no Acre em 2023?",
     "esperado": {"area": "agricultura", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D19", "consulta": "Quais entidades de assistência social receberam emendas no Acre em 2024?",
     "esperado": {"area": "assistencia social", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D20", "consulta": "Quais hospitais receberam mais recursos de emendas no Acre em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},

    # D21-D30: Consultas cruzadas (beneficiário + parlamentar/partido)
    {"id": "D21", "consulta": "Qual deputado mais destinou recursos para instituições de ensino no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D22", "consulta": "Quais beneficiários receberam emendas do deputado Roberto Duarte em 2024?",
     "esperado": {"autor": "ROBERTO DUARTE", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D23", "consulta": "O PT destinou emendas para quais hospitais no Acre em 2023?",
     "esperado": {"partido": "PT", "uf": "AC", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D24", "consulta": "Quais entidades receberam emendas de bancada no Acre em 2024?",
     "esperado": {"tipo_emenda": "bancada", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D25", "consulta": "Qual beneficiário recebeu mais recursos via emendas no Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D26", "consulta": "Quais prefeituras receberam emendas do PL para educação no Acre em 2024?",
     "esperado": {"partido": "PL", "area": "educacao", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D27", "consulta": "A UFAC recebeu emendas de quais parlamentares em 2024?",
     "esperado": {"beneficiario": "UFAC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D28", "consulta": "Quais beneficiários receberam mais de R$ 1 milhão via emendas no Acre em 2024?",
     "esperado": {"uf": "AC", "ano": 2024, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D29", "consulta": "Quais entidades de saúde no Acre receberam emendas individuais em 2023?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2023, "tipo_emenda": "individual", "busca_beneficiario": True}},
    {"id": "D30", "consulta": "Qual o total de recursos recebidos pela Prefeitura de Rio Branco via emendas entre 2020 e 2024?",
     "esperado": {"beneficiario": "Prefeitura de Rio Branco", "ano_inicio": 2020, "ano_fim": 2024, "busca_beneficiario": True}},
]


# ============================================
# Testes de definição
# ============================================

def test_consultas_tipo_a_definidas():
    assert len(CONSULTAS_TIPO_A) == 30


def test_consultas_tipo_b_definidas():
    assert len(CONSULTAS_TIPO_B) == 30


def test_consultas_tipo_c_definidas():
    assert len(CONSULTAS_TIPO_C) == 30


def test_consultas_tipo_d_definidas():
    assert len(CONSULTAS_TIPO_D) == 30


def test_total_120_consultas():
    total = CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C + CONSULTAS_TIPO_D
    assert len(total) == 120


def test_ids_unicos():
    total = CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C + CONSULTAS_TIPO_D
    ids = [c["id"] for c in total]
    assert len(ids) == len(set(ids)), "IDs duplicados encontrados"


def test_todas_consultas_tem_esperado():
    total = CONSULTAS_TIPO_A + CONSULTAS_TIPO_B + CONSULTAS_TIPO_C + CONSULTAS_TIPO_D
    for c in total:
        assert "esperado" in c, f"Consulta {c['id']} sem campo 'esperado'"
        assert len(c["esperado"]) > 0, f"Consulta {c['id']} com esperado vazio"


def test_tipo_d_tem_busca_beneficiario():
    for c in CONSULTAS_TIPO_D:
        assert c["esperado"].get("busca_beneficiario") is True, \
            f"Consulta {c['id']} sem busca_beneficiario=True"
