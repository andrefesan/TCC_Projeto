import json
import re
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import structlog

logger = structlog.get_logger()

PROMPT_PLANNER = """Você é um planejador de consultas sobre emendas parlamentares brasileiras.
Analise a consulta e as entidades extraídas para classificar o tipo de busca necessária.

Retorne APENAS um JSON válido, sem markdown e sem blocos de código.

Campos obrigatórios:
- "tipo_consulta": "especifica" (filtros precisos como autor+ano), "exploratoria" (filtros amplos), "analitica" (agregações/rankings)
- "especificidade": "alta" (autor+ano ou autor+UF+ano), "media" (1-2 filtros genéricos), "baixa" (sem filtros ou só área)
- "volume_esperado": "poucos" (1-20 resultados prováveis), "moderado" (20-100), "muitos" (100+)
- "threshold_suficiencia": número inteiro — mínimo de resultados SQL para considerar busca suficiente (1 para consultas específicas, 20 para exploratórias)
- "precisa_busca_vetorial": true/false — se a consulta depende de busca semântica (áreas temáticas sem filtro SQL direto)
- "precisa_busca_documentos": true/false — se a consulta menciona obra, projeto, equipamento, serviço, material ou finalidade específica que requer busca nas observações dos documentos de despesa
- "limite_sugerido": número de resultados ideal (5-50, default 20)
- "estrategia_hibrida": "rrf" (fusão completa SQL+vetorial para buscas com área temática, obras específicas ou amplas), "sql_first" (SQL prioritário, vetorial como complemento se insuficiente), "sql_only" (SQL suficiente, vetorial desnecessário — para consultas com autor+ano/UF sem componente semântico)

Regras de classificação:
- Se tem "autor" + "ano" ou "autor" + "uf" (sem area e sem obra): especifica, alta, poucos, threshold=1, estrategia_hibrida="sql_only"
- Se tem "autor" sem ano/uf: especifica, media, moderado, threshold=5, estrategia_hibrida="sql_first"
- Se tem só "area" ou "uf" sem autor: exploratoria, baixa, muitos, threshold=20, estrategia_hibrida="rrf"
- Se operacao é soma/contagem/media/ranking SEM "area": analitica, threshold=1, estrategia_hibrida="sql_only"
- Se operacao é soma/contagem/media/ranking COM "area": analitica, threshold=1, estrategia_hibrida="sql_first", precisa_busca_vetorial=true
- Se a consulta menciona obra, projeto, equipamento, serviço, material ou finalidade específica (ponte, escola, hospital, construção, reforma, pavimentação, UBS, creche, quadra, barragem, rodovia, ambulância, equipamento, caminhão, escavadeira, trator, veículo, esgoto, saneamento, irrigação, habitação, moradia, aquisição, medicamento, insumo, consultoria, capacitação, treinamento, bolsa, laboratório, informática, computador, mobiliário, uniforme): estrategia_hibrida="rrf", precisa_busca_documentos=true, precisa_busca_vetorial=true
- precisa_busca_vetorial=true quando "area" está presente ou consulta é exploratória
- precisa_busca_documentos=true quando a consulta busca detalhes de obras, projetos, equipamentos, serviços ou finalidades específicas

ENTIDADES EXTRAÍDAS:
{entidades_json}

CONSULTA ORIGINAL:
{consulta}

JSON:"""


