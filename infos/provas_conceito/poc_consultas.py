#!/usr/bin/env python3
"""Prova de Conceito: Consultas reais sobre emendas parlamentares."""
import json
import sqlite3
import numpy as np
import time

# Carregar embeddings e dados
embeddings = np.load('provas_conceito/embeddings_reais/embeddings_7479.npy')
with open('provas_conceito/embeddings_reais/codigos_map.json', 'r') as f:
    codigos = json.load(f)
with open('provas_conceito/embeddings_reais/textos.json', 'r', encoding='utf-8') as f:
    textos = json.load(f)

conn = sqlite3.connect('dados/processados/emendas_poc.db')
cur = conn.cursor()

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def busca_semantica(consulta, top_k=5):
    start = time.time()
    q_emb = model.encode([consulta])[0]
    sims = np.array([cosine_similarity(q_emb, e) for e in embeddings])
    top_idx = np.argsort(sims)[-top_k:][::-1]
    elapsed = time.time() - start
    results = []
    for idx in top_idx:
        results.append({
            'codigo': codigos[idx],
            'similaridade': round(float(sims[idx]), 4),
            'texto': textos[idx][:200]
        })
    return results, elapsed

def busca_sql(consulta_sql):
    start = time.time()
    cur.execute(consulta_sql)
    results = cur.fetchall()
    elapsed = time.time() - start
    return results, elapsed

def busca_hibrida(consulta_nl, filtros_sql, top_k=5):
    start = time.time()
    cur.execute(filtros_sql)
    sql_results = cur.fetchall()
    codigo_set = set(r[0] for r in sql_results)
    filtered_indices = [i for i, c in enumerate(codigos) if c in codigo_set]
    if not filtered_indices:
        return [], time.time() - start
    q_emb = model.encode([consulta_nl])[0]
    filtered_embeddings = embeddings[filtered_indices]
    sims = np.array([cosine_similarity(q_emb, e) for e in filtered_embeddings])
    top_local_idx = np.argsort(sims)[-top_k:][::-1]
    elapsed = time.time() - start
    results = []
    for li in top_local_idx:
        gi = filtered_indices[li]
        results.append({
            'codigo': codigos[gi],
            'similaridade': round(float(sims[li]), 4),
            'texto': textos[gi][:200]
        })
    return results, elapsed

all_results = {}

# TIPO A: SQL puro
print("TIPO A: SQL puro")
sql_a1 = "SELECT nome_autor, funcao, COUNT(*), printf('R$ %,.2f', SUM(valor_empenhado)), printf('R$ %,.2f', SUM(valor_pago)) FROM emendas WHERE nome_autor = 'ROBERTO DUARTE' AND funcao LIKE '%Sa_de%' GROUP BY funcao"
r1, t1 = busca_sql(sql_a1)
print(f"  Q1: ROBERTO DUARTE saude -> {r1} ({t1*1000:.1f}ms)")

sql_a2 = "SELECT nome_autor, COUNT(*), printf('R$ %,.2f', SUM(valor_empenhado)) FROM emendas WHERE funcao LIKE '%Educa%' AND ano = 2024 GROUP BY nome_autor ORDER BY SUM(valor_empenhado) DESC LIMIT 5"
r2, t2 = busca_sql(sql_a2)
print(f"  Q2: Top 5 educacao 2024 ({t2*1000:.1f}ms)")
for row in r2:
    print(f"    {row[0]}: {row[1]} emendas, {row[2]}")

# TIPO B: Semantica
print("\nTIPO B: Semantica")
rb1, tb1 = busca_semantica("emendas para hospitais e postos de saude")
print(f"  Q3: hospitais saude ({tb1*1000:.1f}ms)")
for r in rb1[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

rb2, tb2 = busca_semantica("investimento em seguranca publica e policiamento")
print(f"  Q4: seguranca publica ({tb2*1000:.1f}ms)")
for r in rb2[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

# TIPO C: Hibrida
print("\nTIPO C: Hibrida")
rc1, tc1 = busca_hibrida("programas sociais assistencia", "SELECT codigo FROM emendas WHERE nome_autor = 'MARA ROCHA'")
print(f"  Q5: MARA ROCHA programas sociais ({tc1*1000:.1f}ms)")
for r in rc1[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

rc2, tc2 = busca_hibrida("armamento militar defesa exercito", "SELECT codigo FROM emendas WHERE ano = 2023 AND funcao LIKE '%Defesa%'")
print(f"  Q6: defesa 2023 ({tc2*1000:.1f}ms)")
for r in rc2[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

# Avaliar relevancia
print("\n--- AVALIACAO DE RELEVANCIA ---")

# Para busca semantica "hospitais e postos de saude"
# Verificar quantos dos top-5 sao efetivamente de Saude
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" + ",".join(f"'{r['codigo']}'" for r in rb1) + ")")
funcoes_b1 = [row[0] for row in cur.fetchall()]
saude_hit = sum(1 for f in funcoes_b1 if 'Sa' in f)
print(f"Busca 'hospitais saude': {saude_hit}/5 resultados relevantes (funcao Saude)")

# Para busca semantica "seguranca publica"
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" + ",".join(f"'{r['codigo']}'" for r in rb2) + ")")
funcoes_b2 = [row[0] for row in cur.fetchall()]
seg_hit = sum(1 for f in funcoes_b2 if 'Seguran' in f)
print(f"Busca 'seguranca publica': {seg_hit}/5 resultados relevantes (funcao Seguranca)")

# Para hibrida "MARA ROCHA programas sociais"
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" + ",".join(f"'{r['codigo']}'" for r in rc1) + ")")
funcoes_c1 = [row[0] for row in cur.fetchall()]
social_hit = sum(1 for f in funcoes_c1 if any(x in f for x in ['Assist', 'Direito', 'Social']))
print(f"Hibrida 'MARA ROCHA sociais': {social_hit}/5 resultados relevantes")

# Resumo final
print("\n=== METRICAS FINAIS ===")
print(f"SQL puro:     media {(t1+t2)*500:.1f}ms")
print(f"Semantica:    media {(tb1+tb2)*500:.1f}ms")
print(f"Hibrida:      media {(tc1+tc2)*500:.1f}ms")
print(f"Precision@5 semantica saude: {saude_hit/5*100:.0f}%")
print(f"Precision@5 semantica seguranca: {seg_hit/5*100:.0f}%")
print(f"Precision@5 hibrida social: {social_hit/5*100:.0f}%")

# Salvar resultados completos
final = {
    "total_registros": 7479,
    "modelo_embeddings": "all-MiniLM-L6-v2",
    "dimensoes": 384,
    "tempo_geracao_embeddings_s": 32.73,
    "metricas": {
        "sql_puro_media_ms": round((t1+t2)*500, 1),
        "semantica_media_ms": round((tb1+tb2)*500, 1),
        "hibrida_media_ms": round((tc1+tc2)*500, 1),
        "precision_at_5_saude": round(saude_hit/5, 2),
        "precision_at_5_seguranca": round(seg_hit/5, 2),
        "precision_at_5_social": round(social_hit/5 if rc1 else 0, 2),
    },
    "consultas_exemplo": {
        "tipo_a_roberto_duarte_saude": [{"nome": r[0], "funcao": r[1], "qtd": r[2], "empenhado": r[3], "pago": r[4]} for r in r1],
        "tipo_a_top5_educacao_2024": [{"nome": r[0], "qtd": r[1], "total": r[2]} for r in r2],
    }
}

with open("provas_conceito/resultados_poc_real.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print("\nSalvo: provas_conceito/resultados_poc_real.json")
conn.close()
