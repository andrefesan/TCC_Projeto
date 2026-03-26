"""Conjunto de avaliação com 120 consultas tipadas (30 por tipo).

Todas as consultas foram projetadas para o contexto da base de dados
nacional: emendas parlamentares de todos os 27 estados brasileiros
(2020–2024), com aproximadamente 32.787 emendas, 915 parlamentares
e 730.571 documentos de despesa com favorecidos finais.
"""
import pytest

# ============================================
# TIPO A — Consultas factuais diretas
# Filtro único/simples, resposta objetiva
# ============================================
CONSULTAS_TIPO_A = [
    {"id": "A1", "consulta": "Quantas emendas individuais o deputado Tasso Jereissati destinou ao Ceará em 2022?",
     "esperado": {"autor": "TASSO JEREISSATI", "uf": "CE", "ano": 2022, "tipo_emenda": "individual", "operacao": "contagem"}},
    {"id": "A2", "consulta": "Quantas emendas foram destinadas ao Acre em 2023?",
     "esperado": {"uf": "AC", "ano": 2023, "operacao": "contagem"}},
    {"id": "A3", "consulta": "Qual deputado do PT mais destinou emendas a Minas Gerais em 2024?",
     "esperado": {"partido": "PT", "uf": "MG", "ano": 2024, "operacao": "ranking"}},
    {"id": "A4", "consulta": "Quanto foi pago em emendas de bancada para o Rio de Janeiro em 2022?",
     "esperado": {"uf": "RJ", "ano": 2022, "tipo_emenda": "bancada", "operacao": "soma"}},
    {"id": "A5", "consulta": "Quantas emendas individuais foram empenhadas na Bahia em 2020?",
     "esperado": {"uf": "BA", "ano": 2020, "tipo_emenda": "individual", "operacao": "contagem"}},
    {"id": "A6", "consulta": "Qual o valor total das emendas de comissão no Rio Grande do Sul em 2024?",
     "esperado": {"uf": "RS", "ano": 2024, "tipo_emenda": "comissao", "operacao": "soma"}},
    {"id": "A7", "consulta": "Quais parlamentares de Pernambuco tiveram emendas em 2023?",
     "esperado": {"uf": "PE", "ano": 2023}},
    {"id": "A8", "consulta": "Qual o valor médio das emendas individuais em Goiás em 2024?",
     "esperado": {"uf": "GO", "ano": 2024, "tipo_emenda": "individual", "operacao": "media"}},
    {"id": "A9", "consulta": "Quantos parlamentares distintos tiveram emendas no Ceará em 2021?",
     "esperado": {"uf": "CE", "ano": 2021, "operacao": "contagem_distinta"}},
    {"id": "A10", "consulta": "Qual o total empenhado em emendas para o Paraná em 2024?",
     "esperado": {"uf": "PR", "ano": 2024, "operacao": "soma"}},
    {"id": "A11", "consulta": "Quantas emendas individuais o deputado Otto Alencar destinou à Bahia em 2021?",
     "esperado": {"autor": "OTTO ALENCAR", "uf": "BA", "ano": 2021, "tipo_emenda": "individual", "operacao": "contagem"}},
    {"id": "A12", "consulta": "Quantas emendas de bancada existem em Santa Catarina em 2024?",
     "esperado": {"uf": "SC", "ano": 2024, "tipo_emenda": "bancada", "operacao": "contagem"}},
    {"id": "A13", "consulta": "Quais emendas foram destinadas ao Pará em 2020?",
     "esperado": {"uf": "PA", "ano": 2020}},
    {"id": "A14", "consulta": "Qual o total empenhado em emendas para o Espírito Santo em 2022?",
     "esperado": {"uf": "ES", "ano": 2022, "operacao": "soma"}},
    {"id": "A15", "consulta": "Quais deputados do PL tiveram emendas no Distrito Federal em 2023?",
     "esperado": {"partido": "PL", "uf": "DF", "ano": 2023}},
    {"id": "A16", "consulta": "Qual o valor liquidado em emendas individuais de Rondônia em 2024?",
     "esperado": {"uf": "RO", "ano": 2024, "tipo_emenda": "individual", "operacao": "soma"}},
    {"id": "A17", "consulta": "Quantas emendas foram pagas no Maranhão em 2021?",
     "esperado": {"uf": "MA", "ano": 2021, "operacao": "contagem"}},
    {"id": "A18", "consulta": "Qual deputado do MDB mais destinou emendas à Bahia em 2022?",
     "esperado": {"partido": "MDB", "uf": "BA", "ano": 2022, "operacao": "ranking"}},
    {"id": "A19", "consulta": "Qual o total empenhado em emendas de relator no Rio Grande do Norte em 2023?",
     "esperado": {"uf": "RN", "ano": 2023, "tipo_emenda": "relator", "operacao": "soma"}},
    {"id": "A20", "consulta": "Quantas emendas foram destinadas ao Mato Grosso do Sul em 2024?",
     "esperado": {"uf": "MS", "ano": 2024, "operacao": "contagem"}},
    {"id": "A21", "consulta": "Qual o total empenhado em emendas individuais do PL no Tocantins em 2024?",
     "esperado": {"partido": "PL", "uf": "TO", "ano": 2024, "tipo_emenda": "individual", "operacao": "soma"}},
    {"id": "A22", "consulta": "Quanto foi empenhado em emendas para a Paraíba em 2023?",
     "esperado": {"uf": "PB", "ano": 2023, "operacao": "soma"}},
    {"id": "A23", "consulta": "Quais parlamentares do UNIÃO tiveram emendas no Amapá em 2024?",
     "esperado": {"partido": "UNIAO", "uf": "AP", "ano": 2024}},
    {"id": "A24", "consulta": "Qual o valor pago em emendas individuais no Piauí em 2022?",
     "esperado": {"uf": "PI", "ano": 2022, "tipo_emenda": "individual", "operacao": "soma"}},
    {"id": "A25", "consulta": "Quantas emendas de comissão existem em Goiás em 2021?",
     "esperado": {"uf": "GO", "ano": 2021, "tipo_emenda": "comissao", "operacao": "contagem"}},
    {"id": "A26", "consulta": "Qual deputado do PP mais destinou emendas ao Paraná em 2024?",
     "esperado": {"partido": "PP", "uf": "PR", "ano": 2024, "operacao": "ranking"}},
    {"id": "A27", "consulta": "Quantas emendas individuais do REPUBLICANOS foram destinadas a São Paulo em 2022?",
     "esperado": {"partido": "REPUBLICANOS", "uf": "SP", "ano": 2022, "tipo_emenda": "individual", "operacao": "contagem"}},
    {"id": "A28", "consulta": "Quantas emendas foram destinadas a Sergipe em 2022?",
     "esperado": {"uf": "SE", "ano": 2022, "operacao": "contagem"}},
    {"id": "A29", "consulta": "Qual o valor médio das emendas de bancada em Roraima em 2024?",
     "esperado": {"uf": "RR", "ano": 2024, "tipo_emenda": "bancada", "operacao": "media"}},
    {"id": "A30", "consulta": "Qual o valor empenhado em emendas do deputado Juarez Costa no Mato Grosso em 2021?",
     "esperado": {"autor": "JUAREZ COSTA", "uf": "MT", "ano": 2021, "operacao": "soma"}},
]

