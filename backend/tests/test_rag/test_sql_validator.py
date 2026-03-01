import pytest
from app.services.rag.sql_validator import SQLValidator


@pytest.fixture
def validator():
    return SQLValidator()


def test_select_valido(validator):
    ok, msg = validator.validar("SELECT * FROM emendas WHERE ano = 2024")
    assert ok is True
    assert msg == "OK"


def test_drop_proibido(validator):
    ok, msg = validator.validar("DROP TABLE emendas")
    assert ok is False
    assert "proibido" in msg.lower()


def test_delete_proibido(validator):
    ok, msg = validator.validar("DELETE FROM emendas WHERE id = 1")
    assert ok is False
    assert "proibido" in msg.lower()


def test_update_proibido(validator):
    ok, msg = validator.validar("UPDATE emendas SET ano = 2025")
    assert ok is False


def test_insert_proibido(validator):
    ok, msg = validator.validar("INSERT INTO emendas (ano) VALUES (2024)")
    assert ok is False


def test_sql_vazia(validator):
    ok, msg = validator.validar("")
    assert ok is False
