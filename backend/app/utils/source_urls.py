from urllib.parse import quote


def build_emenda_source_url(record: dict) -> str:
    """Constrói URL do Portal da Transparência filtrada por autor e ano."""
    base = "https://portaldatransparencia.gov.br/emendas/consulta"
    ano = record.get("ano")
    nome_autor = record.get("nome_autor", "")

    if ano and nome_autor:
        return f"{base}?de={ano}-01-01&ate={ano}-12-31&autor={quote(nome_autor)}"
    if ano:
        return f"{base}?de={ano}-01-01&ate={ano}-12-31"
    return base


def build_parlamentar_source_url(record: dict) -> str | None:
    """Constrói link direto ao parlamentar na Câmara dos Deputados."""
    cod_autor = record.get("cod_autor")
    if cod_autor:
        return f"https://www.camara.leg.br/deputados/{cod_autor}"
    return None


def enrich_record_with_sources(record: dict) -> dict:
    """Adiciona source_url e parlamentar_url a um registro de emenda."""
    enriched = dict(record)
    enriched["source_url"] = build_emenda_source_url(record)
    parlamentar_url = build_parlamentar_source_url(record)
    if parlamentar_url:
        enriched["parlamentar_url"] = parlamentar_url
    return enriched
