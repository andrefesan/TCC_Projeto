from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import json
import structlog

logger = structlog.get_logger()

PROMPT_INTERPRETACAO = """Você é um assistente de análise de consultas sobre emendas parlamentares brasileiras.
Extraia as entidades da pergunta do cidadão e retorne EXCLUSIVAMENTE um JSON válido.

Campos possíveis:
- "autor": nome do parlamentar (se mencionado)
- "partido": sigla do partido (se mencionado)
- "uf": sigla do estado ou nome da região (se mencionado)
- "ano": ano ou período (se mencionado)
- "ano_inicio" e "ano_fim": para períodos
- "area": área temática (saúde, educação, etc.)
- "tipo_emenda": tipo (individual, bancada, comissão)
- "operacao": tipo de operação (total, ranking, comparação, tendência)

PERGUNTA: {consulta}

JSON:"""


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

    async def interpretar(self, consulta: str) -> dict:
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"consulta": consulta})

        try:
            entidades = json.loads(response.content)
            logger.info("interpretacao_ok", consulta=consulta[:50],
                        entidades=entidades)
            return entidades
        except json.JSONDecodeError:
            logger.error("interpretacao_falha", response=response.content)
            return {"raw_query": consulta}
