-- ============================================
-- Migration: Normalização extensiva do schema
-- Novas tabelas: lookup (funcoes, subfuncoes, programas, acoes, orgaos, UGs),
--                classificação despesa, favorecidos, sanções, convênios
-- ============================================

-- ============================================
-- 1. Classificação funcional-programática
-- ============================================
CREATE TABLE IF NOT EXISTS funcoes (
    codigo VARCHAR(5) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS subfuncoes (
    codigo VARCHAR(5) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    funcao_codigo VARCHAR(5) REFERENCES funcoes(codigo)
);
CREATE INDEX IF NOT EXISTS idx_subfuncoes_funcao ON subfuncoes(funcao_codigo);

CREATE TABLE IF NOT EXISTS programas (
    codigo VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(300)
);

CREATE TABLE IF NOT EXISTS acoes (
    codigo VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(300)
);

-- ============================================
-- 2. Estrutura organizacional
-- ============================================
CREATE TABLE IF NOT EXISTS orgaos (
    codigo VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(300),
    orgao_superior_codigo VARCHAR(20)
);
CREATE INDEX IF NOT EXISTS idx_orgaos_superior ON orgaos(orgao_superior_codigo);

CREATE TABLE IF NOT EXISTS unidades_gestoras (
    codigo VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(300),
    orgao_codigo VARCHAR(20) REFERENCES orgaos(codigo)
);
CREATE INDEX IF NOT EXISTS idx_ug_orgao ON unidades_gestoras(orgao_codigo);

-- ============================================
-- 3. Classificação da despesa
-- ============================================
CREATE TABLE IF NOT EXISTS categorias_despesa (
    codigo VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS grupos_despesa (
    codigo VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS elementos_despesa (
    codigo VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS modalidades_aplicacao (
    codigo VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(200)
);

-- ============================================
-- 4. Favorecidos (normalizado de documentos_emenda)
-- ============================================
CREATE TABLE IF NOT EXISTS favorecidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf_cnpj VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(300),
    tipo_pessoa VARCHAR(2),
    uf VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_favorecidos_nome ON favorecidos(nome);
CREATE INDEX IF NOT EXISTS idx_favorecidos_uf ON favorecidos(uf);
CREATE INDEX IF NOT EXISTS idx_favorecidos_tipo ON favorecidos(tipo_pessoa);

CREATE TABLE IF NOT EXISTS documento_favorecido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER REFERENCES documentos_emenda(id) ON DELETE CASCADE,
    favorecido_id INTEGER REFERENCES favorecidos(id),
    valor_recebido NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_doc_fav_documento ON documento_favorecido(documento_id);
CREATE INDEX IF NOT EXISTS idx_doc_fav_favorecido ON documento_favorecido(favorecido_id);

-- ============================================
-- 5. Sanções
-- ============================================
CREATE TABLE IF NOT EXISTS sancoes_ceis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf_cnpj VARCHAR(20) NOT NULL,
    nome VARCHAR(300),
    tipo_sancao VARCHAR(200),
    orgao_sancionador VARCHAR(300),
    data_inicio DATE,
    data_fim DATE,
    fundamentacao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ceis_cpf_cnpj ON sancoes_ceis(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_ceis_nome ON sancoes_ceis(nome);

CREATE TABLE IF NOT EXISTS sancoes_cnep (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf_cnpj VARCHAR(20) NOT NULL,
    nome VARCHAR(300),
    tipo_sancao VARCHAR(200),
    orgao_sancionador VARCHAR(300),
    data_inicio DATE,
    data_fim DATE,
    valor_multa NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cnep_cpf_cnpj ON sancoes_cnep(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_cnep_nome ON sancoes_cnep(nome);

CREATE TABLE IF NOT EXISTS sancoes_cepim (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj VARCHAR(20) NOT NULL,
    nome VARCHAR(300),
    motivo TEXT,
    orgao_maximo VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cepim_cnpj ON sancoes_cepim(cnpj);
CREATE INDEX IF NOT EXISTS idx_cepim_nome ON sancoes_cepim(nome);

CREATE TABLE IF NOT EXISTS sancoes_ceaf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf VARCHAR(14) NOT NULL,
    nome VARCHAR(300),
    tipo_punicao VARCHAR(200),
    orgao_lotacao VARCHAR(300),
    data_inicio DATE,
    data_fim DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ceaf_cpf ON sancoes_ceaf(cpf);
CREATE INDEX IF NOT EXISTS idx_ceaf_nome ON sancoes_ceaf(nome);

-- ============================================
-- 6. Convênios
-- ============================================
CREATE TABLE IF NOT EXISTS convenios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_convenio VARCHAR(50) UNIQUE,
    situacao VARCHAR(100),
    orgao_concedente VARCHAR(300),
    cpf_cnpj_convenente VARCHAR(20),
    nome_convenente VARCHAR(300),
    uf VARCHAR(2),
    municipio VARCHAR(200),
    objeto TEXT,
    valor_convenio NUMERIC(15,2),
    valor_liberado NUMERIC(15,2),
    data_inicio DATE,
    data_fim DATE,
    funcao VARCHAR(5),
    subfuncao VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_convenios_cpf_cnpj ON convenios(cpf_cnpj_convenente);
CREATE INDEX IF NOT EXISTS idx_convenios_uf ON convenios(uf);
CREATE INDEX IF NOT EXISTS idx_convenios_funcao ON convenios(funcao);
CREATE INDEX IF NOT EXISTS idx_convenios_situacao ON convenios(situacao);
