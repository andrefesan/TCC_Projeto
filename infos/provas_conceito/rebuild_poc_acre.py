#!/usr/bin/env python3
"""
Reconstrói a PoC usando EXCLUSIVAMENTE o universo de emendas do Acre (609 registros).
Modelo de embeddings: multilingual-e5-small (mesmo da produção).
"""
import json
import sqlite3
import numpy as np
import time
import os
import platform
import subprocess

# ============================================================
# ETAPA 0: Coletar especificações da máquina
# ============================================================
print("=" * 60)
print("ETAPA 0: Coletando especificações do ambiente")
print("=" * 60)

def get_hardware_info():
    """Coleta informações de hardware para reprodutibilidade."""
    info = {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "plataforma": platform.platform(),
        "python_versao": platform.python_version(),
        "arquitetura": platform.machine(),
    }
    # CPU
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
            for line in cpuinfo.split("\n"):
                if "model name" in line:
                    info["processador"] = line.split(":")[1].strip()
                    break
            info["cpu_nucleos_logicos"] = os.cpu_count()
        elif platform.system() == "Windows":
            info["processador"] = platform.processor()
            info["cpu_nucleos_logicos"] = os.cpu_count()
        elif platform.system() == "Darwin":
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                    capture_output=True, text=True)
            info["processador"] = result.stdout.strip()
            info["cpu_nucleos_logicos"] = os.cpu_count()
    except Exception:
        info["processador"] = platform.processor() or "não detectado"
        info["cpu_nucleos_logicos"] = os.cpu_count()
    # RAM
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        kb = int(line.split()[1])
                        info["ram_total_gb"] = round(kb / 1024 / 1024, 1)
                        break
        elif platform.system() == "Darwin":
            result = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                    capture_output=True, text=True)
            info["ram_total_gb"] = round(int(result.stdout.strip()) / 1024**3, 1)
        elif platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", c_ulonglong),
                            ("ullAvailPhys", c_ulonglong),
                            ("ullTotalPageFile", c_ulonglong),
                            ("ullAvailPageFile", c_ulonglong),
                            ("ullTotalVirtual", c_ulonglong),
                            ("ullAvailVirtual", c_ulonglong),
                            ("ullAvailExtendedVirtual", c_ulonglong)]
            memstat = MEMORYSTATUSEX()
            memstat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memstat))
            info["ram_total_gb"] = round(memstat.ullTotalPhys / 1024**3, 1)
    except Exception:
        info["ram_total_gb"] = "não detectado"
    # GPU
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                                 "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            info["gpu"] = result.stdout.strip()
        else:
            info["gpu"] = "Nenhuma GPU NVIDIA detectada"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        info["gpu"] = "nvidia-smi não disponível (sem GPU dedicada ou driver não instalado)"

    return info

hw_info = get_hardware_info()
print(f"  SO: {hw_info['sistema_operacional']}")
print(f"  CPU: {hw_info.get('processador', '?')}")
print(f"  Núcleos: {hw_info.get('cpu_nucleos_logicos', '?')}")
print(f"  RAM: {hw_info.get('ram_total_gb', '?')} GB")
print(f"  GPU: {hw_info.get('gpu', '?')}")
print(f"  Python: {hw_info['python_versao']}")

# ============================================================
# ETAPA 1: Criar banco SQLite com dados do Acre
# ============================================================
print("=" * 60)
print("ETAPA 1: Criando banco SQLite com emendas do Acre")
print("=" * 60)

ACRE_JSON = "infos/dados/emendas_reais/emendas_acre_completo.json"
DB_PATH = "infos/provas_conceito/emendas_acre_poc.db"
EMBEDDINGS_DIR = "infos/provas_conceito/embeddings_acre"

with open(ACRE_JSON, "r", encoding="utf-8") as f:
    emendas_acre = json.load(f)

print(f"Total de emendas carregadas: {len(emendas_acre)}")

