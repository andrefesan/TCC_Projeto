-- ============================================
-- Migration: Schema inicial - Transparência Fiscal
-- Extensões: pgvector
-- Tabelas: parlamentares, classificacao_orcamentaria, emendas, execucao, consultas_log
-- ============================================

-- Habilitar pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. Parlamentares
-- ============================================
CREATE TABLE parlamentares (
    cod_autor INTEGER PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    nome_civil VARCHAR(200),
    partido VARCHAR(20),
    uf VARCHAR(2),
    legislaturas INTEGER[],
    url_foto TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_parlamentares_partido ON parlamentares (partido);
CREATE INDEX idx_parlamentares_uf ON parlamentares (uf);
CREATE INDEX idx_parlamentares_nome ON parlamentares USING gin(to_tsvector('portuguese', nome));

-- ============================================
-- 2. Classificação Orçamentária
-- ============================================
CREATE TABLE classificacao_orcamentaria (
    id SERIAL PRIMARY KEY,
    funcao VARCHAR(5) NOT NULL,
    funcao_nome VARCHAR(100),
    subfuncao VARCHAR(5),
    subfuncao_nome VARCHAR(100),
    programa VARCHAR(10),
    programa_nome VARCHAR(200),
    descricao TEXT,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_classif_funcao ON classificacao_orcamentaria (funcao);
CREATE INDEX idx_classif_subfuncao ON classificacao_orcamentaria (subfuncao);
CREATE INDEX idx_classif_embedding ON classificacao_orcamentaria
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);

-- ============================================
-- 3. Emendas
-- ============================================
CREATE TABLE emendas (
    id SERIAL PRIMARY KEY,
    codigo_emenda VARCHAR(50) UNIQUE,
    cod_autor INTEGER REFERENCES parlamentares(cod_autor),
    nome_autor VARCHAR(200),
    ano INTEGER NOT NULL,
    tipo_emenda VARCHAR(50),
    funcao VARCHAR(5),
    funcao_nome VARCHAR(100),
    subfuncao VARCHAR(5),
    subfuncao_nome VARCHAR(100),
    programa VARCHAR(10),
    acao VARCHAR(20),
    localidade VARCHAR(200),
    uf VARCHAR(2),
    valor_empenhado NUMERIC(15,2) DEFAULT 0,
    valor_liquidado NUMERIC(15,2) DEFAULT 0,
    valor_pago NUMERIC(15,2) DEFAULT 0,
    descricao TEXT,
    embedding vector(384),
    fonte VARCHAR(50) DEFAULT 'Portal da Transparência',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_emendas_ano ON emendas (ano);
CREATE INDEX idx_emendas_uf ON emendas (uf);
CREATE INDEX idx_emendas_cod_autor ON emendas (cod_autor);
CREATE INDEX idx_emendas_funcao ON emendas (funcao);
CREATE INDEX idx_emendas_subfuncao ON emendas (subfuncao);
CREATE INDEX idx_emendas_tipo ON emendas (tipo_emenda);
CREATE INDEX idx_emendas_tsv ON emendas
    USING gin(to_tsvector('portuguese',
        coalesce(nome_autor, '') || ' ' ||
        coalesce(funcao_nome, '') || ' ' ||
        coalesce(subfuncao_nome, '') || ' ' ||
        coalesce(descricao, '')));
CREATE INDEX idx_emendas_embedding ON emendas
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);

-- ============================================
-- 4. Execução
-- ============================================
CREATE TABLE execucao (
    id SERIAL PRIMARY KEY,
    emenda_id INTEGER REFERENCES emendas(id) ON DELETE CASCADE,
    data_movimento DATE,
    valor NUMERIC(15,2),
    fase VARCHAR(20),
    documento VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_execucao_emenda ON execucao (emenda_id);
CREATE INDEX idx_execucao_fase ON execucao (fase);
CREATE INDEX idx_execucao_data ON execucao (data_movimento);

-- ============================================
-- 5. Consultas Log
-- ============================================
CREATE TABLE consultas_log (
    id SERIAL PRIMARY KEY,
    consulta_nl TEXT NOT NULL,
    entidades_json JSON,
    sql_gerada TEXT,
    modo_busca VARCHAR(20),
    num_resultados INTEGER,
    latencia_ms INTEGER,
    sucesso BOOLEAN DEFAULT TRUE,
    erro TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_log_created ON consultas_log (created_at);
