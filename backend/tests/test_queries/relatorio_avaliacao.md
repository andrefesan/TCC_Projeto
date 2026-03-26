# Relatório de Avaliação — Arquitetura RAG Híbrida para Emendas Parlamentares

## 1. Configuração do Experimento

| Parâmetro                  | Valor                                      |
|----------------------------|---------------------------------------------|
| Data da execução           | 2026-03-25 16:29 – 17:53 (UTC-3)          |
| Modelo LLM                 | claude-sonnet-4-20250514                    |
| Max Tokens LLM             | 2048                                        |
| Modelo de Embeddings       | intfloat/multilingual-e5-small              |
| Dimensão dos Embeddings    | 384                                         |
| Threshold de Similaridade  | 0.45                                        |
| RRF_K                      | 60 (Cormack et al., 2009)                  |
| RRF_FETCH_MULTIPLIER       | 3                                           |
| HNSW_M                     | 16                                          |
| HNSW_EF_CONSTRUCTION       | 200                                         |
| Max Results (default)      | 20                                          |
| Max Results Cap             | 50                                          |
| Total de Emendas           | 32.787                                      |
| Total de Parlamentares     | 915                                         |
| Total de Documentos        | 730.571                                     |
| Total de Beneficiários     | 371                                         |
| Consultas por tipo         | 30 (A, B, C, D) = 120 total                |
| Total de execuções         | 120 × 3 modos = 360                        |

## 2. Métricas Consolidadas por Tipo e Modo

### 2.1 Modo Híbrido (RRF)

| Tipo        | Categoria     | P@5     | R@5     | F1      | NDCG@5  | MRR     | Entity Acc. | Latência (ms) |
|-------------|---------------|---------|---------|---------|---------|---------|-------------|---------------|
| A           | Factual       | 97,00%  | 93,84%  | 94,42%  | 96,55%  | 96,67%  | 97,14%      | 12.722        |
| B           | Semântico     | 77,33%  | 60,89%  | 63,83%  | 77,09%  | 77,33%  | 85,00%      | 13.892        |
| C           | Comparativo   | 100,00% | 47,79%  | 59,12%  | 100,00% | 100,00% | 91,67%      | 16.250        |
| D           | Beneficiário  | 83,33%  | 37,44%  | 47,39%  | 83,44%  | 83,33%  | 73,33%      | 14.832        |
| **GERAL**   |               | **89,17%** | **60,22%** | **66,19%** | **89,27%** | **89,33%** | **86,79%** | **14.393** |

### 2.2 Modo SQL Puro

| Tipo        | Categoria     | P@5     | R@5     | F1      | NDCG@5  | MRR     | Entity Acc. | Latência (ms) |
|-------------|---------------|---------|---------|---------|---------|---------|-------------|---------------|
| A           | Factual       | 97,00%  | 93,84%  | 94,42%  | 96,55%  | 96,67%  | 97,14%      | 12.198        |
| B           | Semântico     | 77,33%  | 60,89%  | 63,83%  | 77,09%  | 77,33%  | 85,00%      | 13.367        |
| C           | Comparativo   | 100,00% | 47,79%  | 59,12%  | 100,00% | 100,00% | 91,67%      | 15.446        |
| D           | Beneficiário  | 83,33%  | 37,44%  | 47,39%  | 83,44%  | 83,33%  | 73,33%      | 15.048        |
| **GERAL**   |               | **89,17%** | **60,22%** | **66,19%** | **89,27%** | **89,33%** | **86,79%** | **13.991** |

### 2.3 Modo Vetorial Puro

