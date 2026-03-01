import pytest
from app.services.ingestion.normalizer import DataNormalizer
from app.models.parlamentar import Parlamentar


def test_upsert_parlamentar_novo(db_session):
    normalizer = DataNormalizer(db_session)
    data = {
        "cod_autor": 12345,
        "nome": "DEPUTADO TESTE",
        "partido": "PT",
        "uf": "AC",
        "legislaturas": [57],
    }
    parl = normalizer.upsert_parlamentar(data)
    normalizer.commit()

    assert parl.cod_autor == 12345
    assert parl.nome == "DEPUTADO TESTE"

    result = db_session.query(Parlamentar).filter_by(cod_autor=12345).first()
    assert result is not None
    assert result.partido == "PT"


def test_upsert_parlamentar_atualiza(db_session):
    normalizer = DataNormalizer(db_session)
    data = {"cod_autor": 99, "nome": "TESTE", "partido": "PT", "uf": "SP", "legislaturas": [56]}
    normalizer.upsert_parlamentar(data)
    normalizer.commit()

    data_atualizado = {"cod_autor": 99, "nome": "TESTE", "partido": "PL", "uf": "SP", "legislaturas": [56, 57]}
    normalizer.upsert_parlamentar(data_atualizado)
    normalizer.commit()

    result = db_session.query(Parlamentar).filter_by(cod_autor=99).first()
    assert result.partido == "PL"


def test_inserir_emenda(db_session):
    normalizer = DataNormalizer(db_session)
    emenda_data = {
        "codigo_emenda": "EMD001",
        "nome_autor": "TESTE",
        "ano": 2024,
        "tipo_emenda": "Individual",
        "funcao": "10",
        "funcao_nome": "Saúde",
        "uf": "AC",
        "valor_empenhado": 100000.00,
        "valor_pago": 50000.00,
    }
    emenda = normalizer.inserir_emenda(emenda_data)
    normalizer.commit()

    assert emenda.codigo_emenda == "EMD001"
    assert emenda.ano == 2024
