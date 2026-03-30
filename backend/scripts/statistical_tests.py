"""Testes de significância estatística para o artigo SEMISH.

Compara as três abordagens (híbrido, SQL puro, vetorial puro) usando
testes pareados (Wilcoxon signed-rank) e intervalos de confiança bootstrap.
"""
import json
import sys
import io
import numpy as np
from pathlib import Path
from scipy import stats

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar resultados
BASE = Path(__file__).parent.parent / "tests" / "test_queries"

def load_results(filename):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {r["id"]: r["metricas"] for r in data["resultados"] if r.get("sucesso")}

hibrido = load_results("resultados_hibrido.json")
sql_puro = load_results("resultados_sql_puro.json")
vetorial = load_results("resultados_vetorial_puro.json")

# Alinhar por ID de consulta (interseção — exclui consultas que falharam em algum modo)
common_ids = hibrido.keys() & sql_puro.keys() & vetorial.keys()
query_ids = sorted(common_ids)
n_excluded = max(len(hibrido), len(sql_puro), len(vetorial)) - len(query_ids)
if n_excluded:
    print(f"[AVISO] {n_excluded} consulta(s) excluída(s) por falha em algum modo")

METRICS = ["precision_at_5", "recall_at_5", "f1_score", "ndcg_at_5", "mrr"]
METRIC_LABELS = {"precision_at_5": "P@5", "recall_at_5": "R@5", "f1_score": "F1",
                 "ndcg_at_5": "NDCG@5", "mrr": "MRR"}

def get_arrays(metric):
    h = np.array([hibrido[qid][metric] for qid in query_ids])
    s = np.array([sql_puro[qid][metric] for qid in query_ids])
    v = np.array([vetorial[qid][metric] for qid in query_ids])
    return h, s, v

def bootstrap_ci(data, n_bootstrap=10000, ci=0.95, seed=42):
    """Intervalo de confiança bootstrap para a média."""
    rng = np.random.RandomState(seed)
    means = np.array([data[rng.randint(0, len(data), len(data))].mean()
                      for _ in range(n_bootstrap)])
    alpha = (1 - ci) / 2
    return np.percentile(means, [alpha * 100, (1 - alpha) * 100])

def wilcoxon_test(x, y):
    """Wilcoxon signed-rank test (bicaudal). Retorna statistic e p-value."""
    diff = x - y
    # Se todas as diferenças são zero, não há efeito
    if np.all(diff == 0):
        return 0.0, 1.0
    # Remover zeros (padrão do Wilcoxon: zero_method='wilcox')
    nonzero = diff[diff != 0]
    if len(nonzero) < 5:
        # Poucos pares não-empatados — reportar n_diff e retornar sem teste
        return float(len(nonzero)), 1.0
    stat, p = stats.wilcoxon(x, y, alternative='two-sided', zero_method='zsplit')
    return stat, p

def paired_ttest(x, y):
    """Paired t-test (bicaudal). Retorna statistic e p-value."""
    diff = x - y
    if np.all(diff == 0):
        return 0.0, 1.0
    stat, p = stats.ttest_rel(x, y)
    return stat, p

print("=" * 80)
print("  TESTES DE SIGNIFICÂNCIA ESTATÍSTICA — Artigo SEMISH")
print("  Wilcoxon signed-rank test (pareado, bicaudal) + IC 95% bootstrap")
print("=" * 80)

# 1. Intervalos de confiança para cada abordagem
print("\n1. INTERVALOS DE CONFIANÇA (95%, bootstrap 10.000 reamostras)")
print("-" * 80)
print(f"{'Métrica':<10} {'Híbrido (IC 95%)':<28} {'SQL Puro (IC 95%)':<28} {'Vetorial (IC 95%)':<28}")
print("-" * 80)
for m in METRICS:
    h, s, v = get_arrays(m)
    h_ci = bootstrap_ci(h)
    s_ci = bootstrap_ci(s)
    v_ci = bootstrap_ci(v)
    label = METRIC_LABELS[m]
    print(f"{label:<10} {h.mean():.4f} [{h_ci[0]:.4f}, {h_ci[1]:.4f}]   "
          f"{s.mean():.4f} [{s_ci[0]:.4f}, {s_ci[1]:.4f}]   "
          f"{v.mean():.4f} [{v_ci[0]:.4f}, {v_ci[1]:.4f}]")

# 2. Testes pareados Híbrido vs SQL Puro
print("\n2. WILCOXON SIGNED-RANK: Híbrido vs. SQL Puro")
print("-" * 80)
print(f"{'Métrica':<10} {'Δ média':<12} {'W-stat':<12} {'p-valor':<12} {'Sig. (α=0.05)':<15}")
print("-" * 80)
for m in METRICS:
    h, s, _ = get_arrays(m)
    diff = h - s
    w, p = wilcoxon_test(h, s)
    sig = "SIM ***" if p < 0.001 else ("SIM **" if p < 0.01 else ("SIM *" if p < 0.05 else "NÃO"))
    print(f"{METRIC_LABELS[m]:<10} {diff.mean():>+.4f}     {w:>10.1f}  {p:>10.6f}  {sig}")

