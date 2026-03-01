import asyncio
import re
import httpx
from typing import AsyncGenerator
from app.config import settings
from app.utils.rate_limiter import RateLimiter
import structlog

logger = structlog.get_logger()

ESTADOS = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPÁ": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARÁ": "CE", "DISTRITO FEDERAL": "DF",
    "ESPÍRITO SANTO": "ES", "GOIÁS": "GO", "MARANHÃO": "MA",
    "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARÁ": "PA", "PARAÍBA": "PB",
    "PARANÁ": "PR", "PERNAMBUCO": "PE", "PIAUÍ": "PI",
    "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDÔNIA": "RO", "RORAIMA": "RR",
    "SANTA CATARINA": "SC", "SÃO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}

FUNCOES = {
    "Saúde": "10", "Educação": "12", "Segurança Pública": "06",
    "Transporte": "26", "Assistência Social": "08", "Cultura": "13",
    "Defesa Nacional": "05", "Agricultura": "20",
    "Ciência e Tecnologia": "19", "Meio Ambiente": "18",
    "Direitos da Cidadania": "14", "Desporto e Lazer": "27",
    "Habitação": "16", "Saneamento": "17", "Trabalho": "11",
    "Previdência Social": "09", "Comunicações": "24", "Turismo": "23",
}


class CGUCollector:
    """Coletor de dados de emendas do Portal da Transparência."""

    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"

    def __init__(self):
        self.rate_limiter = RateLimiter(settings.CGU_RATE_LIMIT_RPM)
        self.headers = {"chave-api-dados": settings.CGU_API_KEY}

    async def coletar_emendas(self, ano: int) -> AsyncGenerator[dict, None]:
        """Coleta todas as emendas de um ano com paginação automática."""
        pagina = 1
        total_coletadas = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                await self.rate_limiter.acquire()

                try:
                    response = await client.get(
                        f"{self.BASE_URL}/emendas",
                        params={"ano": ano, "pagina": pagina},
                        headers=self.headers,
                    )

                    if response.status_code == 429:
                        logger.warning("rate_limit_hit", ano=ano, pagina=pagina)
                        await asyncio.sleep(10)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    if not data:
                        logger.info("coleta_completa", ano=ano, total=total_coletadas)
                        break

                    for emenda in data:
                        yield self._normalizar_emenda(emenda, ano)
                        total_coletadas += 1

                    pagina += 1

                except httpx.HTTPStatusError as e:
                    logger.error("http_error", status=e.response.status_code,
                                 ano=ano, pagina=pagina)
                    if e.response.status_code >= 500:
                        await asyncio.sleep(30)
                        continue
                    raise

    def _normalizar_emenda(self, raw: dict, ano: int) -> dict:
        """Normaliza campos da API CGU para o schema unificado."""
        return {
            "codigo_emenda": raw.get("codigoEmenda"),
            "nome_autor": (raw.get("nomeAutor") or "").strip().upper(),
            "ano": ano,
            "tipo_emenda": raw.get("tipoEmenda", ""),
            "funcao": self._extrair_codigo_funcao(raw.get("funcao", "")),
            "funcao_nome": raw.get("funcao", ""),
            "subfuncao": self._extrair_codigo_subfuncao(raw.get("subfuncao", "")),
            "subfuncao_nome": raw.get("subfuncao", ""),
            "localidade": raw.get("localidadeDoGasto", ""),
            "uf": self._extrair_uf(raw.get("localidadeDoGasto", "")),
            "valor_empenhado": self._parse_valor(raw.get("valorEmpenhado", "0")),
            "valor_pago": self._parse_valor(raw.get("valorPago", "0")),
            "descricao": raw.get("nomeSubfuncao", ""),
            "fonte": "Portal da Transparência",
        }

    @staticmethod
    def _parse_valor(valor_str) -> float:
        """Converte string monetária BR para float."""
        if not valor_str:
            return 0.0
        if isinstance(valor_str, (int, float)):
            return float(valor_str)
        return float(str(valor_str).replace(".", "").replace(",", "."))

    @staticmethod
    def _extrair_uf(localidade: str) -> str:
        """Extrai sigla UF de string como 'ACRE (UF)' ou 'RIO BRANCO (MUN)'."""
        if not localidade:
            return ""
        match = re.search(r"\(UF\)$", localidade)
        if match:
            nome = localidade.replace(" (UF)", "").strip()
            return ESTADOS.get(nome, "")
        return ""

    @staticmethod
    def _extrair_codigo_funcao(funcao_str: str) -> str:
        """Extrai código da função a partir do nome."""
        for nome, codigo in FUNCOES.items():
            if nome.lower() in funcao_str.lower():
                return codigo
        return ""

    @staticmethod
    def _extrair_codigo_subfuncao(subfuncao_str: str) -> str:
        """Extrai código numérico da subfunção se presente."""
        if not subfuncao_str:
            return ""
        match = re.match(r"^(\d{3})", subfuncao_str)
        return match.group(1) if match else ""