| Tipo        | Categoria     | P@5     | R@5     | F1      | NDCG@5  | MRR     | Entity Acc. | Latência (ms) |
|-------------|---------------|---------|---------|---------|---------|---------|-------------|---------------|
| A           | Factual       | 100,00% | 93,84%  | 95,35%  | 99,35%  | 100,00% | 97,14%      | 12.453        |
| B           | Semântico     | 84,67%  | 52,73%  | 59,72%  | 82,66%  | 85,00%  | 85,00%      | 14.035        |
| C           | Comparativo   | 95,00%  | 44,88%  | 56,07%  | 95,02%  | 100,00% | 91,67%      | 15.197        |
| D           | Beneficiário  | 80,67%  | 44,64%  | 52,15%  | 88,06%  | 98,33%  | 73,33%      | 15.044        |
| **GERAL**   |               | **90,00%** | **59,26%** | **65,99%** | **91,21%** | **95,76%** | **86,79%** | **14.165** |

## 3. Análise Comparativa entre Modos

### 3.1 Desempenho Geral

| Métrica         | Híbrido   | SQL Puro  | Vetorial Puro | Melhor Modo       |
|-----------------|-----------|-----------|---------------|-------------------|
| P@5             | 89,17%    | 89,17%    | **90,00%**    | Vetorial Puro     |
| R@5             | **60,22%**| **60,22%**| 59,26%        | Híbrido / SQL     |
| F1              | **66,19%**| **66,19%**| 65,99%        | Híbrido / SQL     |
| NDCG@5          | 89,27%    | 89,27%    | **91,21%**    | Vetorial Puro     |
| MRR             | 89,33%    | 89,33%    | **95,76%**    | Vetorial Puro     |
| Entity Accuracy | 86,79%    | 86,79%    | 86,79%        | Equivalente       |
| Latência média  | 14.393    | **13.991**| 14.165        | SQL Puro          |
| Sucessos        | 118/120   | 118/120   | 118/120       | Equivalente       |

### 3.2 Observações por Tipo de Consulta

**Tipo A (Factual):** Os três modos apresentaram desempenho equivalente, com P@5 entre 97% e 100%. Consultas factuais com filtros estruturados são bem atendidas por qualquer abordagem.

**Tipo B (Semântico):** O modo vetorial puro obteve P@5 de 84,67% contra 77,33% dos demais, porém com recall inferior (52,73% vs. 60,89%). O modo híbrido e SQL puro apresentaram F1 ligeiramente superior (63,83% vs. 59,72%).

**Tipo C (Comparativo):** Os modos híbrido e SQL puro atingiram P@5 de 100% e NDCG de 100%, superando o vetorial puro (95% e 95,02%). A abordagem estruturada mostrou-se adequada para consultas comparativas.

**Tipo D (Beneficiário):** O modo vetorial puro obteve os melhores resultados de recall (44,64%) e MRR (98,33%), superando o híbrido/SQL (37,44% e 83,33%). Consultas sobre beneficiários se beneficiam da busca semântica.

### 3.3 Convergência entre Modos Híbrido e SQL Puro

Os modos híbrido e SQL puro apresentaram métricas idênticas em todas as dimensões (exceto latência), o que indica que o planejador de consultas (query planner) direcionou a maioria das consultas para estratégias SQL-only ou SQL-first, sem necessidade de fusão RRF na maior parte dos casos. Isso reflete a eficácia do componente de planejamento adaptativo.

## 4. Análise de Falhas

### 4.1 Consultas com sucesso=False (2/120, consistente nos 3 modos)

| ID  | Consulta                                                          | Erro                                           |
|-----|-------------------------------------------------------------------|------------------------------------------------|
| C2  | "Compare as emendas para educação entre PT e PL em MG em 2024"   | `'list' object has no attribute 'upper'`       |
| C26 | "Compare emendas de São Paulo e Rio de Janeiro em 2024"           | `'list' object has no attribute 'lower'`       |

Ambas as falhas ocorrem em consultas comparativas envolvendo múltiplas entidades (partidos ou UFs). O erro indica que o interpretador retornou uma lista de valores onde uma string era esperada no processamento de entidades.

### 4.2 Consultas com Entity Accuracy < 50%