class QueryPlanner:
    """Classifica consultas e define estratégia de busca."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=256,
            temperature=0,
        )
        self.prompt = ChatPromptTemplate.from_template(PROMPT_PLANNER)

    def _extrair_json(self, texto: str) -> dict:
        """Extrai JSON mesmo se envolto em markdown."""
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', texto, re.DOTALL)
        if match:
            texto = match.group(1)
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(texto.strip())

    async def planejar(self, consulta: str, entidades: dict) -> dict:
        """Classifica a consulta e retorna plano de busca.

        Returns:
            dict com tipo_consulta, especificidade, volume_esperado,
            threshold_suficiencia, precisa_busca_vetorial, limite_sugerido
        """
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke({
                "consulta": consulta,
                "entidades_json": json.dumps(entidades, ensure_ascii=False),
            })
            plano = self._extrair_json(response.content)
            # Validar e garantir campos obrigatórios com defaults seguros
            plano.setdefault("tipo_consulta", "exploratoria")
            plano.setdefault("especificidade", "media")
            plano.setdefault("volume_esperado", "moderado")
            plano.setdefault("threshold_suficiencia", 20)
            plano.setdefault("precisa_busca_vetorial", True)
            plano.setdefault("limite_sugerido", 20)
            plano.setdefault("estrategia_hibrida", "rrf")
            plano.setdefault("precisa_busca_documentos", False)
            # Cap de segurança no limite
            plano["limite_sugerido"] = min(max(plano["limite_sugerido"], 5), 50)
            plano["threshold_suficiencia"] = max(plano["threshold_suficiencia"], 1)
            if plano.get("estrategia_hibrida") not in ("rrf", "sql_first", "sql_only"):
                plano["estrategia_hibrida"] = "rrf"

            logger.info("plano_consulta", consulta=consulta[:50], plano=plano)
            return plano
        except Exception as e:
            logger.warning("planner_fallback", erro=str(e))
            return self._plano_fallback(entidades, consulta)

    _KEYWORDS_DOCUMENTO = frozenset({
        # Obras civis
        "ponte", "escola", "hospital", "construcao", "construção", "reforma",
        "creche", "quadra", "ubs", "posto de saude", "posto de saúde",
        "unidade de saude", "unidade de saúde", "barragem", "academia de saude",
        # Infraestrutura
        "pavimentacao", "pavimentação", "asfalto", "rodovia", "estrada",
        # Equipamentos e veículos
        "ambulancia", "ambulância", "equipamento", "caminhao", "caminhão",
        "escavadeira", "trator", "retroescavadeira", "onibus", "ônibus",
        "veiculo", "veículo",
        # Saneamento e água
        "esgoto", "saneamento", "irrigacao", "irrigação", "abastecimento de agua",
        # Habitação
        "habitacao", "habitação", "moradia",
        # Serviços e capacitação
        "consultoria", "capacitacao", "capacitação", "treinamento",
        "servico", "serviço",
        # Materiais e insumos
        "medicamento", "insumo", "material",
        "informatica", "informática", "computador", "mobiliario", "mobiliário",
        "uniforme", "laboratorio", "laboratório",
        # Assistência social
        "bolsa", "auxilio", "auxílio",
        # Genéricos
        "obra", "projeto", "aquisicao de", "aquisição de",
    })

    def _detectar_busca_documentos(self, consulta: str) -> bool:
        """Detecta se a consulta menciona obra, equipamento, serviço ou finalidade específica."""
        consulta_lower = consulta.lower()
        return any(kw in consulta_lower for kw in self._KEYWORDS_DOCUMENTO)

    def _plano_fallback(self, entidades: dict, consulta: str = "") -> dict:
        """Plano heurístico quando o LLM falha."""
        tem_autor = bool(entidades.get("autor"))
        tem_ano = bool(entidades.get("ano"))
        tem_uf = bool(entidades.get("uf"))
        tem_area = bool(entidades.get("area"))
        operacao = entidades.get("operacao", "busca")
        precisa_documentos = self._detectar_busca_documentos(consulta)

        # Consultas sobre obras específicas → sempre rrf + busca em documentos
        if precisa_documentos:
            return {
                "tipo_consulta": "exploratoria",
                "especificidade": "baixa",
                "volume_esperado": "muitos",
                "threshold_suficiencia": 5,
                "precisa_busca_vetorial": True,
                "precisa_busca_documentos": True,
                "limite_sugerido": 20,
                "estrategia_hibrida": "rrf",
            }

        if operacao in ("soma", "contagem", "ranking", "media"):
            return {
                "tipo_consulta": "analitica",
                "especificidade": "alta",
                "volume_esperado": "poucos",
                "threshold_suficiencia": 1,
                "precisa_busca_vetorial": tem_area,
                "precisa_busca_documentos": False,
                "limite_sugerido": 20,
                "estrategia_hibrida": "sql_first" if tem_area else "sql_only",
            }

        if tem_autor and (tem_ano or tem_uf):
            return {
                "tipo_consulta": "especifica",
                "especificidade": "alta",
                "volume_esperado": "poucos",
                "threshold_suficiencia": 1,
                "precisa_busca_vetorial": False,
                "precisa_busca_documentos": False,
                "limite_sugerido": 20,
                "estrategia_hibrida": "sql_only",
            }

        if tem_autor:
            return {
                "tipo_consulta": "especifica",
                "especificidade": "media",
                "volume_esperado": "moderado",
                "threshold_suficiencia": 5,
                "precisa_busca_vetorial": False,
                "precisa_busca_documentos": False,
                "limite_sugerido": 20,
                "estrategia_hibrida": "sql_first",
            }

        return {
            "tipo_consulta": "exploratoria",
            "especificidade": "baixa",
            "volume_esperado": "muitos",
            "threshold_suficiencia": 20,
            "precisa_busca_vetorial": tem_area,
            "precisa_busca_documentos": False,
            "limite_sugerido": 20,
            "estrategia_hibrida": "rrf" if tem_area else "sql_first",
        }
