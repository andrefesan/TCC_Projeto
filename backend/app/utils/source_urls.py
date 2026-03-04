TIPO_EMENDA_CODIGOS = {
    "individual": "1",
    "bancada": "2",
    "bancada estadual": "2",
    "comissão": "3",
    "comissao": "3",
    "relator": "4",
    "relator-geral": "4",
}


def _resolver_codigo_tipo_emenda(tipo_emenda: str) -> str | None:
    """Mapeia o nome do tipo de emenda para o código numérico do portal."""
    if not tipo_emenda:
        return None
    chave = tipo_emenda.strip().lower()
    for nome, codigo in TIPO_EMENDA_CODIGOS.items():
        if nome in chave:
            return codigo
    return None


def build_emenda_source_url(record: dict) -> str:
    """Constrói URL de detalhe da emenda no Portal da Transparência."""
    codigo_emenda = record.get("codigo_emenda")
    tipo_emenda = record.get("tipo_emenda", "")

    if codigo_emenda:
        codigo_tipo = _resolver_codigo_tipo_emenda(tipo_emenda)
        url = (
            f"https://portaldatransparencia.gov.br/emendas/detalhe"
            f"?codigoEmenda={codigo_emenda}"
        )
        if codigo_tipo:
            url += f"&codigoTipoEmenda={codigo_tipo}"
        return url

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
