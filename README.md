# Transparência Fiscal — Consulta Inteligente de Emendas Parlamentares

Plataforma web que permite a pessoas comuns consultar dados sobre emendas parlamentares federais brasileiras em **linguagem natural**, recebendo respostas fundamentadas com citações verificáveis de fontes governamentais.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 4: INTERFACE                                        │
│  React + Vite (SPA) ──── FastAPI (REST API) ──── Swagger    │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 3: RAG HÍBRIDO                                      │
│  Interpretação (LLM) → Decomposição → Síntese (LLM)        │
│  Dicionário (87 mapeamentos) | LangChain | Validação SQL    │
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

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, LangChain, sentence-transformers
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS
- **Banco:** Supabase (PostgreSQL 16 + pgvector)
- **LLM:** Claude (Anthropic)
- **Deploy:** Vercel (frontend estático + backend serverless)

## Setup Local

```bash
# 1. Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# 2. Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

## Deploy (Railway)

```bash
npm i -g vercel
vercel          # Setup inicial
vercel --prod   # Deploy de produção
```


## Ingestão de Dados

```bash
cd backend
poetry run python scripts/ingest_all.py --anos 2020,2021,2022,2023,2024
poetry run python scripts/generate_embeddings.py
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Health check |
| POST | `/api/query` | Consulta em linguagem natural |
| GET | `/api/emendas` | Listagem de emendas (filtros) |
| GET | `/api/parlamentares` | Listagem de parlamentares |

---

**Autor:** André Ferreira Santana — UFAC
**TCC:** Arquitetura de Plataforma Baseada em LLM e RAG para Consulta Inteligente de Dados de Transparência Fiscal
