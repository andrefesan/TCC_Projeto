from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import structlog

logger = structlog.get_logger()

PROMPT_SINTESE_V14 = """Você é um assistente de transparência fiscal brasileira.
Responda a pergunta do cidadão com base EXCLUSIVAMENTE nos dados fornecidos abaixo.

REGRAS:
1. Responda em português acessível, evitando jargão orçamentário desnecessário.
2. Cite valores exatos com separador de milhares (ex: R$ 1.234.567,89).
3. Inclua referência às fontes primárias: Portal da Transparência (CGU) e/ou
   Câmara dos Deputados, indicando que os dados podem ser verificados nesses portais.
4. Se os dados forem insuficientes para responder, declare claramente:
   "Não foram encontrados dados suficientes para responder a esta consulta com
   confiança. Sugerimos consultar diretamente o Portal da Transparência."
5. NÃO invente informações. Use SOMENTE os dados fornecidos.
6. Ao mencionar siglas orçamentárias, explique-as na primeira ocorrência.
7. Formate listas com numeração quando houver rankings.
8. Para valores monetários, use sempre o formato brasileiro: R$ 1.234,56
9. Quando houver múltiplos anos, organize cronologicamente.
10. Se detectar tendência nos dados (crescimento/queda), mencione-a apenas se
    claramente suportada pelos números, sem inferir causalidade.
11. Use markdown para formatação: **negrito** para destaques, ## para seções,
    listas numeradas para rankings.

DADOS RECUPERADOS:
{contexto_dados}

PERGUNTA DO CIDADÃO:
{consulta_usuario}

RESPOSTA:"""


class ResponseSynthesizer:
    """Sintetiza resposta em linguagem natural a partir dos dados recuperados."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_template(PROMPT_SINTESE_V14)

    async def sintetizar(self, consulta: str, dados: list[dict]) -> dict:
        """Gera resposta em linguagem natural."""
        if not dados:
            return {
                "resposta": "Não foram encontrados dados suficientes para "
                            "responder a esta consulta com confiança. "
                            "Sugerimos consultar diretamente o Portal da "
                            "Transparência (https://portaldatransparencia.gov.br).",
                "fontes": ["https://portaldatransparencia.gov.br"],
                "dados": [],
            }

        contexto = self._formatar_contexto(dados)
        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "contexto_dados": contexto,
            "consulta_usuario": consulta,
        })

        fontes = self._extrair_fontes(dados)

        return {
            "resposta": response.content,
            "fontes": fontes,
            "dados": dados,
        }

    def _formatar_contexto(self, dados: list[dict]) -> str:
        """Formata dados recuperados como tabela textual para o prompt."""
        if not dados:
            return "Nenhum dado encontrado."

        linhas = []
        for i, d in enumerate(dados[:20], 1):
            linha = (
                f"{i}. Autor: {d.get('nome_autor', 'N/A')} | "
                f"Partido: {d.get('partido', 'N/A')} | "
                f"UF: {d.get('uf', 'N/A')} | "
                f"Ano: {d.get('ano', 'N/A')} | "
                f"Função: {d.get('funcao_nome', 'N/A')} | "
                f"Subfunção: {d.get('subfuncao_nome', 'N/A')} | "
                f"Empenhado: R$ {d.get('valor_empenhado', 0):,.2f} | "
                f"Pago: R$ {d.get('valor_pago', 0):,.2f}"
            )
            linhas.append(linha)

        return "\n".join(linhas)

    def _extrair_fontes(self, dados: list[dict]) -> list[str]:
        """Extrai URLs de fontes primárias."""
        fontes = set()
        fontes.add("https://portaldatransparencia.gov.br")
        if any(d.get("partido") for d in dados):
            fontes.add("https://dadosabertos.camara.leg.br")
        return list(fontes)
