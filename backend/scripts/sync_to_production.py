"""Sincroniza dados do SQLite local para o PostgreSQL de produção (Supabase).

Uso:
    python scripts/sync_to_production.py                # sync completo
    python scripts/sync_to_production.py --dry-run      # apenas mostra o que faria
    python scripts/sync_to_production.py --tabela emendas  # sync de uma tabela específica
"""
import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
SQLITE_PATH = Path(__file__).parent.parent / "data" / "transparencia_local.db"

PG_CONFIG = dict(
    host=os.environ["PG_HOST"],
    port=int(os.environ.get("PG_PORT", 5432)),
    dbname=os.environ.get("PG_DBNAME", "postgres"),
    user=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    sslmode=os.environ.get("PG_SSLMODE", "require"),
)

BATCH_SIZE = 1000


def pg_connect():
    return psycopg2.connect(**PG_CONFIG)


def sqlite_connect():
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Fase 0: Ajustar schema de produção (colunas faltantes em documentos_emenda)
# ---------------------------------------------------------------------------
COLUNAS_EXTRAS_DOC = [
    ("funcao", "VARCHAR(200)"),
    ("subfuncao", "VARCHAR(200)"),
    ("programa", "VARCHAR(300)"),
    ("acao", "VARCHAR(300)"),
    ("localizador_gasto", "VARCHAR(200)"),
    ("especie", "VARCHAR(200)"),
    ("categoria", "VARCHAR(200)"),
    ("grupo_despesa", "VARCHAR(200)"),
    ("elemento_despesa", "VARCHAR(200)"),
    ("modalidade", "VARCHAR(300)"),
    ("orgao", "VARCHAR(300)"),
    ("orgao_superior", "VARCHAR(300)"),
    ("unidade_gestora", "VARCHAR(300)"),
    ("unidade_orcamentaria", "VARCHAR(300)"),
    ("favorecido_nome", "VARCHAR(300)"),
    ("favorecido_cpf_cnpj", "VARCHAR(20)"),
    ("favorecido_uf", "VARCHAR(20)"),
    ("numero_processo", "VARCHAR(100)"),
    ("plano_orcamentario", "VARCHAR(300)"),
    ("detalhes_coletados", "INTEGER DEFAULT 0"),
    ("embedding", "vector(384)"),
]


COLUNAS_ALARGAR = [
    ("orgaos", "codigo", "VARCHAR(100)"),
    ("orgaos", "nome", "VARCHAR(300)"),
    ("orgaos", "orgao_superior_codigo", "VARCHAR(100)"),
    ("unidades_gestoras", "codigo", "VARCHAR(100)"),
    ("unidades_gestoras", "nome", "VARCHAR(300)"),
    ("unidades_gestoras", "orgao_codigo", "VARCHAR(100)"),
    ("acoes", "nome", "VARCHAR(300)"),
    ("programas", "nome", "VARCHAR(300)"),
]


COLUNAS_EXTRAS_EMENDA = [
    ("valor_resto_inscrito", "NUMERIC(15,2) DEFAULT 0"),
    ("valor_resto_cancelado", "NUMERIC(15,2) DEFAULT 0"),
    ("valor_resto_pago", "NUMERIC(15,2) DEFAULT 0"),
    ("numero_emenda", "VARCHAR(20)"),
]


def ajustar_schema(pg_cur, dry_run: bool):
    """Adiciona colunas faltantes e alarga colunas estreitas em produção."""
    # 1a. Colunas faltantes em documentos_emenda
    pg_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'documentos_emenda'
    """)
    colunas_existentes = {r[0] for r in pg_cur.fetchall()}

    for col_name, col_type in COLUNAS_EXTRAS_DOC:
        if col_name not in colunas_existentes:
            sql = f"ALTER TABLE documentos_emenda ADD COLUMN {col_name} {col_type}"
            if dry_run:
                log(f"  [DRY-RUN] {sql}")
            else:
                pg_cur.execute(sql)
                log(f"  + coluna documentos_emenda.{col_name} adicionada")

    # 1b. Colunas faltantes em emendas
    pg_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'emendas'
    """)
    colunas_emendas = {r[0] for r in pg_cur.fetchall()}

    for col_name, col_type in COLUNAS_EXTRAS_EMENDA:
        if col_name not in colunas_emendas:
            sql = f"ALTER TABLE emendas ADD COLUMN {col_name} {col_type}"
            if dry_run:
                log(f"  [DRY-RUN] {sql}")
            else:
                pg_cur.execute(sql)
                log(f"  + coluna emendas.{col_name} adicionada")

    # 2. Alargar colunas que podem truncar dados
    for tabela, coluna, novo_tipo in COLUNAS_ALARGAR:
        sql = f"ALTER TABLE {tabela} ALTER COLUMN {coluna} TYPE {novo_tipo}"
        if dry_run:
            log(f"  [DRY-RUN] {sql}")
        else:
            try:
                pg_cur.execute(sql)
                log(f"  ~ {tabela}.{coluna} alargado para {novo_tipo}")
            except Exception:
                pass  # Já está no tipo correto

    log("Schema ajustado.")


