import pytest
from app.services.rag.dictionary import BudgetDictionary


def test_resolver_funcao_saude():
    d = BudgetDictionary()
    assert d.resolver_funcao("saúde") == "10"
    assert d.resolver_funcao("saude") == "10"
    assert d.resolver_funcao("hospital") == "10"


def test_resolver_funcao_educacao():
    d = BudgetDictionary()
    assert d.resolver_funcao("educação") == "12"
    assert d.resolver_funcao("escola") == "12"


def test_resolver_subfuncao():
    d = BudgetDictionary()
    assert d.resolver_subfuncao("ensino fundamental") == "361"
    assert d.resolver_subfuncao("ensino superior") == "364"
    assert d.resolver_subfuncao("atenção básica") == "301"


def test_resolver_area_prioriza_subfuncao():
    d = BudgetDictionary()
    # "saneamento basico" existe como subfunção (512) E função (17 via "saneamento")
    assert d.resolver_area("saneamento basico") == "512"


def test_resolver_regiao():
    d = BudgetDictionary()
    assert d.resolver_regiao("norte") == ["AC", "AM", "AP", "PA", "RO", "RR", "TO"]
    assert d.resolver_regiao("sudeste") == ["ES", "MG", "RJ", "SP"]
    assert d.resolver_regiao("inexistente") is None


def test_resolver_funcao_inexistente():
    d = BudgetDictionary()
    assert d.resolver_funcao("xyz_inexistente") is None