# ============================================
# TIPO B — Cruzamento de fontes / mapeamento semântico
# Requerem mapeamento de área temática via dicionário
# ============================================
CONSULTAS_TIPO_B = [
    {"id": "B1", "consulta": "Quais emendas para saúde foram executadas no Distrito Federal em 2023?",
     "esperado": {"area": "saude", "uf": "DF", "ano": 2023}},
    {"id": "B2", "consulta": "Qual partido destinou mais recursos para educação em Minas Gerais?",
     "esperado": {"area": "educacao", "uf": "MG", "operacao": "ranking"}},
    {"id": "B3", "consulta": "Quanto foi investido em segurança pública no Rio de Janeiro em 2024?",
     "esperado": {"area": "seguranca", "uf": "RJ", "ano": 2024, "operacao": "soma"}},
    {"id": "B4", "consulta": "Quais emendas para transporte foram pagas na Bahia?",
     "esperado": {"area": "transporte", "uf": "BA"}},
    {"id": "B5", "consulta": "Qual deputado mais investiu em meio ambiente no Pará em 2023?",
     "esperado": {"area": "meio ambiente", "uf": "PA", "ano": 2023, "operacao": "ranking"}},
    {"id": "B6", "consulta": "Emendas para assistência social no Rio Grande do Sul em 2022?",
     "esperado": {"area": "assistencia social", "uf": "RS", "ano": 2022}},
    {"id": "B7", "consulta": "Quanto foi pago em emendas para cultura em Pernambuco?",
     "esperado": {"area": "cultura", "uf": "PE", "operacao": "soma"}},
    {"id": "B8", "consulta": "Quais parlamentares destinaram emendas para agricultura no Paraná?",
     "esperado": {"area": "agricultura", "uf": "PR"}},
    {"id": "B9", "consulta": "Quanto foi investido em saúde no Acre em 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano": 2024, "operacao": "soma"}},
    {"id": "B10", "consulta": "Emendas para saneamento básico no Ceará em 2023?",
     "esperado": {"area": "saneamento basico", "uf": "CE", "ano": 2023}},
    {"id": "B11", "consulta": "Quanto foi empenhado em emendas para agricultura no Tocantins em 2024?",
     "esperado": {"area": "agricultura", "uf": "TO", "ano": 2024, "operacao": "soma"}},
    {"id": "B12", "consulta": "Quais emendas para segurança pública foram pagas em Roraima em 2023?",
     "esperado": {"area": "seguranca", "uf": "RR", "ano": 2023}},
    {"id": "B13", "consulta": "Qual deputado mais investiu em agricultura em Rondônia em 2024?",
     "esperado": {"area": "agricultura", "uf": "RO", "ano": 2024, "operacao": "ranking"}},
    {"id": "B14", "consulta": "Emendas para trabalho e emprego no Rio Grande do Sul em 2023?",
     "esperado": {"area": "trabalho", "uf": "RS", "ano": 2023}},
    {"id": "B15", "consulta": "Valor das emendas para desporto e lazer em Santa Catarina em 2022?",
     "esperado": {"area": "desporto e lazer", "uf": "SC", "ano": 2022, "operacao": "soma"}},
    {"id": "B16", "consulta": "Quais emendas de saúde foram pagas na Bahia em 2024?",
     "esperado": {"area": "saude", "uf": "BA", "ano": 2024}},
    {"id": "B17", "consulta": "Quanto foi investido em comunicações no Paraná em 2023?",
     "esperado": {"area": "comunicacoes", "uf": "PR", "ano": 2023, "operacao": "soma"}},
    {"id": "B18", "consulta": "Emendas para urbanismo em Goiás em 2024?",
     "esperado": {"area": "urbanismo", "uf": "GO", "ano": 2024}},
    {"id": "B19", "consulta": "Qual partido mais investiu em meio ambiente no Amapá em 2024?",
     "esperado": {"area": "meio ambiente", "uf": "AP", "ano": 2024, "operacao": "ranking"}},
    {"id": "B20", "consulta": "Emendas para previdência social em Pernambuco em 2023?",
     "esperado": {"area": "previdencia social", "uf": "PE", "ano": 2023}},
    {"id": "B21", "consulta": "Quanto o PL investiu em educação no Espírito Santo em 2024?",
     "esperado": {"partido": "PL", "area": "educacao", "uf": "ES", "ano": 2024, "operacao": "soma"}},
    {"id": "B22", "consulta": "Emendas para direitos da cidadania na Paraíba em 2023?",
     "esperado": {"area": "direitos da cidadania", "uf": "PB", "ano": 2023}},
    {"id": "B23", "consulta": "Qual deputado do MDB mais investiu em transporte em Mato Grosso do Sul em 2022?",
     "esperado": {"partido": "MDB", "area": "transporte", "uf": "MS", "ano": 2022, "operacao": "ranking"}},
    {"id": "B24", "consulta": "Emendas para segurança pública em São Paulo em 2024?",
     "esperado": {"area": "seguranca", "uf": "SP", "ano": 2024}},
    {"id": "B25", "consulta": "Valor das emendas para saúde no Ceará em 2023?",
     "esperado": {"area": "saude", "uf": "CE", "ano": 2023, "operacao": "soma"}},
    {"id": "B26", "consulta": "Quanto foi pago em emendas para educação no Rio Grande do Sul em 2024?",
     "esperado": {"area": "educacao", "uf": "RS", "ano": 2024, "operacao": "soma"}},
    {"id": "B27", "consulta": "Emendas para agricultura no Paraná em 2022?",
     "esperado": {"area": "agricultura", "uf": "PR", "ano": 2022}},
    {"id": "B28", "consulta": "Qual deputado mais investiu em saneamento em Alagoas em 2023?",
     "esperado": {"area": "saneamento", "uf": "AL", "ano": 2023, "operacao": "ranking"}},
    {"id": "B29", "consulta": "Emendas para meio ambiente no Amazonas em 2024?",
     "esperado": {"area": "meio ambiente", "uf": "AM", "ano": 2024}},
    {"id": "B30", "consulta": "Quanto foi empenhado em assistência social na Bahia em 2023?",
     "esperado": {"area": "assistencia social", "uf": "BA", "ano": 2023, "operacao": "soma"}},
]