# ---------------------------------------------------------------------------
# Helpers genéricos
# ---------------------------------------------------------------------------
def contar(pg_cur, tabela: str) -> int:
    pg_cur.execute(f"SELECT COUNT(*) FROM {tabela}")
    return pg_cur.fetchone()[0]


def get_existing_keys(pg_cur, tabela: str, key_col: str) -> set:
    """Retorna set de chaves já existentes em produção."""
    pg_cur.execute(f"SELECT {key_col} FROM {tabela}")
    return {r[0] for r in pg_cur.fetchall()}


# ---------------------------------------------------------------------------
# Tabelas lookup (código/nome)
# ---------------------------------------------------------------------------
def sync_lookup(lite, pg_cur, tabela: str, cols: list[str], dry_run: bool):
    """Sincroniza uma tabela lookup simples."""
    existentes = contar(pg_cur, tabela)
    rows = lite.execute(f"SELECT {','.join(cols)} FROM {tabela}").fetchall()
    total = len(rows)
    novas = 0

    if existentes >= total:
        log(f"  {tabela}: {existentes} em prod >= {total} local — skip")
        return

    # Pega chaves existentes (primeira coluna = PK)
    keys_prod = get_existing_keys(pg_cur, tabela, cols[0])

    placeholders = ",".join(["%s"] * len(cols))
    col_str = ",".join(cols)
    sql = f"INSERT INTO {tabela} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    batch = []
    for row in rows:
        if row[cols[0]] in keys_prod:
            continue
        values = tuple(row[c] for c in cols)
        batch.append(values)
        novas += 1

        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql, batch)
            batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  {tabela}: +{novas} novas ({total} local, {existentes} prod)")


