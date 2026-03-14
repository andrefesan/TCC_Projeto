-- ============================================
-- Migration: Módulo de Beneficiários
-- Tabelas: documentos_emenda, beneficiarios
-- Objetivo: Rastrear beneficiários finais das emendas parlamentares
-- via encadeamento de endpoints do Portal da Transparência
-- ============================================

-- ============================================
-- 1. Documentos vinculados a emendas
-- ============================================
CREATE TABLE documentos_emenda (
    id SERIAL PRIMARY KEY,
    emenda_id INTEGER REFERENCES emendas(id) ON DELETE CASCADE,
    codigo_documento VARCHAR(50) NOT NULL,
    fase VARCHAR(20),
    valor NUMERIC(15,2) DEFAULT 0,
    data_documento DATE,
    tipo_documento VARCHAR(100),
    observacao TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_doc_codigo ON documentos_emenda (codigo_documento);
CREATE INDEX idx_doc_emenda_id ON documentos_emenda (emenda_id);
CREATE INDEX idx_doc_fase ON documentos_emenda (fase);

-- ============================================
-- 2. Beneficiários finais
-- ============================================
CREATE TABLE beneficiarios (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos_emenda(id) ON DELETE CASCADE,
    codigo_pessoa VARCHAR(20),
    nome VARCHAR(300) NOT NULL,
    tipo_pessoa VARCHAR(2) CHECK (tipo_pessoa IN ('PF', 'PJ')),
    cpf_cnpj VARCHAR(20),
    valor_recebido NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_benef_documento_id ON beneficiarios (documento_id);
CREATE INDEX idx_benef_cpf_cnpj ON beneficiarios (cpf_cnpj);
CREATE INDEX idx_benef_nome ON beneficiarios
    USING gin(to_tsvector('portuguese', nome));
CREATE INDEX idx_benef_tipo ON beneficiarios (tipo_pessoa);