# 3. Testes pareados Híbrido vs Vetorial Puro
print("\n3. WILCOXON SIGNED-RANK: Híbrido vs. Vetorial Puro")
print("-" * 80)
print(f"{'Métrica':<10} {'Δ média':<12} {'W-stat':<12} {'p-valor':<12} {'Sig. (α=0.05)':<15}")
print("-" * 80)
for m in METRICS:
    h, _, v = get_arrays(m)
    diff = h - v
    w, p = wilcoxon_test(h, v)
    sig = "SIM ***" if p < 0.001 else ("SIM **" if p < 0.01 else ("SIM *" if p < 0.05 else "NÃO"))
    print(f"{METRIC_LABELS[m]:<10} {diff.mean():>+.4f}     {w:>10.1f}  {p:>10.6f}  {sig}")

# 4. Paired t-test (complementar ao Wilcoxon)
print("\n4. PAIRED T-TEST: Híbrido vs. SQL Puro (n=120)")
print("-" * 80)
print(f"{'Métrica':<10} {'Diff media':<12} {'t-stat':<12} {'p-valor':<12} {'Sig. (a=0.05)':<15}")
print("-" * 80)
for m in METRICS:
    h, s, _ = get_arrays(m)
    diff = h - s
    t, p = paired_ttest(h, s)
    sig = "SIM ***" if p < 0.001 else ("SIM **" if p < 0.01 else ("SIM *" if p < 0.05 else "NAO"))
    print(f"{METRIC_LABELS[m]:<10} {diff.mean():>+.4f}     {t:>10.4f}  {p:>10.6f}  {sig}")

print("\n5. PAIRED T-TEST: Híbrido vs. Vetorial Puro (n=120)")
print("-" * 80)
print(f"{'Métrica':<10} {'Diff media':<12} {'t-stat':<12} {'p-valor':<12} {'Sig. (a=0.05)':<15}")
print("-" * 80)
for m in METRICS:
    h, _, v = get_arrays(m)
    diff = h - v
    t, p = paired_ttest(h, v)
    sig = "SIM ***" if p < 0.001 else ("SIM **" if p < 0.01 else ("SIM *" if p < 0.05 else "NAO"))
    print(f"{METRIC_LABELS[m]:<10} {diff.mean():>+.4f}     {t:>10.4f}  {p:>10.6f}  {sig}")

# 6. Análise por tipo de consulta (Tipo B — cenário com maior diferenciação)
print("\n6. ANALISE POR TIPO: Hibrido vs. SQL Puro (paired t-test)")
print("-" * 80)
for tipo in ["A", "B", "C", "D"]:
    tipo_ids = [qid for qid in query_ids if qid.startswith(tipo)]
    print(f"\n  Tipo {tipo} (n={len(tipo_ids)})")
    print(f"  {'Metrica':<10} {'Diff media':<12} {'t-stat':<12} {'p-valor':<12} {'Sig.':<10}")
    for m in METRICS:
        h_t = np.array([hibrido[qid][m] for qid in tipo_ids])
        s_t = np.array([sql_puro[qid][m] for qid in tipo_ids])
        diff = h_t - s_t
        t, p = paired_ttest(h_t, s_t)
        sig = "SIM *" if p < 0.05 else "NAO"
        print(f"  {METRIC_LABELS[m]:<10} {diff.mean():>+.4f}     {t:>10.4f}  {p:>10.6f}  {sig}")

# 7. Contagem de pares não-empatados (para entender comportamento do Wilcoxon)
print("\n7. PARES NAO-EMPATADOS (Hibrido vs SQL Puro, por tipo)")
print("-" * 80)
for tipo in ["A", "B", "C", "D"]:
    tipo_ids = [qid for qid in query_ids if qid.startswith(tipo)]
    for m in ["ndcg_at_5", "precision_at_5"]:
        h_t = np.array([hibrido[qid][m] for qid in tipo_ids])
        s_t = np.array([sql_puro[qid][m] for qid in tipo_ids])
        diff = h_t - s_t
        n_nonzero = np.sum(diff != 0)
        n_positive = np.sum(diff > 0)
        n_negative = np.sum(diff < 0)
        print(f"  Tipo {tipo} {METRIC_LABELS[m]:<8}: {n_nonzero:>2} pares diferentes "
              f"({n_positive} hibrido>sql, {n_negative} sql>hibrido)")

# 5. Resumo para o artigo
print("\n" + "=" * 80)
print("  RESUMO PARA O ARTIGO")
print("=" * 80)
print("""
Os testes acima podem ser reportados no artigo da seguinte forma:
- Na seção de Resultados ou Discussão, após apresentar os valores agregados
- Formato sugerido: "Teste pareado de Wilcoxon (n=120, α=0.05)"
- Reportar p-valores e indicar significância
- Os intervalos de confiança bootstrap (95%) podem ser adicionados às tabelas
""")