# ---------------------------------------------------------------------------
# Emendas
# ---------------------------------------------------------------------------
def sync_emendas(lite, pg_cur, dry_run: bool):
    """Sincroniza emendas — usa codigo_emenda como chave de dedup."""
    cols = [
        "codigo_emenda", "cod_autor", "nome_autor", "ano", "tipo_emenda",
        "funcao", "funcao_nome", "subfuncao", "subfuncao_nome",
        "programa", "acao", "localidade", "uf",
        "valor_empenhado", "valor_liquidado", "valor_pago",
        "valor_resto_inscrito", "valor_resto_cancelado", "valor_resto_pago",
        "numero_emenda",
        "descricao", "fonte",
    ]

    codigos_prod = get_existing_keys(pg_cur, "emendas", "codigo_emenda")
    rows = lite.execute(f"SELECT {','.join(cols)} FROM emendas").fetchall()

    sql_insert = f"""
        INSERT INTO emendas ({','.join(cols)})
        VALUES ({','.join(['%s'] * len(cols))})
        ON CONFLICT (codigo_emenda) DO NOTHING
    """

    sql_update_valores = """
        UPDATE emendas SET
            valor_empenhado = %s, valor_liquidado = %s, valor_pago = %s,
            valor_resto_inscrito = %s, valor_resto_cancelado = %s, valor_resto_pago = %s,
            numero_emenda = COALESCE(NULLIF(%s, ''), numero_emenda)
        WHERE codigo_emenda = %s
    """

    # Buscar valores atuais em produção para detectar divergências
    pg_cur.execute("""
        SELECT codigo_emenda, valor_empenhado, valor_liquidado, valor_pago,
               valor_resto_inscrito, valor_resto_cancelado, valor_resto_pago
        FROM emendas
    """)
    valores_prod = {}
    for r in pg_cur.fetchall():
        valores_prod[r[0]] = (
            float(r[1] or 0), float(r[2] or 0), float(r[3] or 0),
            float(r[4] or 0), float(r[5] or 0), float(r[6] or 0),
        )

    batch_insert = []
    batch_update = []
    novas = 0
    atualizadas = 0

    for row in rows:
        cod = row["codigo_emenda"]
        if cod not in codigos_prod:
            values = tuple(row[c] for c in cols)
            batch_insert.append(values)
            novas += 1
        else:
            # Verificar se valores locais são maiores (reconciliados)
            local_emp = float(row["valor_empenhado"] or 0)
            local_liq = float(row["valor_liquidado"] or 0)
            local_pag = float(row["valor_pago"] or 0)
            local_ri = float(row["valor_resto_inscrito"] or 0)
            local_rc = float(row["valor_resto_cancelado"] or 0)
            local_rp = float(row["valor_resto_pago"] or 0)
            local_num = row["numero_emenda"] or ""
            prod_emp, prod_liq, prod_pag, prod_ri, prod_rc, prod_rp = valores_prod.get(cod, (0, 0, 0, 0, 0, 0))

            if (local_emp > prod_emp or local_liq > prod_liq or local_pag > prod_pag
                    or local_ri > prod_ri or local_rc > prod_rc or local_rp > prod_rp
                    or local_num):
                batch_update.append((
                    max(local_emp, prod_emp),
                    max(local_liq, prod_liq),
                    max(local_pag, prod_pag),
                    max(local_ri, prod_ri),
                    max(local_rc, prod_rc),
                    max(local_rp, prod_rp),
                    local_num,
                    cod,
                ))
                atualizadas += 1

        if len(batch_insert) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql_insert, batch_insert)
                pg_cur.connection.commit()
                log(f"    emendas batch: {novas} inseridas até agora...")
            batch_insert = []

        if len(batch_update) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql_update_valores, batch_update)
                pg_cur.connection.commit()
                log(f"    emendas batch: {atualizadas} valores atualizados até agora...")
            batch_update = []

    if batch_insert and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql_insert, batch_insert)
    if batch_update and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql_update_valores, batch_update)

    log(f"  emendas: +{novas} novas, {atualizadas} valores atualizados ({len(rows)} local, {len(codigos_prod)} prod)")


