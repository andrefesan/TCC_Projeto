from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Banco de Dados (Supabase)
    DATABASE_URL: str = "postgresql://postgres:secret@localhost:5432/transparencia_fiscal"

    # API LLM (Anthropic Claude)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 2048

    # API Portal da Transparência (CGU)
    CGU_API_KEY: str = ""
    CGU_API_BASE_URL: str = "https://api.portaldatransparencia.gov.br/api-de-dados"
    CGU_RATE_LIMIT_RPM: int = 400

    # Embeddings
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIMENSIONS: int = 384
    EMBEDDING_BATCH_SIZE: int = 256

    # HNSW Index
    HNSW_M: int = 16
    HNSW_EF_CONSTRUCTION: int = 200

    # Busca
    SIMILARITY_THRESHOLD: float = 0.45
    MAX_RESULTS: int = 20

    # Aplicação
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    PRODUCTION_URL: str = ""
    LOG_LEVEL: str = "INFO"


settings = Settings()
