import sqlparse
import structlog

logger = structlog.get_logger()


class SQLValidator:
    """Validação em duas camadas: sintática + semântica."""

    TABELAS_VALIDAS = {"emendas", "parlamentares", "execucao",
                        "classificacao_orcamentaria"}
    COLUNAS_VALIDAS = {
        "emendas": {"id", "codigo_emenda", "cod_autor", "nome_autor", "ano",
                     "tipo_emenda", "funcao", "funcao_nome", "subfuncao",
                     "subfuncao_nome", "uf", "valor_empenhado", "valor_pago",
                     "descricao", "localidade"},
        "parlamentares": {"cod_autor", "nome", "partido", "uf", "legislaturas"},
    }

    def validar_sintatica(self, sql: str) -> tuple[bool, str]:
        """Verifica se a SQL é sintaticamente válida."""
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "SQL vazia"
            stmt = parsed[0]
            if stmt.get_type() not in ("SELECT", None):
                return False, f"Apenas SELECT permitido, recebeu: {stmt.get_type()}"
            return True, "OK"
        except Exception as e:
            return False, str(e)

    def validar_semantica(self, sql: str) -> tuple[bool, str]:
        """Verifica se não contém comandos perigosos."""
        sql_lower = sql.lower()
        for cmd in ["drop", "delete", "update", "insert", "alter", "truncate"]:
            if cmd in sql_lower:
                return False, f"Comando proibido: {cmd}"
        return True, "OK"

    def validar(self, sql: str) -> tuple[bool, str]:
        """Validação completa em duas camadas."""
        ok, msg = self.validar_sintatica(sql)
        if not ok:
            return False, f"Erro sintático: {msg}"
        ok, msg = self.validar_semantica(sql)
        if not ok:
            return False, f"Erro semântico: {msg}"
        return True, "OK"
