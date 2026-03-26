from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import json
import re
import structlog

logger = structlog.get_logger()

PROMPT_INTERPRETACAO = """Você é um assistente de análise de consultas sobre emendas parlamentares brasileiras.
Extraia as entidades da pergunta do cidadão e retorne APENAS um JSON válido, sem markdown e sem blocos de código.

Campos possíveis:
- "autor": nome do parlamentar (se mencionado)
- "partido": sigla do partido (se mencionado)
- "uf": sigla do estado ou nome da região (se mencionado)
- "ano": ano específico (se mencionado um único ano)
- "ano_inicio" e "ano_fim": para períodos (ex: "de 2020 a 2024")
- "area": área temática (saúde, educação, etc.)
- "tipo_emenda": tipo (individual, bancada, comissão)
- "operacao": tipo de operação. Valores possíveis:
  - "busca" (padrão, listar registros individuais)
  - "soma" (quando pergunta "quanto", "total", "valor total")
  - "contagem" (quando pergunta "quantas", "número de")
  - "contagem_distinta" (quando pergunta "quantos X distintos/diferentes")
  - "ranking" (quando pergunta "maiores", "top", "quem mais")
  - "media" (quando pergunta "média", "em média")
  - "tendencia" (quando pergunta sobre evolução, crescimento, tendência ao longo do tempo)
  - "comparacao" (quando pede comparação entre partidos, áreas, estados ou tipos)
- "instituicao": nome de instituição específica mencionada (ex: Hospital das Clínicas, Prefeitura de Salvador, USP, UFMG, Fundo Municipal de Saúde)
- "beneficiario": nome de beneficiário final (pessoa física ou jurídica que recebeu recursos)
- "busca_beneficiario": true se a consulta pede informações sobre beneficiários, favorecidos ou destinatários finais dos recursos
- "ambiguidade": null se a consulta é clara, ou uma string descritiva se há ambiguidade
  (ex: "O sobrenome 'Silva' pode se referir a múltiplos parlamentares",
   "Não ficou claro se 'Acre' refere-se ao estado ou à Bancada do Acre")

Responda SOMENTE com o JSON. Exemplo: {{"autor": "nome", "ano": 2024, "ambiguidade": null}}

PERGUNTA: {consulta}"""


class QueryInterpreter:
    """Extrai entidades estruturadas da consulta em linguagem natural."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=512,
            temperature=0,
        )
        self.prompt = ChatPromptTemplate.from_template(PROMPT_INTERPRETACAO)

    def _extrair_json(self, texto: str) -> dict:
        """Extrai JSON mesmo se envolto em markdown."""
        # Tenta extrair de bloco markdown ```json ... ```
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', texto, re.DOTALL)
        if match:
            texto = match.group(1)
        # Tenta extrair primeiro objeto JSON encontrado
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(texto.strip())

    async def interpretar(self, consulta: str) -> dict:
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"consulta": consulta})

        try:
            entidades = self._extrair_json(response.content)
            logger.info("interpretacao_ok", consulta=consulta[:50],
                        entidades=entidades)
            return entidades
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("interpretacao_falha", response=response.content, erro=str(e))
            return {"raw_query": consulta}