# ============================================
# TIPO C — Comparação temporal / análise de tendências
# Requerem raciocínio sobre dados, múltiplos anos ou comparações
# ============================================
CONSULTAS_TIPO_C = [
    {"id": "C1", "consulta": "Houve aumento nas emendas para agricultura no Tocantins entre 2022 e 2024?",
     "esperado": {"area": "agricultura", "uf": "TO", "ano_inicio": 2022, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C2", "consulta": "Compare as emendas para educação entre PT e PL em Minas Gerais em 2024.",
     "esperado": {"area": "educacao", "uf": "MG", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C3", "consulta": "Qual a tendência das emendas para saúde no Rio de Janeiro de 2020 a 2024?",
     "esperado": {"area": "saude", "uf": "RJ", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C4", "consulta": "Quais áreas temáticas mais receberam emendas na Bahia em 2023?",
     "esperado": {"uf": "BA", "ano": 2023, "operacao": "ranking"}},
    {"id": "C5", "consulta": "Como evoluíram as emendas de bancada vs individuais no Paraná entre 2020 e 2024?",
     "esperado": {"uf": "PR", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "comparacao"}},
    {"id": "C6", "consulta": "Top 3 deputados que mais destinaram emendas para saúde no Distrito Federal em 2024?",
     "esperado": {"area": "saude", "uf": "DF", "ano": 2024, "operacao": "ranking"}},
    {"id": "C7", "consulta": "As emendas para segurança pública cresceram no Rio de Janeiro entre 2021 e 2024?",
     "esperado": {"area": "seguranca", "uf": "RJ", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C8", "consulta": "Compare os investimentos em transporte e saúde no Rio Grande do Sul em 2023.",
     "esperado": {"uf": "RS", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C9", "consulta": "Quais áreas tiveram mais crescimento em emendas em Pernambuco de 2020 a 2024?",
     "esperado": {"uf": "PE", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C10", "consulta": "Qual a proporção entre valor empenhado e valor pago nas emendas de Rondônia em 2024?",
     "esperado": {"uf": "RO", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C11", "consulta": "Como evoluiu o investimento em saúde no Ceará entre 2020 e 2024?",
     "esperado": {"area": "saude", "uf": "CE", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C12", "consulta": "Compare as emendas para educação e saúde em Sergipe em 2023.",
     "esperado": {"uf": "SE", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C13", "consulta": "O investimento em saúde no Acre cresceu entre 2021 e 2024?",
     "esperado": {"area": "saude", "uf": "AC", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C14", "consulta": "Top 5 deputados que mais receberam emendas no Rio de Janeiro em 2024?",
     "esperado": {"uf": "RJ", "ano": 2024, "operacao": "ranking"}},
    {"id": "C15", "consulta": "A taxa de execução (pago/empenhado) melhorou no Paraná entre 2022 e 2024?",
     "esperado": {"uf": "PR", "ano_inicio": 2022, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C16", "consulta": "Compare o investimento em agricultura e urbanismo em Goiás em 2023.",
     "esperado": {"uf": "GO", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C17", "consulta": "Quais deputados de Minas Gerais mais aumentaram suas emendas entre 2020 e 2024?",
     "esperado": {"uf": "MG", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C18", "consulta": "Houve crescimento nas emendas de meio ambiente no Pará de 2021 a 2024?",
     "esperado": {"area": "meio ambiente", "uf": "PA", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C19", "consulta": "Compare as emendas para segurança e educação no Rio Grande do Sul em 2024.",
     "esperado": {"uf": "RS", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C20", "consulta": "Qual partido teve maior crescimento em emendas de educação em Pernambuco de 2020 a 2024?",
     "esperado": {"area": "educacao", "uf": "PE", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C21", "consulta": "Top 3 partidos que mais investiram em transporte em Santa Catarina em 2023?",
     "esperado": {"area": "transporte", "uf": "SC", "ano": 2023, "operacao": "ranking"}},
    {"id": "C22", "consulta": "Como evoluíram as emendas para segurança em Roraima entre 2020 e 2024?",
     "esperado": {"area": "seguranca", "uf": "RR", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C23", "consulta": "Compare emendas individuais vs de comissão em São Paulo em 2024.",
     "esperado": {"uf": "SP", "ano": 2024, "operacao": "comparacao"}},
    {"id": "C24", "consulta": "Quais deputados mais investiram em saúde na Bahia em 2023?",
     "esperado": {"area": "saude", "uf": "BA", "ano": 2023, "operacao": "ranking"}},
    {"id": "C25", "consulta": "A participação do PT em emendas de educação no Ceará cresceu de 2020 a 2024?",
     "esperado": {"partido": "PT", "area": "educacao", "uf": "CE", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
    {"id": "C26", "consulta": "Compare emendas de São Paulo e Rio de Janeiro em 2024.",
     "esperado": {"ano": 2024, "operacao": "comparacao"}},
    {"id": "C27", "consulta": "Quais as 5 áreas com mais emendas empenhadas em Minas Gerais em 2024?",
     "esperado": {"uf": "MG", "ano": 2024, "operacao": "ranking"}},
    {"id": "C28", "consulta": "Houve mudança na distribuição de emendas por tipo no Rio Grande do Sul entre 2021 e 2024?",
     "esperado": {"uf": "RS", "ano_inicio": 2021, "ano_fim": 2024, "operacao": "comparacao"}},
    {"id": "C29", "consulta": "Compare investimentos em habitação e saneamento no Maranhão em 2023.",
     "esperado": {"uf": "MA", "ano": 2023, "operacao": "comparacao"}},
    {"id": "C30", "consulta": "Qual a evolução do valor médio por emenda em São Paulo de 2020 a 2024?",
     "esperado": {"uf": "SP", "ano_inicio": 2020, "ano_fim": 2024, "operacao": "tendencia"}},
]

# ============================================
# TIPO D — Consultas de beneficiários (NOVO)
# Requerem dados das tabelas documentos_emenda e beneficiarios
# ============================================
CONSULTAS_TIPO_D = [
    # D1-D10: Por nome de beneficiário / favorecido
    {"id": "D1", "consulta": "Quais recursos o Fundo Municipal de Saúde recebeu via emendas em Minas Gerais?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "MG", "busca_beneficiario": True}},
    {"id": "D2", "consulta": "O Banco do Brasil recebeu emendas no Distrito Federal em 2024?",
     "esperado": {"beneficiario": "Banco do Brasil", "uf": "DF", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D3", "consulta": "Quais emendas foram destinadas ao Fundo Estadual de Saúde no Rio Grande do Sul?",
     "esperado": {"beneficiario": "Fundo Estadual de Saude", "uf": "RS", "busca_beneficiario": True}},
    {"id": "D4", "consulta": "O Fundo Municipal de Assistência Social recebeu recursos de emendas no Tocantins em 2023?",
     "esperado": {"beneficiario": "Fundo Municipal de Assistencia Social", "uf": "TO", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D5", "consulta": "Quais hospitais receberam emendas no Rio de Janeiro em 2024?",
     "esperado": {"uf": "RJ", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D6", "consulta": "O Fundo Municipal de Saúde recebeu recursos via emendas no Paraná em 2023?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "PR", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D7", "consulta": "Quais emendas foram destinadas ao Fundo Municipal de Saúde em Goiás em 2024?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "GO", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D8", "consulta": "O Fundo Estadual de Saúde recebeu emendas no Acre em 2024?",
     "esperado": {"beneficiario": "Fundo Estadual de Saude", "uf": "AC", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D9", "consulta": "Quais entidades de assistência social receberam emendas na Bahia em 2023?",
     "esperado": {"area": "assistencia social", "uf": "BA", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D10", "consulta": "O Fundo Municipal de Saúde recebeu recursos de emendas no Ceará em 2024?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "CE", "ano": 2024, "busca_beneficiario": True}},

    # D11-D20: Por tipo de beneficiário
    {"id": "D11", "consulta": "Quais empresas receberam emendas de saúde em Rondônia em 2024?",
     "esperado": {"area": "saude", "uf": "RO", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D12", "consulta": "Quais prefeituras de Minas Gerais receberam mais recursos de emendas em 2023?",
     "esperado": {"uf": "MG", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D13", "consulta": "Quais instituições de ensino receberam emendas de educação no Rio de Janeiro em 2024?",
     "esperado": {"area": "educacao", "uf": "RJ", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D14", "consulta": "Quais entidades receberam emendas de meio ambiente no Amapá em 2023?",
     "esperado": {"area": "meio ambiente", "uf": "AP", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D15", "consulta": "Quais fundos receberam recursos via emendas no Rio Grande do Sul em 2024?",
     "esperado": {"uf": "RS", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D16", "consulta": "Quais entidades receberam emendas para educação em Pernambuco em 2023?",
     "esperado": {"area": "educacao", "uf": "PE", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D17", "consulta": "Quais municípios do Paraná receberam emendas de saúde em 2024?",
     "esperado": {"area": "saude", "uf": "PR", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D18", "consulta": "Quais entidades receberam emendas de meio ambiente no Amazonas em 2023?",
     "esperado": {"area": "meio ambiente", "uf": "AM", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D19", "consulta": "Quais entidades de assistência social receberam emendas no Amapá em 2024?",
     "esperado": {"area": "assistencia social", "uf": "AP", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D20", "consulta": "Quais hospitais receberam mais recursos de emendas em Minas Gerais em 2023?",
     "esperado": {"area": "saude", "uf": "MG", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},

    # D21-D30: Consultas cruzadas (beneficiário + parlamentar/partido)
    {"id": "D21", "consulta": "Qual deputado mais destinou recursos para instituições de ensino no Rio de Janeiro em 2024?",
     "esperado": {"uf": "RJ", "ano": 2024, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D22", "consulta": "Quais beneficiários receberam emendas da deputada Jandira Feghali em 2024?",
     "esperado": {"autor": "JANDIRA FEGHALI", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D23", "consulta": "O PT destinou emendas para quais hospitais em Roraima em 2023?",
     "esperado": {"partido": "PT", "uf": "RR", "ano": 2023, "busca_beneficiario": True}},
    {"id": "D24", "consulta": "Quais entidades receberam emendas de bancada no Rio Grande do Sul em 2024?",
     "esperado": {"tipo_emenda": "bancada", "uf": "RS", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D25", "consulta": "Qual beneficiário recebeu mais recursos via emendas em São Paulo em 2023?",
     "esperado": {"uf": "SP", "ano": 2023, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D26", "consulta": "Quais prefeituras receberam emendas do PL para educação na Bahia em 2024?",
     "esperado": {"partido": "PL", "area": "educacao", "uf": "BA", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D27", "consulta": "O Fundo Municipal de Saúde recebeu emendas de quais parlamentares em Goiás em 2024?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "GO", "ano": 2024, "busca_beneficiario": True}},
    {"id": "D28", "consulta": "Quais beneficiários receberam mais de R$ 1 milhão via emendas no Rio de Janeiro em 2024?",
     "esperado": {"uf": "RJ", "ano": 2024, "busca_beneficiario": True, "operacao": "ranking"}},
    {"id": "D29", "consulta": "Quais entidades de saúde em Pernambuco receberam emendas individuais em 2023?",
     "esperado": {"area": "saude", "uf": "PE", "ano": 2023, "tipo_emenda": "individual", "busca_beneficiario": True}},
    {"id": "D30", "consulta": "Qual o total de recursos recebidos pelo Fundo Municipal de Saúde via emendas em Minas Gerais entre 2020 e 2024?",
     "esperado": {"beneficiario": "Fundo Municipal de Saude", "uf": "MG", "ano_inicio": 2020, "ano_fim": 2024, "busca_beneficiario": True, "operacao": "soma"}},
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