# Limpar DB anterior se existir
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE emendas (
        codigo TEXT PRIMARY KEY,
        ano INTEGER,
        tipo_emenda TEXT,
        nome_autor TEXT,
        localidade TEXT,
        funcao TEXT,
        subfuncao TEXT,
        valor_empenhado REAL DEFAULT 0,
        valor_liquidado REAL DEFAULT 0,
        valor_pago REAL DEFAULT 0
    )
""")

def parse_valor(v):
    """Converte valor monetário (str ou num) para float."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).replace(".", "").replace(",", "."))

inseridos = 0
for e in emendas_acre:
    try:
        cur.execute("""
            INSERT OR IGNORE INTO emendas
            (codigo, ano, tipo_emenda, nome_autor, localidade, funcao, subfuncao,
             valor_empenhado, valor_liquidado, valor_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e.get("codigoEmenda", ""),
            e.get("ano", 0),
            e.get("tipoEmenda", ""),
            (e.get("nomeAutor") or e.get("autor", "")).strip().upper(),
            e.get("localidadeDoGasto", ""),
            e.get("funcao", ""),
            e.get("subfuncao", ""),
            parse_valor(e.get("valorEmpenhado")),
            parse_valor(e.get("valorLiquidado")),
            parse_valor(e.get("valorPago")),
        ))
        inseridos += 1
    except Exception as ex:
        print(f"  ERRO ao inserir {e.get('codigoEmenda')}: {ex}")

conn.commit()
print(f"Emendas inseridas no SQLite: {inseridos}")

# Verificação rápida
cur.execute("SELECT COUNT(*) FROM emendas")
print(f"Verificação: {cur.fetchone()[0]} registros no banco")
cur.execute("SELECT DISTINCT nome_autor FROM emendas ORDER BY nome_autor")
autores = [r[0] for r in cur.fetchall()]
print(f"Autores distintos: {len(autores)}")
for a in autores:
    print(f"  - {a}")
cur.execute("SELECT ano, COUNT(*), printf('R$ %,.2f', SUM(valor_empenhado)) FROM emendas GROUP BY ano ORDER BY ano")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} emendas, {r[2]} empenhado")

# ============================================================
# ETAPA 2: Gerar embeddings com multilingual-e5-small
# ============================================================
print("\n" + "=" * 60)
print("ETAPA 2: Gerando embeddings com multilingual-e5-small")
print("=" * 60)

from sentence_transformers import SentenceTransformer

# IMPORTANTE: usar o mesmo modelo da produção
MODEL_NAME = "intfloat/multilingual-e5-small"
model = SentenceTransformer(MODEL_NAME)

# Compor textos representativos (mesmo padrão do EmbeddingGenerator da produção)
cur.execute("""
    SELECT codigo, nome_autor, funcao, subfuncao, localidade, ano
    FROM emendas ORDER BY codigo
""")
rows = cur.fetchall()

codigos = []
textos = []
for r in rows:
    codigo, autor, funcao, subfuncao, localidade, ano = r
    texto = f"{autor} | {funcao} | {subfuncao} | {localidade} | Ano: {ano}"
    codigos.append(codigo)
    textos.append(texto)

print(f"Gerando embeddings para {len(textos)} registros...")
t_start = time.time()
embeddings = model.encode(textos, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
t_embed = time.time() - t_start
print(f"Embeddings gerados em {t_embed:.2f}s ({len(textos)/t_embed:.1f} emb/s)")
print(f"Shape: {embeddings.shape}")

# Salvar
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
np.save(f"{EMBEDDINGS_DIR}/embeddings_acre_{len(textos)}.npy", embeddings)
with open(f"{EMBEDDINGS_DIR}/codigos_map.json", "w") as f:
    json.dump(codigos, f)
with open(f"{EMBEDDINGS_DIR}/textos.json", "w", encoding="utf-8") as f:
    json.dump(textos, f, ensure_ascii=False)
with open(f"{EMBEDDINGS_DIR}/metadata.json", "w", encoding="utf-8") as f:
    json.dump({
        "modelo": MODEL_NAME,
        "dimensoes": int(embeddings.shape[1]),
        "total_registros": len(textos),
        "tempo_segundos": round(t_embed, 2),
        "taxa_emb_por_segundo": round(len(textos) / t_embed, 1),
        "fonte": "emendas_acre_completo.json (Portal da Transparência - API REST)",
        "escopo": "Universo completo de emendas parlamentares do estado do Acre",
        "anos": [2020, 2021, 2022, 2023, 2024],
        "data_geracao": time.strftime("%Y-%m-%d"),
    }, f, ensure_ascii=False, indent=2)

print(f"Arquivos salvos em {EMBEDDINGS_DIR}/")

# ============================================================
# ETAPA 3: Executar consultas da PoC
# ============================================================
print("\n" + "=" * 60)
print("ETAPA 3: Executando consultas sobre dados do Acre")
print("=" * 60)

def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def busca_sql(sql_query):
    start = time.time()
    cur.execute(sql_query)
    results = cur.fetchall()
    elapsed = time.time() - start
    return results, elapsed

def busca_semantica(consulta, top_k=5):
    start = time.time()
    q_emb = model.encode([consulta])[0]
    sims = np.array([cosine_similarity(q_emb, e) for e in embeddings])
    top_idx = np.argsort(sims)[-top_k:][::-1]
    elapsed = time.time() - start
    results = []
    for idx in top_idx:
        results.append({
            "codigo": codigos[idx],
            "similaridade": round(float(sims[idx]), 4),
            "texto": textos[idx][:200]
        })
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
    filtered_embs = embeddings[filtered_indices]
    sims = np.array([cosine_similarity(q_emb, e) for e in filtered_embs])
    top_local_idx = np.argsort(sims)[-top_k:][::-1]
    elapsed = time.time() - start
    results = []
    for li in top_local_idx:
        gi = filtered_indices[li]
        results.append({
            "codigo": codigos[gi],
            "similaridade": round(float(sims[li]), 4),
            "texto": textos[gi][:200]
        })
    return results, elapsed

# --- CONSULTAS ---

# Executar cada consulta N vezes para obter média e desvio padrão
N_RUNS = 10
latencias = {"sql": [], "semantica": [], "hibrida": []}

print("\n--- TIPO A: SQL puro ---")

sql_a1 = """
    SELECT nome_autor, funcao, COUNT(*),
           printf('R$ %,.2f', SUM(valor_empenhado)),
           printf('R$ %,.2f', SUM(valor_pago))
    FROM emendas
    WHERE nome_autor = 'ROBERTO DUARTE' AND funcao LIKE '%Sa_de%'
    GROUP BY funcao
"""
for _ in range(N_RUNS):
    _, t = busca_sql(sql_a1)
    latencias["sql"].append(t * 1000)
r1, t1 = busca_sql(sql_a1)
print(f"  Q1: ROBERTO DUARTE + saúde -> {r1}")

sql_a2 = """
    SELECT nome_autor, COUNT(*), printf('R$ %,.2f', SUM(valor_empenhado))
    FROM emendas
    WHERE funcao LIKE '%Educa%' AND ano = 2024
    GROUP BY nome_autor
    ORDER BY SUM(valor_empenhado) DESC
    LIMIT 5
"""
for _ in range(N_RUNS):
    _, t = busca_sql(sql_a2)
    latencias["sql"].append(t * 1000)
r2, t2 = busca_sql(sql_a2)
print(f"  Q2: Top 5 educação Acre 2024:")
for row in r2:
    print(f"    {row[0]}: {row[1]} emendas, {row[2]}")

sql_a3 = """
    SELECT nome_autor, COUNT(*), printf('R$ %,.2f', SUM(valor_empenhado))
    FROM emendas
    WHERE ano BETWEEN 2020 AND 2024
    GROUP BY nome_autor
    ORDER BY SUM(valor_empenhado) DESC
    LIMIT 5
"""
for _ in range(N_RUNS):
    _, t = busca_sql(sql_a3)
    latencias["sql"].append(t * 1000)
r3, _ = busca_sql(sql_a3)
print(f"  Q3: Top 5 parlamentares Acre (total 2020-2024):")
for row in r3:
    print(f"    {row[0]}: {row[1]} emendas, {row[2]}")

print("\n--- TIPO B: Busca semântica ---")

for _ in range(N_RUNS):
    _, t = busca_semantica("emendas para hospitais e postos de saúde")
    latencias["semantica"].append(t * 1000)
rb1, tb1 = busca_semantica("emendas para hospitais e postos de saúde")
print(f"  Q4: hospitais e saúde ({tb1*1000:.1f}ms)")
for r in rb1[:5]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

for _ in range(N_RUNS):
    _, t = busca_semantica("investimento em segurança pública e policiamento")
    latencias["semantica"].append(t * 1000)
rb2, tb2 = busca_semantica("investimento em segurança pública e policiamento")
print(f"  Q5: segurança pública ({tb2*1000:.1f}ms)")
for r in rb2[:5]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

for _ in range(N_RUNS):
    _, t = busca_semantica("infraestrutura urbana saneamento e água")
    latencias["semantica"].append(t * 1000)
rb3, tb3 = busca_semantica("infraestrutura urbana saneamento e água")
print(f"  Q6: saneamento ({tb3*1000:.1f}ms)")
for r in rb3[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

print("\n--- TIPO C: Busca híbrida ---")

for _ in range(N_RUNS):
    _, t = busca_hibrida(
        "programas sociais e assistência",
        "SELECT codigo FROM emendas WHERE nome_autor = 'MARA ROCHA'"
    )
    latencias["hibrida"].append(t * 1000)
rc1, tc1 = busca_hibrida(
    "programas sociais e assistência",
    "SELECT codigo FROM emendas WHERE nome_autor = 'MARA ROCHA'"
)
print(f"  Q7: MARA ROCHA + programas sociais ({tc1*1000:.1f}ms)")
for r in rc1[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

for _ in range(N_RUNS):
    _, t = busca_hibrida(
        "educação ensino escola universidade",
        "SELECT codigo FROM emendas WHERE nome_autor = 'ALAN RICK'"
    )
    latencias["hibrida"].append(t * 1000)
rc2, tc2 = busca_hibrida(
    "educação ensino escola universidade",
    "SELECT codigo FROM emendas WHERE nome_autor = 'ALAN RICK'"
)
print(f"  Q8: ALAN RICK + educação ({tc2*1000:.1f}ms)")
for r in rc2[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

for _ in range(N_RUNS):
    _, t = busca_hibrida(
        "saúde hospitais atenção básica",
        "SELECT codigo FROM emendas WHERE ano = 2024"
    )
    latencias["hibrida"].append(t * 1000)
rc3, tc3 = busca_hibrida(
    "saúde hospitais atenção básica",
    "SELECT codigo FROM emendas WHERE ano = 2024"
)
print(f"  Q9: Saúde 2024 híbrida ({tc3*1000:.1f}ms)")
for r in rc3[:3]:
    print(f"    [{r['similaridade']}] {r['texto'][:120]}")

# ============================================================
# ETAPA 4: Avaliação de relevância (Precision@5)
# ============================================================
print("\n" + "=" * 60)
print("ETAPA 4: Avaliação de relevância")
print("=" * 60)

# Semântica: "hospitais e saúde" -> resultados devem ter função Saúde
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" +
            ",".join(f"'{r['codigo']}'" for r in rb1) + ")")
funcoes_b1 = [row[0] for row in cur.fetchall()]
saude_hit = sum(1 for f in funcoes_b1 if "Sa" in f)
print(f"P@5 semântica 'hospitais saúde': {saude_hit}/5 = {saude_hit/5:.2f}")

# Semântica: "segurança pública" -> resultados devem ter função Segurança
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" +
            ",".join(f"'{r['codigo']}'" for r in rb2) + ")")
funcoes_b2 = [row[0] for row in cur.fetchall()]
seg_hit = sum(1 for f in funcoes_b2 if "Seguran" in f or "Defesa" in f)
print(f"P@5 semântica 'segurança': {seg_hit}/5 = {seg_hit/5:.2f}")

# Semântica: "saneamento" -> resultados devem ter função Saneamento ou Urbanismo
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" +
            ",".join(f"'{r['codigo']}'" for r in rb3) + ")")
funcoes_b3 = [row[0] for row in cur.fetchall()]
san_hit = sum(1 for f in funcoes_b3 if any(x in f for x in ["Saneamento", "Urban", "Habitação"]))
print(f"P@5 semântica 'saneamento': {san_hit}/5 = {san_hit/5:.2f}")

# Híbrida: "MARA ROCHA sociais" -> Assistência Social / Direitos
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" +
            ",".join(f"'{r['codigo']}'" for r in rc1) + ")")
funcoes_c1 = [row[0] for row in cur.fetchall()]
social_hit = sum(1 for f in funcoes_c1 if any(x in f for x in ["Assist", "Direito", "Social"]))
rc1_len = min(len(rc1), 5)
print(f"P@5 híbrida 'MARA ROCHA sociais': {social_hit}/{rc1_len} = {social_hit/max(rc1_len,1):.2f}")

# Híbrida: "ALAN RICK educação" -> Educação
cur.execute("SELECT funcao FROM emendas WHERE codigo IN (" +
            ",".join(f"'{r['codigo']}'" for r in rc2) + ")")
funcoes_c2 = [row[0] for row in cur.fetchall()]
edu_hit = sum(1 for f in funcoes_c2 if "Educa" in f)
rc2_len = min(len(rc2), 5)
print(f"P@5 híbrida 'ALAN RICK educação': {edu_hit}/{rc2_len} = {edu_hit/max(rc2_len,1):.2f}")

# ============================================================
# ETAPA 5: Estatísticas de latência (média + desvio padrão)
# ============================================================
print("\n" + "=" * 60)
print("ETAPA 5: Estatísticas de latência")
print("=" * 60)

for modo, vals in latencias.items():
    arr = np.array(vals)
    print(f"{modo:12s}: média={arr.mean():.2f}ms  dp={arr.std():.2f}ms  "
          f"min={arr.min():.2f}ms  max={arr.max():.2f}ms  (n={len(vals)})")

# ============================================================
# ETAPA 6: Salvar resultados
# ============================================================
print("\n" + "=" * 60)
print("ETAPA 6: Salvando resultados")
print("=" * 60)

resultados = {
    "escopo": "Universo completo de emendas parlamentares do estado do Acre (2020-2024)",
    "total_registros": len(emendas_acre),
    "ambiente": hw_info,
    "modelo_embeddings": MODEL_NAME,
    "dimensoes": int(embeddings.shape[1]),
    "tempo_geracao_embeddings_s": round(t_embed, 2),
    "latencia": {
        modo: {
            "media_ms": round(float(np.mean(vals)), 2),
            "desvio_padrao_ms": round(float(np.std(vals)), 2),
            "min_ms": round(float(np.min(vals)), 2),
            "max_ms": round(float(np.max(vals)), 2),
            "n_execucoes": len(vals),
        }
        for modo, vals in latencias.items()
    },
    "precision_at_5": {
        "semantica_saude": round(saude_hit / 5, 2),
        "semantica_seguranca": round(seg_hit / 5, 2),
        "semantica_saneamento": round(san_hit / 5, 2),
        "hibrida_mara_rocha_social": round(social_hit / max(rc1_len, 1), 2),
        "hibrida_alan_rick_educacao": round(edu_hit / max(rc2_len, 1), 2),
    },
    "consultas": {
        "roberto_duarte_saude": [
            {"nome": r[0], "funcao": r[1], "qtd": r[2], "empenhado": r[3], "pago": r[4]}
            for r in r1
        ],
        "top5_educacao_acre_2024": [
            {"nome": r[0], "qtd": r[1], "total": r[2]}
            for r in r2
        ],
        "top5_parlamentares_acre_total": [
            {"nome": r[0], "qtd": r[1], "total": r[2]}
            for r in r3
        ],
    },
    "data_execucao": time.strftime("%Y-%m-%dT%H:%M:%S"),
}

output_path = "infos/provas_conceito/resultados_poc_acre.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"Resultados salvos em: {output_path}")
print("\nPoC do Acre concluída com sucesso.")

conn.close()