# ---------------------------------------------------------------------------
# Documentos
# ---------------------------------------------------------------------------
def sync_documentos(lite, pg_cur, dry_run: bool):
    """Sincroniza documentos_emenda — mapeia emenda_id via codigo_emenda."""
    # Construir mapa local emenda_id -> codigo_emenda
    local_map = {}
    for row in lite.execute("SELECT id, codigo_emenda FROM emendas").fetchall():
        local_map[row["id"]] = row["codigo_emenda"]

    # Construir mapa produção codigo_emenda -> id
    pg_cur.execute("SELECT id, codigo_emenda FROM emendas")
    prod_map = {r[1]: r[0] for r in pg_cur.fetchall()}

    # Chaves já em produção
    codigos_doc_prod = get_existing_keys(pg_cur, "documentos_emenda", "codigo_documento")

    cols_read = [
        "emenda_id", "codigo_documento", "fase", "valor", "data_documento",
        "tipo_documento", "observacao",
        "funcao", "subfuncao", "programa", "acao", "localizador_gasto",
        "especie", "categoria", "grupo_despesa", "elemento_despesa",
        "modalidade", "orgao", "orgao_superior", "unidade_gestora",
        "unidade_orcamentaria", "favorecido_nome", "favorecido_cpf_cnpj",
        "favorecido_uf", "numero_processo", "plano_orcamentario",
        "detalhes_coletados",
    ]
    cols_write = [c if c != "emenda_id" else "emenda_id" for c in cols_read]

    sql = f"""
        INSERT INTO documentos_emenda ({','.join(cols_write)})
        VALUES ({','.join(['%s'] * len(cols_write))})
        ON CONFLICT (codigo_documento) DO UPDATE SET valor = EXCLUDED.valor
        WHERE documentos_emenda.valor IS NULL OR documentos_emenda.valor = 0
    """

    # Ler em blocos do SQLite para não estourar memória
    total_local = lite.execute("SELECT COUNT(*) FROM documentos_emenda").fetchone()[0]
    log(f"  documentos: {total_local} local, {len(codigos_doc_prod)} prod — lendo...")

    cursor_lite = lite.execute(
        f"SELECT {','.join(cols_read)} FROM documentos_emenda ORDER BY id"
    )

    batch = []
    novas = 0
    skipped_no_emenda = 0
    processed = 0

    while True:
        rows = cursor_lite.fetchmany(5000)
        if not rows:
            break

        for row in rows:
            processed += 1
            cod_doc = row["codigo_documento"]
            if cod_doc in codigos_doc_prod:
                continue

            # Mapear emenda_id local -> prod
            local_emenda_id = row["emenda_id"]
            codigo_emenda = local_map.get(local_emenda_id)
            if not codigo_emenda:
                skipped_no_emenda += 1
                continue
            prod_emenda_id = prod_map.get(codigo_emenda)
            if not prod_emenda_id:
                skipped_no_emenda += 1
                continue

            values = []
            for c in cols_read:
                if c == "emenda_id":
                    values.append(prod_emenda_id)
                else:
                    v = row[c]
                    # Converter embedding bytes para None (não sincronizamos embeddings)
                    if c == "embedding" and isinstance(v, bytes):
                        values.append(None)
                    else:
                        values.append(v)
            batch.append(tuple(values))
            novas += 1

            if len(batch) >= BATCH_SIZE:
                if not dry_run:
                    psycopg2.extras.execute_batch(pg_cur, sql, batch)
                    pg_cur.connection.commit()
                log(f"    documentos batch: {novas:,} inseridos, {processed:,}/{total_local:,} processados")
                batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  documentos: +{novas:,} novos (skip_sem_emenda={skipped_no_emenda})")


# ---------------------------------------------------------------------------
# Favorecidos
# ---------------------------------------------------------------------------
def sync_favorecidos(lite, pg_cur, dry_run: bool):
    """Sincroniza favorecidos — usa cpf_cnpj como chave de dedup."""
    cols = ["cpf_cnpj", "nome", "tipo_pessoa", "uf"]

    existentes_prod = get_existing_keys(pg_cur, "favorecidos", "cpf_cnpj")
    rows = lite.execute(f"SELECT {','.join(cols)} FROM favorecidos").fetchall()

    sql = """
        INSERT INTO favorecidos (cpf_cnpj, nome, tipo_pessoa, uf)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (cpf_cnpj) DO NOTHING
    """

    batch = []
    novas = 0
    for row in rows:
        if row["cpf_cnpj"] in existentes_prod:
            continue
        batch.append((row["cpf_cnpj"], row["nome"], row["tipo_pessoa"], row["uf"]))
        novas += 1

        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql, batch)
                pg_cur.connection.commit()
            batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  favorecidos: +{novas} novos ({len(rows)} local, {len(existentes_prod)} prod)")


