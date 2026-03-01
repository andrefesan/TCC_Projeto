# Transparência Fiscal — Consulta Inteligente de Emendas Parlamentares

Plataforma web que permite a pessoas comuns consultar dados sobre emendas parlamentares federais brasileiras em **linguagem natural**, recebendo respostas fundamentadas com citações verificáveis de fontes governamentais.

> **Acesse:** [https://andrefersan.com/](https://andrefersan.com/)

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 4: INTERFACE                                        │
│  React 18 + Vite (SPA) ── FastAPI (REST API) ── Swagger     │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 3: RAG HÍBRIDO                                      │
│  Interpretação (LLM) → Decomposição → Síntese (LLM)        │
│  Dicionário (97 mapeamentos) | LangChain | Validação SQL    │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 2: INDEXAÇÃO HÍBRIDA                                │
│  pgvector (HNSW) | B-tree/GIN | Embeddings (E5-small 384d) │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 1: INGESTÃO DE DADOS                                │
│  CGU API | Câmara API | SIOP CSV                            │
│  Normalização → PostgreSQL (Supabase)                       │
└─────────────────────────────────────────────────────────────┘
```

## Stack

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, LangChain, sentence-transformers, Alembic, structlog |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, React Router, React Query, Axios |
| **Banco** | Supabase (PostgreSQL 16 + pgvector 0.7) |
| **Embeddings** | `intfloat/multilingual-e5-small` (384 dimensões) |
| **LLM** | Claude — Anthropic |
| **Deploy** | Railway (Docker multi-stage) + domínio personalizado |

## Setup Local

```bash
# 1. Clone e configure variáveis de ambiente
cp .env.example .env
# Preencha DATABASE_URL, ANTHROPIC_API_KEY e CGU_API_KEY

# 2. Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# 3. Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

## Deploy (Railway)

O deploy utiliza o `Dockerfile` na raiz (multi-stage: frontend build + backend), configurado via `railway.toml`:

```bash
# Instale o CLI do Railway
npm i -g @railway/cli

railway login
railway link          # Vincular ao projeto
railway up            # Deploy
```

Variáveis de ambiente necessárias no Railway: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL`, `CGU_API_KEY`.

## Ingestão de Dados

```bash
cd backend
poetry run python scripts/ingest_all.py --anos 2020,2021,2022,2023,2024
poetry run python scripts/generate_embeddings.py
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| POST | `/api/query` | Consulta em linguagem natural |
| GET | `/api/emendas` | Listagem de emendas (filtros) |
| GET | `/api/parlamentares` | Listagem de parlamentares |

## Estrutura do Projeto

```
TCC_Projeto/
├── backend/
│   ├── app/
│   │   ├── api/             # Rotas FastAPI
│   │   ├── models/          # Modelos SQLAlchemy
│   │   └── services/
│   │       ├── ingestion/   # Coletores de dados (CGU, Câmara, SIOP)
│   │       ├── indexing/    # Geração de embeddings e índices HNSW
│   │       ├── rag/         # Pipeline RAG (interpretação, decomposição, síntese)
│   │       └── search/      # Busca SQL, vetorial e híbrida
│   ├── scripts/             # Ingestão e geração de embeddings
│   └── Dockerfile
├── frontend/
│   └── src/                 # Interface React + Tailwind
├── supabase/
│   └── migrations/          # Migrações de esquema SQL
├── Dockerfile               # Multi-stage (frontend + backend)
├── railway.toml             # Configuração Railway
└── .env.example             # Variáveis de ambiente
```

---

**Autor:** André Ferreira Santana — UFAC
**TCC:** Arquitetura de Plataforma Baseada em LLM e RAG para Consulta Inteligente de Dados de Transparência Fiscal
