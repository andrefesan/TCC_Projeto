import httpx
from typing import List
import structlog

logger = structlog.get_logger()


class CamaraCollector:
    """Coletor de dados de parlamentares da Câmara dos Deputados."""

    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    async def coletar_deputados(self, legislatura: int = 57) -> List[dict]:
        """Coleta lista completa de deputados de uma legislatura."""
        deputados = []
        pagina = 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await client.get(
                    f"{self.BASE_URL}/deputados",
                    params={
                        "idLegislatura": legislatura,
                        "ordenarPor": "nome",
                        "pagina": pagina,
                        "itens": 100,
                    },
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("dados", [])
                if not items:
                    break

                for dep in items:
                    deputados.append({
                        "cod_autor": dep["id"],
                        "nome": dep["nome"].upper(),
                        "partido": dep.get("siglaPartido", ""),
                        "uf": dep.get("siglaUf", ""),
                        "url_foto": dep.get("urlFoto", ""),
                        "legislaturas": [legislatura],
                    })

                pagina += 1

        logger.info("deputados_coletados", total=len(deputados),
                     legislatura=legislatura)
        return deputados

    async def coletar_detalhes(self, cod_deputado: int) -> dict:
        """Coleta detalhes de um deputado específico."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/deputados/{cod_deputado}"
            )
            response.raise_for_status()
            data = response.json().get("dados", {})
            return {
                "nome_civil": data.get("nomeCivil", ""),
                "data_nascimento": data.get("dataNascimento"),
                "municipio_nascimento": data.get("municipioNascimento", ""),
                "escolaridade": data.get("escolaridade", ""),
            }
