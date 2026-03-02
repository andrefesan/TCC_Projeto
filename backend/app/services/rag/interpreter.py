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
- "operacao": tipo de operação (total, ranking, comparação, tendência)

Responda SOMENTE com o JSON. Exemplo: {{"autor": "nome", "ano": 2024}}

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