# ---------------------------------------------------------------------------
# Documento-Favorecido (join table)
# ---------------------------------------------------------------------------
def sync_documento_favorecido(lite, pg_cur, dry_run: bool):
    """Sincroniza documento_favorecido via mapeamento de IDs."""
    # Mapeamento local doc_id -> codigo_documento
    local_doc_map = {}
    for row in lite.execute("SELECT id, codigo_documento FROM documentos_emenda").fetchall():
        local_doc_map[row["id"]] = row["codigo_documento"]

    # Mapeamento local fav_id -> cpf_cnpj
    local_fav_map = {}
    for row in lite.execute("SELECT id, cpf_cnpj FROM favorecidos").fetchall():
        local_fav_map[row["id"]] = row["cpf_cnpj"]

    # Mapeamento produção codigo_documento -> id
    pg_cur.execute("SELECT id, codigo_documento FROM documentos_emenda")
    prod_doc_map = {r[1]: r[0] for r in pg_cur.fetchall()}

    # Mapeamento produção cpf_cnpj -> id
    pg_cur.execute("SELECT id, cpf_cnpj FROM favorecidos")
    prod_fav_map = {r[1]: r[0] for r in pg_cur.fetchall()}

    # Pares já existentes em produção
    pg_cur.execute("SELECT documento_id, favorecido_id FROM documento_favorecido")
    pares_prod = {(r[0], r[1]) for r in pg_cur.fetchall()}

    total_local = lite.execute("SELECT COUNT(*) FROM documento_favorecido").fetchone()[0]
    log(f"  doc_favorecido: {total_local:,} local, {len(pares_prod):,} prod — lendo...")

    sql = """
        INSERT INTO documento_favorecido (documento_id, favorecido_id, valor_recebido)
        VALUES (%s, %s, %s)
    """

    cursor_lite = lite.execute(
        "SELECT documento_id, favorecido_id, valor_recebido FROM documento_favorecido ORDER BY id"
    )

    batch = []
    novas = 0
    skipped = 0
    processed = 0

    while True:
        rows = cursor_lite.fetchmany(5000)
        if not rows:
            break

        for row in rows:
            processed += 1
            local_doc_id = row["documento_id"]
            local_fav_id = row["favorecido_id"]

            cod_doc = local_doc_map.get(local_doc_id)
            cpf_cnpj = local_fav_map.get(local_fav_id)
            if not cod_doc or not cpf_cnpj:
                skipped += 1
                continue

            prod_doc_id = prod_doc_map.get(cod_doc)
            prod_fav_id = prod_fav_map.get(cpf_cnpj)
            if not prod_doc_id or not prod_fav_id:
                skipped += 1
                continue

            if (prod_doc_id, prod_fav_id) in pares_prod:
                continue

            batch.append((prod_doc_id, prod_fav_id, row["valor_recebido"]))
            pares_prod.add((prod_doc_id, prod_fav_id))
            novas += 1

            if len(batch) >= BATCH_SIZE:
                if not dry_run:
                    psycopg2.extras.execute_batch(pg_cur, sql, batch)
                    pg_cur.connection.commit()
                log(f"    doc_favorecido batch: {novas:,} inseridos, {processed:,}/{total_local:,}")
                batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  doc_favorecido: +{novas:,} novos (skip={skipped})")


# ---------------------------------------------------------------------------
# Sanções
# ---------------------------------------------------------------------------
def sync_sancoes(lite, pg_cur, tabela: str, cols: list[str], dry_run: bool):
    """Sincroniza uma tabela de sanções."""
    existentes = contar(pg_cur, tabela)
    rows = lite.execute(f"SELECT {','.join(cols)} FROM {tabela}").fetchall()
    total = len(rows)

    if existentes >= total:
        log(f"  {tabela}: {existentes} em prod >= {total} local — skip")
        return

    if not dry_run:
        # Limpar e reinserir (sanções mudam pouco, mais simples)
        pg_cur.execute(f"DELETE FROM {tabela}")

    placeholders = ",".join(["%s"] * len(cols))
    col_str = ",".join(cols)
    sql = f"INSERT INTO {tabela} ({col_str}) VALUES ({placeholders})"

    batch = []
    for row in rows:
        values = tuple(row[c] for c in cols)
        batch.append(values)

        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql, batch)
            batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  {tabela}: reinserido {total} registros (era {existentes} em prod)")


# ---------------------------------------------------------------------------
# Convênios
# ---------------------------------------------------------------------------
def sync_convenios(lite, pg_cur, dry_run: bool):
    cols = [
        "numero_convenio", "situacao", "orgao_concedente",
        "cpf_cnpj_convenente", "nome_convenente", "uf", "municipio",
        "objeto", "valor_convenio", "valor_liberado",
        "data_inicio", "data_fim", "funcao", "subfuncao",
    ]

    existentes = contar(pg_cur, "convenios")
    rows = lite.execute(f"SELECT {','.join(cols)} FROM convenios").fetchall()
    total = len(rows)

    if existentes >= total:
        log(f"  convenios: {existentes} em prod >= {total} local — skip")
        return

    if not dry_run:
        pg_cur.execute("DELETE FROM convenios")

    placeholders = ",".join(["%s"] * len(cols))
    sql = f"INSERT INTO convenios ({','.join(cols)}) VALUES ({placeholders})"

    batch = []
    for row in rows:
        batch.append(tuple(row[c] for c in cols))
        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                psycopg2.extras.execute_batch(pg_cur, sql, batch)
            batch = []

    if batch and not dry_run:
        psycopg2.extras.execute_batch(pg_cur, sql, batch)

    log(f"  convenios: reinserido {total} registros (era {existentes} em prod)")


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
TABELAS_ORDEM = [
    "schema",
    "lookups",
    "emendas",
    "documentos",
    "favorecidos",
    "documento_favorecido",
    "sancoes",
    "convenios",
]


