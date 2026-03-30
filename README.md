# Fiscalia — Consulta Inteligente de Emendas Parlamentares

Plataforma web que permite consultar dados sobre emendas parlamentares federais brasileiras usando **linguagem natural**. O sistema interpreta perguntas como *"Quanto o estado do Pará recebeu em emendas de saúde em 2023?"* e retorna respostas fundamentadas, com citações verificáveis de fontes governamentais oficiais.

> **Acesse a plataforma:** [fiscalia.astrosoft.com.br](https://fiscalia.astrosoft.com.br)

---

## Sobre

Iniciativa acadêmica sem fins lucrativos. O objetivo é tornar os dados de emendas parlamentares mais acessíveis, permitindo que qualquer pessoa consulte informações públicas sem precisar navegar entre múltiplos portais governamentais ou entender vocabulários orçamentários especializados.

O artigo associado apresenta e avalia a arquitetura RAG híbrida implementada nesta plataforma, comparando três estratégias de recuperação (SQL puro, vetorial puro e híbrido) em um corpus de 32.787 emendas parlamentares e 915 parlamentares.

---

## Arquitetura

O sistema é organizado em quatro camadas:

```
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 4 — INTERFACE                                        │
│  React 18 + Vite (SPA) ── FastAPI (REST) ── Swagger UI       │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 3 — PIPELINE RAG HÍBRIDO                             │
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐   │
│  │ Interpretação│──▸│ Decomposição │──▸│ Planejamento de │   │
│  │   (LLM)     │   │  (SQL + Vec) │   │    consulta     │   │
│  └─────────────┘   └──────────────┘   └────────┬────────┘   │
│                                                 │            │
│  ┌──────────────────────────────────────────────▼──────────┐ │
│  │  Recuperação: SQL ∪ Vetorial → Fusão RRF → Reranking   │ │
│  └──────────────────────────────────────────────┬──────────┘ │
│                                                 │            │
│  ┌──────────────────────────────────────────────▼──────────┐ │
│  │            Síntese (LLM) — resposta com fontes          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Dicionário de domínio (97 mapeamentos) | Validação SQL      │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 2 — INDEXAÇÃO HÍBRIDA                                │
│  pgvector (HNSW m=16, ef=200) | B-tree/GIN | E5-small 384d  │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 1 — INGESTÃO DE DADOS                               │
│  Portal da Transparência (CGU) | Câmara dos Deputados |     │
│  SIOP/SIGA Brasil (CSV) → Normalização → PostgreSQL          │
└──────────────────────────────────────────────────────────────┘
```

**Fluxo de uma consulta:** o usuário digita uma pergunta em linguagem natural → o pipeline RAG interpreta a intenção e extrai entidades (autor, UF, ano, área funcional) → decompõe em filtros SQL e/ou embedding vetorial → o planejador escolhe a estratégia (SQL puro, vetorial puro ou híbrido com RRF) → executa a busca → o sintetizador gera uma resposta em linguagem acessível com links para as fontes oficiais.

---

## Stack

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, LangChain, sentence-transformers, Alembic, structlog |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, React Router, React Query, Axios |
| **Banco de dados** | PostgreSQL 16 + pgvector 0.7 (Supabase) |
| **Embeddings** | `intfloat/multilingual-e5-small` (384 dimensões) |
| **LLM** | Claude (Anthropic) |
| **Deploy** | Railway (Docker multi-stage) |

---

## Estrutura do projeto

```
├── backend/
│   ├── app/
│   │   ├── api/                # Rotas FastAPI (query, emendas, parlamentares, health)
│   │   ├── models/             # Modelos SQLAlchemy (emenda, parlamentar, beneficiário...)
│   │   ├── schemas/            # Schemas Pydantic (request/response)
│   │   ├── services/
│   │   │   ├── ingestion/      # Coletores de dados (CGU, Câmara, SIOP)
│   │   │   ├── indexing/       # Geração de embeddings e índices HNSW
│   │   │   ├── rag/            # Pipeline RAG (interpretação → decomposição → síntese)
│   │   │   └── search/         # Busca SQL, vetorial e híbrida (RRF)
│   │   └── utils/              # Circuit breaker, rate limiter, formatação
│   ├── data/
│   │   ├── dictionary.json     # Dicionário de domínio (97 mapeamentos)
│   │   └── prompts/            # Templates de prompt para o LLM
│   ├── migrations/             # Migrações Alembic
│   ├── scripts/                # Scripts de ingestão, embeddings e avaliação
│   └── tests/                  # Testes unitários e de avaliação
├── frontend/
│   └── src/
│       ├── components/         # SearchBar, ResponseCard, DataTable, FilterPanel...
│       ├── pages/              # HomePage, ResultsPage, AboutPage
│       ├── hooks/              # useQuery, useEmendas
│       └── services/           # Cliente API (Axios)
├── supabase/
│   └── migrations/             # Migrações SQL do schema
├── Dockerfile                  # Build multi-stage (frontend + backend)
├── railway.toml                # Configuração de deploy
└── .env.example                # Variáveis de ambiente (template)
```

---

## Pré-requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 com extensão pgvector
- Conta no [Supabase](https://supabase.com/) (ou PostgreSQL local com pgvector)
- Chave de API da Anthropic (Claude)
- Chave de API do Portal da Transparência (CGU)

## Setup local

```bash
# 1. Clone o repositório
git clone https://github.com/anonymus-astro/Fiscalia.git
cd Fiscalia

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves (DATABASE_URL, ANTHROPIC_API_KEY, CGU_API_KEY)

# 3. Backend
cd backend
poetry install            # ou: pip install -r requirements.txt
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# 4. Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

O backend roda em `http://localhost:8000` e o frontend em `http://localhost:5173`.

---

## Pipeline de dados

A plataforma consome dados de três fontes governamentais:

1. **Portal da Transparência (CGU)** — emendas parlamentares, execução orçamentária, convênios e sanções. Coleta via API REST com rate limiting e circuit breaker.

2. **Câmara dos Deputados — Dados Abertos** — dados de parlamentares (nome, partido, UF, legislatura). Coleta via API REST.

3. **SIOP/SIGA Brasil** — classificações orçamentárias (funções e subfunções). Importação via CSV.

Após a coleta, os dados passam por normalização (padronização de nomes, UFs, partidos, valores monetários) e são inseridos no PostgreSQL. Em seguida, embeddings vetoriais são gerados com o modelo `intfloat/multilingual-e5-small` e indexados via HNSW no pgvector.

```bash
# Ingestão completa (2020–2024)
cd backend
poetry run python scripts/ingest_all.py --anos 2020,2021,2022,2023,2024

# Geração de embeddings
poetry run python scripts/generate_embeddings.py
```

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `POST` | `/api/query` | Consulta em linguagem natural |
| `GET` | `/api/emendas` | Listagem de emendas com filtros (ano, UF, autor, função) |
| `GET` | `/api/parlamentares` | Listagem de parlamentares |

Documentação interativa disponível em `/docs` (Swagger UI) quando o backend está rodando.

---

## Avaliação

O sistema foi avaliado com **120 consultas** distribuídas em 4 categorias de complexidade (factuais, semânticas, comparativas e de beneficiários), comparando 3 abordagens:

| Métrica | Híbrido | SQL Puro | Vetorial Puro |
|---------|---------|----------|---------------|
| Precision@5 | **73,1%** | 69,8% | 69,0% |
| NDCG@5 | **64,8%** | 60,6% | 54,8% |
| Extração de entidades | **95,4%** | — | — |

O ganho mais expressivo foi em consultas semânticas, onde o híbrido superou o SQL puro em +15,7 p.p. no NDCG@5. Testes t pareados confirmaram significância estatística (p < 0,05) para as principais métricas.

Detalhes completos em [`backend/tests/test_queries/relatorio_avaliacao.md`](backend/tests/test_queries/relatorio_avaliacao.md).

---

## Deploy

O deploy usa o `Dockerfile` na raiz (multi-stage: build do frontend + backend Python), configurado via `railway.toml`:

```bash
npm i -g @railway/cli
railway login
railway link
railway up
```

Variáveis de ambiente necessárias no Railway: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL`, `CGU_API_KEY`.

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
