import re
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.utils.source_urls import enrich_record_with_sources
import structlog

logger = structlog.get_logger()

PROMPT_SINTESE_V15 = """Você é um assistente de transparência fiscal brasileira.
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

FORMATO DE RESPOSTA OBRIGATÓRIO:
Estruture sua resposta exatamente assim:

RESUMO: [1-2 frases com a resposta direta e objetiva à pergunta]

DETALHES:
[Análise completa com valores, fontes e explicações]

SUGESTOES: [2-3 perguntas complementares que o cidadão poderia fazer para aprofundar a consulta, separadas por |]

{bloco_completude}
{bloco_regras_extras}
DADOS RECUPERADOS:
{contexto_dados}

PERGUNTA DO CIDADÃO:
{consulta_usuario}

RESPOSTA:"""

PROMPT_SEM_RESULTADOS = """Você é um assistente de transparência fiscal brasileira.
O cidadão fez uma pergunta, mas não foram encontrados dados correspondentes.

Entidades extraídas da pergunta:
{entidades_json}

Com base nas entidades acima, gere uma resposta útil que:
1. Informe que não foram encontrados dados para os filtros utilizados.
2. Sugira possíveis motivos (grafia do nome, período não disponível, filtro muito restritivo).
3. Proponha 2-3 consultas alternativas concretas que o cidadão pode tentar.
4. Indique o Portal da Transparência como fonte oficial para verificação.

Responda em português acessível. Use o formato:

RESUMO: [1 frase informando que não foram encontrados dados]

DETALHES:
[Motivos possíveis e sugestões]

SUGESTOES: [2-3 consultas alternativas separadas por |]

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

    async def sintetizar(self, consulta: str, dados: list[dict],
                         instituicao: str | None = None,
                         operacao: str = "busca",
                         tem_sancoes: bool = False,
                         completude: dict | None = None,
                         entidades: dict | None = None) -> dict:
        """Gera resposta em linguagem natural.

        Args:
            consulta: pergunta original do cidadão
            dados: registros recuperados
            instituicao: nome de instituição mencionada (se houver)
            operacao: tipo de operação (busca, soma, contagem, ranking, media)
            tem_sancoes: se há alertas de sanções nos dados
            completude: dict com total_no_banco, resultados_exibidos, dados_completos
            entidades: entidades extraídas da consulta (para resposta sem resultados)
        """
        if not dados:
            return await self._gerar_resposta_vazia(consulta, entidades or {})

        contexto = self._formatar_contexto(dados, operacao)

        # Verifica se há dados de beneficiários nos resultados
        tem_beneficiarios = any(d.get("beneficiario_nome") for d in dados)

        # Bloco de completude
        bloco_completude = self._formatar_completude(completude)

        # Regras extras acumuláveis
        regras_extras = []

        if operacao in ("soma", "contagem", "media"):
            regras_extras.append(
                "Os dados abaixo são resultados AGREGADOS (totais/contagens/médias). "
                "Apresente os valores de forma direta e clara, sem listar registros individuais."
            )
        elif operacao == "ranking":
            regras_extras.append(
                "Os dados abaixo são um RANKING. Apresente em lista numerada "
                "ordenada do maior para o menor valor, com nome, partido, UF e valores."
            )

        if tem_sancoes:
            regras_extras.append(
                "ALERTA DE SANÇÕES: Alguns beneficiários "
                "constam em cadastros de sanções (CEIS, CNEP, CEPIM ou CEAF). "
                "Destaque essas ocorrências com **ALERTA** e informe o tipo de sanção "
                "e o órgão sancionador. Isso pode indicar irregularidade na destinação "
                "dos recursos."
            )

        # Injeta regra condicional quando há instituição específica
        if instituicao and not tem_beneficiarios:
            regras_extras.append(
                f"IMPORTANTE: O usuário mencionou a instituição "
                f"\"{instituicao}\", mas os dados disponíveis só permitem filtragem por "
                "classificação funcional (função, subfunção) e UF — não por instituição "
                "beneficiária. Inclua na resposta um aviso claro de que os resultados "
                "representam uma aproximação por área temática e localidade, e não uma "
                "confirmação de repasse direto à instituição mencionada."
            )
        elif tem_beneficiarios:
            regras_extras.append(
                "Os dados incluem informações de beneficiários "
                "finais (pessoas físicas ou jurídicas que receberam os recursos). "
                "Apresente o nome do beneficiário, CPF/CNPJ (parcialmente oculto para PF) "
                "e o valor recebido de forma clara e organizada."
            )

        bloco_regras = ""
        if regras_extras:
            numeradas = [f"{12 + i}. {r}" for i, r in enumerate(regras_extras)]
            bloco_regras = "\n".join(numeradas) + "\n"

        prompt = ChatPromptTemplate.from_template(PROMPT_SINTESE_V15)
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "contexto_dados": contexto,
            "consulta_usuario": consulta,
            "bloco_completude": bloco_completude,
            "bloco_regras_extras": bloco_regras,
        })

        dados_enriquecidos = [enrich_record_with_sources(d) for d in dados]
        fontes = self._extrair_fontes(dados_enriquecidos)

        # Parsear seções estruturadas da resposta
        resumo, resposta_limpa, sugestoes = self._parsear_resposta(response.content)

        return {
            "resposta": resposta_limpa,
            "resumo": resumo,
            "fontes": fontes,
            "dados": dados_enriquecidos,
            "sugestoes_followup": sugestoes,
        }

    async def _gerar_resposta_vazia(self, consulta: str,
                                     entidades: dict) -> dict:
        """Gera resposta inteligente quando não há dados."""
        import json

        try:
            prompt = ChatPromptTemplate.from_template(PROMPT_SEM_RESULTADOS)
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "consulta_usuario": consulta,
                "entidades_json": json.dumps(entidades, ensure_ascii=False),
            })
            resumo, resposta_limpa, sugestoes = self._parsear_resposta(
                response.content
            )
            return {
                "resposta": resposta_limpa,
                "resumo": resumo,
                "fontes": ["https://portaldatransparencia.gov.br"],
                "dados": [],
                "sugestoes_followup": sugestoes,
            }
        except Exception as e:
            logger.warning("erro_resposta_vazia", erro=str(e))
            return {
                "resposta": "Não foram encontrados dados suficientes para "
                            "responder a esta consulta com confiança. "
                            "Sugerimos consultar diretamente o Portal da "
                            "Transparência (https://portaldatransparencia.gov.br).",
                "resumo": "Nenhum dado encontrado para esta consulta.",
                "fontes": ["https://portaldatransparencia.gov.br"],
                "dados": [],
                "sugestoes_followup": [],
            }

    def _formatar_completude(self, completude: dict | None) -> str:
        """Gera bloco de completude para o prompt."""
        if not completude:
            return ""

        total = completude.get("total_no_banco", 0)
        exibidos = completude.get("resultados_exibidos", 0)
        completo = completude.get("dados_completos", False)

        if completo:
            status = "DADOS COMPLETOS — todos os registros encontrados estão apresentados abaixo."
        else:
            restantes = total - exibidos
            status = (
                f"AMOSTRA — existem {total:,} registros no total, "
                f"mas apenas os {exibidos} de maior valor empenhado são apresentados abaixo "
                f"(mais {restantes:,} não exibidos)."
            )

        return (
            f"COMPLETUDE DOS DADOS:\n"
            f"- Total de registros no banco: {total:,}\n"
            f"- Registros apresentados: {exibidos}\n"
            f"- Status: {status}\n"
            f"Se os dados são COMPLETOS, declare isso na resposta (ex: 'foram encontradas X emendas no total').\n"
            f"Se são AMOSTRA, informe quantos existem e que apenas os de maior valor foram apresentados.\n"
        )

    def _parsear_resposta(self, content: str) -> tuple[str | None, str, list[str]]:
        """Extrai resumo, corpo e sugestões da resposta estruturada do LLM.

        Returns:
            (resumo, resposta_limpa, sugestoes_followup)
        """
        resumo = None
        sugestoes = []

        # Extrair RESUMO
        match_resumo = re.search(
            r'RESUMO:\s*(.+?)(?=\n\s*(?:DETALHES:|SUGESTOES:|$))',
            content, re.DOTALL
        )
        if match_resumo:
            resumo = match_resumo.group(1).strip()

        # Extrair SUGESTOES
        match_sugestoes = re.search(
            r'SUGESTOES:\s*(.+?)$', content, re.DOTALL
        )
        if match_sugestoes:
            raw = match_sugestoes.group(1).strip()
            sugestoes = [s.strip() for s in raw.split("|") if s.strip()]

        # Extrair corpo (DETALHES ou tudo entre RESUMO e SUGESTOES)
        match_detalhes = re.search(
            r'DETALHES:\s*(.+?)(?=\n\s*SUGESTOES:|$)',
            content, re.DOTALL
        )
        if match_detalhes:
            resposta_limpa = match_detalhes.group(1).strip()
        else:
            # Fallback: remover RESUMO e SUGESTOES, usar o resto
            resposta_limpa = content
            resposta_limpa = re.sub(r'RESUMO:\s*.+?\n', '', resposta_limpa, count=1)
            resposta_limpa = re.sub(r'SUGESTOES:\s*.+?$', '', resposta_limpa, flags=re.DOTALL)
            resposta_limpa = resposta_limpa.strip()

        if not resposta_limpa:
            resposta_limpa = content

        return resumo, resposta_limpa, sugestoes

    def _formatar_contexto(self, dados: list[dict],
                           operacao: str = "busca") -> str:
        """Formata dados recuperados como tabela textual para o prompt."""
        if not dados:
            return "Nenhum dado encontrado."

        # Agregações: formato diferente
        if operacao in ("soma", "contagem", "media") and len(dados) == 1:
            d = dados[0]
            partes = []
            if "total_empenhado" in d:
                partes.append(f"Total Empenhado: R$ {d['total_empenhado'] or 0:,.2f}")
            if "total_liquidado" in d:
                partes.append(f"Total Liquidado: R$ {d['total_liquidado'] or 0:,.2f}")
            if "total_pago" in d:
                partes.append(f"Total Pago: R$ {d['total_pago'] or 0:,.2f}")
            if "media_empenhado" in d:
                partes.append(f"Média Empenhado: R$ {d['media_empenhado'] or 0:,.2f}")
            if "media_pago" in d:
                partes.append(f"Média Pago: R$ {d['media_pago'] or 0:,.2f}")
            if "quantidade" in d:
                partes.append(f"Quantidade: {d['quantidade']:,}")
            return " | ".join(partes)

        linhas = []
        for i, d in enumerate(dados[:20], 1):
            # Ranking
            if operacao == "ranking" and "total_empenhado" in d:
                linha = (
                    f"{i}. {d.get('nome_autor', 'N/A')} | "
                    f"Partido: {d.get('partido', 'N/A')} | "
                    f"UF: {d.get('uf', 'N/A')} | "
                    f"Total Empenhado: R$ {(d.get('total_empenhado') or 0):,.2f} | "
                    f"Total Pago: R$ {(d.get('total_pago') or 0):,.2f} | "
                    f"Qtd: {d.get('quantidade', 0)}"
                )
            else:
                linha = (
                    f"{i}. Autor: {d.get('nome_autor', 'N/A')} | "
                    f"Partido: {d.get('partido', 'N/A')} | "
                    f"UF: {d.get('uf', 'N/A')} | "
                    f"Ano: {d.get('ano', 'N/A')} | "
                    f"Função: {d.get('funcao_nome', 'N/A')} | "
                    f"Subfunção: {d.get('subfuncao_nome', 'N/A')} | "
                    f"Empenhado: R$ {(d.get('valor_empenhado') or 0):,.2f} | "
                    f"Pago: R$ {(d.get('valor_pago') or 0):,.2f}"
                )
            if d.get("beneficiario_nome"):
                linha += (
                    f" | Beneficiário: {d['beneficiario_nome']}"
                    f" ({d.get('beneficiario_tipo', 'N/A')})"
                    f" | CPF/CNPJ: {d.get('beneficiario_cpf_cnpj', 'N/A')}"
                    f" | Valor Recebido: R$ {(d.get('beneficiario_valor') or 0):,.2f}"
                )
            if d.get("sancoes"):
                for s in d["sancoes"]:
                    linha += (
                        f" | **SANÇÃO ({s['cadastro']})**: {s['tipo']} "
                        f"por {s['orgao']}"
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
