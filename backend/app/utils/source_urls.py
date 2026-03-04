def build_emenda_source_url(record: dict) -> str:
    """Constrói URL de detalhe da emenda no Portal da Transparência."""
    codigo_emenda = record.get("codigo_emenda")
    if codigo_emenda:
        return (
            f"https://portaldatransparencia.gov.br/emendas/detalhe"
            f"?codigoEmenda={codigo_emenda}"
        )
    return "https://portaldatransparencia.gov.br/emendas/consulta"


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