def run_sync(tabela_filter: str | None, dry_run: bool):
    log("Conectando ao SQLite local e PostgreSQL produção...")
    lite = sqlite_connect()
    pg = pg_connect()
    pg.autocommit = False
    pg_cur = pg.cursor()

    try:
        etapas = TABELAS_ORDEM if not tabela_filter else [tabela_filter]

        for etapa in etapas:
            log(f"=== {etapa.upper()} ===")

            if etapa == "schema":
                ajustar_schema(pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "lookups":
                for tabela, cols in [
                    ("funcoes", ["codigo", "nome"]),
                    ("subfuncoes", ["codigo", "nome", "funcao_codigo"]),
                    ("programas", ["codigo", "nome"]),
                    ("acoes", ["codigo", "nome"]),
                    ("orgaos", ["codigo", "nome", "orgao_superior_codigo"]),
                    ("unidades_gestoras", ["codigo", "nome", "orgao_codigo"]),
                    ("categorias_despesa", ["codigo", "nome"]),
                    ("grupos_despesa", ["codigo", "nome"]),
                    ("elementos_despesa", ["codigo", "nome"]),
                    ("modalidades_aplicacao", ["codigo", "nome"]),
                ]:
                    sync_lookup(lite, pg_cur, tabela, cols, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "emendas":
                sync_emendas(lite, pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "documentos":
                sync_documentos(lite, pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "favorecidos":
                sync_favorecidos(lite, pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "documento_favorecido":
                sync_documento_favorecido(lite, pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "sancoes":
                sync_sancoes(lite, pg_cur, "sancoes_ceis",
                             ["cpf_cnpj", "nome", "tipo_sancao", "orgao_sancionador",
                              "data_inicio", "data_fim", "fundamentacao"], dry_run)
                sync_sancoes(lite, pg_cur, "sancoes_cnep",
                             ["cpf_cnpj", "nome", "tipo_sancao", "orgao_sancionador",
                              "data_inicio", "data_fim", "valor_multa"], dry_run)
                sync_sancoes(lite, pg_cur, "sancoes_cepim",
                             ["cnpj", "nome", "motivo", "orgao_maximo"], dry_run)
                sync_sancoes(lite, pg_cur, "sancoes_ceaf",
                             ["cpf", "nome", "tipo_punicao", "orgao_lotacao",
                              "data_inicio", "data_fim"], dry_run)
                if not dry_run:
                    pg.commit()

            elif etapa == "convenios":
                sync_convenios(lite, pg_cur, dry_run)
                if not dry_run:
                    pg.commit()

        log("=" * 50)
        log("SINCRONIZAÇÃO COMPLETA" + (" (DRY-RUN)" if dry_run else ""))

        # Contagens finais
        if not dry_run:
            log("Contagens finais em produção:")
            for t in ["parlamentares", "emendas", "documentos_emenda",
                       "favorecidos", "documento_favorecido",
                       "funcoes", "subfuncoes", "orgaos",
                       "sancoes_ceis", "sancoes_cnep", "sancoes_cepim", "sancoes_ceaf",
                       "convenios"]:
                count = contar(pg_cur, t)
                log(f"  {t}: {count:,}")

    except Exception as e:
        pg.rollback()
        log(f"ERRO: {e}")
        raise
    finally:
        pg_cur.close()
        pg.close()
        lite.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincronizar SQLite → PostgreSQL produção")
    parser.add_argument("--dry-run", action="store_true",
                        help="Apenas mostra o que faria, sem alterar produção")
    parser.add_argument("--tabela", choices=TABELAS_ORDEM,
                        help="Sincronizar apenas uma etapa específica")
    args = parser.parse_args()

    run_sync(tabela_filter=args.tabela, dry_run=args.dry_run)
