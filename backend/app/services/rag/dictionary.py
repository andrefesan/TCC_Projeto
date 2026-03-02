import json
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()

_DICT_PATH = Path(__file__).parent.parent.parent.parent / "data" / "dictionary.json"


class BudgetDictionary:
    """Wrapper do dicionário orçamentário (87 mapeamentos)."""

    def __init__(self):
        with open(_DICT_PATH, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._funcoes = self._data.get("mapeamentos_funcao", {})
        self._subfuncoes = self._data.get("mapeamentos_subfuncao", {})
        self._regioes = self._data.get("mapeamentos_regiao", {})

    def resolver_funcao(self, termo: str) -> Optional[str]:
        """Resolve um termo para código de função orçamentária."""
        return self._funcoes.get(termo.lower().strip())

    def resolver_subfuncao(self, termo: str) -> Optional[str]:
        """Resolve um termo para código de subfunção."""
        return self._subfuncoes.get(termo.lower().strip())

    def resolver_area(self, termo: str) -> Optional[str]:
        """Tenta resolver subfunção (mais específico) e depois função."""
        codigo = self.resolver_subfuncao(termo)
        if codigo:
            return codigo
        return self.resolver_funcao(termo)

    def resolver_regiao(self, nome: str) -> Optional[list[str]]:
        """Resolve nome de região para lista de UFs."""
        return self._regioes.get(nome.lower().strip())

    def get_all_mappings(self) -> dict:
        """Retorna todos os mapeamentos."""
        return self._data