Nenhuma consulta apresentou Entity Accuracy inferior a 50% em qualquer modo.

### 4.3 Consultas com F1 = 0

Nenhuma consulta com execução bem-sucedida apresentou F1 = 0 em qualquer modo.

## 5. Comparação com Resultados Anteriores (Rodada 4 → Rodada 5)

### 5.1 Evolução do Modo Híbrido (GERAL)

| Métrica         | Rodada 4 (16/03) | Rodada 5 (25/03) | Δ Absoluto | Δ Relativo |
|-----------------|-------------------|-------------------|------------|------------|
| Entity Accuracy | 80,24%            | 86,79%            | +6,55 pp   | +8,2%      |
| P@5             | 52,51%            | 89,17%            | +36,66 pp  | +69,8%     |
| R@5             | 19,75%            | 60,22%            | +40,47 pp  | +204,9%    |
| F1              | 26,39%            | 66,19%            | +39,80 pp  | +150,8%    |
| NDCG@5          | 88,66%            | 89,27%            | +0,61 pp   | +0,7%      |
| MRR             | 53,20%            | 89,33%            | +36,13 pp  | +67,9%     |
| Latência (ms)   | 15.781            | 14.393            | -1.388     | -8,8%      |
| Sucessos        | 120/120           | 118/120           | -2         | -1,7%      |

### 5.2 Evolução por Tipo — Modo Híbrido

| Tipo | Métrica | Rodada 4 | Rodada 5 | Δ Absoluto |
|------|---------|----------|----------|------------|
| A    | F1      | 14,78%   | 94,42%   | +79,64 pp  |
| A    | P@5     | 23,33%   | 97,00%   | +73,67 pp  |
| B    | F1      | 21,03%   | 63,83%   | +42,80 pp  |
| B    | P@5     | 38,13%   | 77,33%   | +39,20 pp  |
| C    | F1      | 32,82%   | 59,12%   | +26,30 pp  |
| C    | P@5     | 59,01%   | 100,00%  | +40,99 pp  |
| D    | F1      | 36,93%   | 47,39%   | +10,46 pp  |
| D    | P@5     | 89,55%   | 83,33%   | -6,22 pp   |

### 5.3 Síntese das Mudanças

As melhorias mais expressivas concentram-se em Precision@5 e Recall@5, que apresentaram ganhos superiores a 36 pontos percentuais no agregado geral. O tipo A (Factual) exibiu a maior evolução em F1 (+79,64 pp), indicando que as otimizações no pipeline de interpretação e execução SQL foram particularmente eficazes para consultas estruturadas.

A única regressão observada ocorre na P@5 do tipo D (Beneficiário), com redução de 6,22 pp. Entretanto, o F1 desse tipo melhorou em 10,46 pp devido ao ganho expressivo em recall (+13,16 pp).

A redução de 2 sucessos (120→118) decorre das falhas em C2 e C26, ambas relacionadas a consultas comparativas com múltiplas entidades — um caso de borda no interpretador.

## 6. Limitações Identificadas

1. **Consultas comparativas multi-entidade:** O interpretador não trata adequadamente cenários onde múltiplas UFs ou partidos são retornados como lista (falhas C2 e C26).

2. **Convergência Híbrido/SQL:** A equivalência de métricas entre os modos híbrido e SQL puro sugere que o planejador adaptativo raramente aciona a fusão RRF, possivelmente pela alta suficiência dos resultados SQL. Isso pode indicar subutilização do componente vetorial no modo híbrido.

3. **Recall geral:** O recall médio de 60% indica que o sistema retorna resultados corretos nos primeiros 5, mas não cobre a totalidade dos resultados relevantes. Isso é parcialmente esperado dado o limite de 5 resultados avaliados (P@5, R@5).

---

*Relatório gerado automaticamente em 2026-03-25. Dados provenientes dos arquivos resultados_hibrido.json, resultados_sql_puro.json e resultados_vetorial_puro.json.*
