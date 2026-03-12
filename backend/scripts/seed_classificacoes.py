"""
Seed da tabela classificacao_orcamentaria com a classificação funcional
oficial brasileira (Portaria MOG nº 42/1999).

Insere todas as 28 funções e suas subfunções típicas.
Após executar, rode generate_embeddings.py para gerar os vetores.

Uso:
    cd TCC_Projeto/backend
    python scripts/seed_classificacoes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal

# ─── Classificação funcional-programática (Portaria MOG nº 42/1999) ───

FUNCOES = {
    "01": "Legislativa",
    "02": "Judiciária",
    "03": "Essencial à Justiça",
    "04": "Administração",
    "05": "Defesa Nacional",
    "06": "Segurança Pública",
    "07": "Relações Exteriores",
    "08": "Assistência Social",
    "09": "Previdência Social",
    "10": "Saúde",
    "11": "Trabalho",
    "12": "Educação",
    "13": "Cultura",
    "14": "Direitos da Cidadania",
    "15": "Urbanismo",
    "16": "Habitação",
    "17": "Saneamento",
    "18": "Gestão Ambiental",
    "19": "Ciência e Tecnologia",
    "20": "Agricultura",
    "21": "Organização Agrária",
    "22": "Indústria",
    "23": "Comércio e Serviços",
    "24": "Comunicações",
    "25": "Energia",
    "26": "Transporte",
    "27": "Desporto e Lazer",
    "28": "Encargos Especiais",
}

SUBFUNCOES = {
    # 01 - Legislativa
    "031": ("01", "Ação Legislativa"),
    "032": ("01", "Controle Externo"),
    # 02 - Judiciária
    "061": ("02", "Ação Judiciária"),
    "062": ("02", "Defesa do Interesse Público no Processo Judiciário"),
    # 03 - Essencial à Justiça
    "091": ("03", "Defesa da Ordem Jurídica"),
    "092": ("03", "Representação Judicial e Extrajudicial"),
    # 04 - Administração
    "121": ("04", "Planejamento e Orçamento"),
    "122": ("04", "Administração Geral"),
    "123": ("04", "Administração Financeira"),
    "124": ("04", "Controle Interno"),
    "125": ("04", "Normatização e Fiscalização"),
    "126": ("04", "Tecnologia da Informação"),
    "127": ("04", "Ordenamento Territorial"),
    "128": ("04", "Formação de Recursos Humanos"),
    "129": ("04", "Administração de Receitas"),
    "130": ("04", "Administração de Concessões"),
    "131": ("04", "Comunicação Social"),
    # 05 - Defesa Nacional
    "151": ("05", "Defesa Aérea"),
    "152": ("05", "Defesa Naval"),
    "153": ("05", "Defesa Terrestre"),
    # 06 - Segurança Pública
    "181": ("06", "Policiamento"),
    "182": ("06", "Defesa Civil"),
    "183": ("06", "Informação e Inteligência"),
    # 07 - Relações Exteriores
    "211": ("07", "Relações Diplomáticas"),
    "212": ("07", "Cooperação Internacional"),
    # 08 - Assistência Social
    "241": ("08", "Assistência ao Idoso"),
    "242": ("08", "Assistência ao Portador de Deficiência"),
    "243": ("08", "Assistência à Criança e ao Adolescente"),
    "244": ("08", "Assistência Comunitária"),
    # 09 - Previdência Social
    "271": ("09", "Previdência Básica"),
    "272": ("09", "Previdência do Regime Estatutário"),
    "273": ("09", "Previdência Complementar"),
    "274": ("09", "Previdência Especial"),
    # 10 - Saúde
    "301": ("10", "Atenção Básica"),
    "302": ("10", "Assistência Hospitalar e Ambulatorial"),
    "303": ("10", "Suporte Profilático e Terapêutico"),
    "304": ("10", "Vigilância Sanitária"),
    "305": ("10", "Vigilância Epidemiológica"),
    "306": ("10", "Alimentação e Nutrição"),
    # 11 - Trabalho
    "331": ("11", "Proteção e Benefícios ao Trabalhador"),
    "332": ("11", "Relações de Trabalho"),
    "333": ("11", "Empregabilidade"),
    "334": ("11", "Fomento ao Trabalho"),
    # 12 - Educação
    "361": ("12", "Ensino Fundamental"),
    "362": ("12", "Ensino Médio"),
    "363": ("12", "Ensino Profissional"),
    "364": ("12", "Ensino Superior"),
    "365": ("12", "Educação Infantil"),
    "366": ("12", "Educação de Jovens e Adultos"),
    "367": ("12", "Educação Especial"),
    "368": ("12", "Educação Básica"),
    # 13 - Cultura
    "391": ("13", "Patrimônio Histórico, Artístico e Arqueológico"),
    "392": ("13", "Difusão Cultural"),
    # 14 - Direitos da Cidadania
    "421": ("14", "Custódia e Reintegração Social"),
    "422": ("14", "Direitos Individuais, Coletivos e Difusos"),
    # 15 - Urbanismo
    "451": ("15", "Infraestrutura Urbana"),
    "452": ("15", "Serviços Urbanos"),
    "453": ("15", "Transportes Coletivos Urbanos"),
    # 16 - Habitação
    "481": ("16", "Habitação Rural"),
    "482": ("16", "Habitação Urbana"),
    # 17 - Saneamento
    "511": ("17", "Saneamento Básico Rural"),
    "512": ("17", "Saneamento Básico Urbano"),
    # 18 - Gestão Ambiental
    "541": ("18", "Preservação e Conservação Ambiental"),
    "542": ("18", "Controle Ambiental"),
    "543": ("18", "Recuperação de Áreas Degradadas"),
    "544": ("18", "Recursos Hídricos"),
    "545": ("18", "Meteorologia"),
    # 19 - Ciência e Tecnologia
    "571": ("19", "Desenvolvimento Científico"),
    "572": ("19", "Desenvolvimento Tecnológico e Engenharia"),
    "573": ("19", "Difusão do Conhecimento Científico e Tecnológico"),
    # 20 - Agricultura
    "601": ("20", "Promoção da Produção Vegetal"),
    "602": ("20", "Promoção da Produção Animal"),
    "603": ("20", "Defesa Sanitária Vegetal"),
    "604": ("20", "Defesa Sanitária Animal"),
    "605": ("20", "Abastecimento"),
    "606": ("20", "Extensão Rural"),
    # 21 - Organização Agrária
    "631": ("21", "Reforma Agrária"),
    "632": ("21", "Colonização"),
    # 22 - Indústria
    "661": ("22", "Promoção Industrial"),
    "662": ("22", "Produção Industrial"),
    "663": ("22", "Mineração"),
    "664": ("22", "Propriedade Industrial"),
    "665": ("22", "Normalização e Qualidade"),
    # 23 - Comércio e Serviços
    "691": ("23", "Promoção Comercial"),
    "692": ("23", "Comercialização"),
    "693": ("23", "Comércio Exterior"),
    "694": ("23", "Serviços Financeiros"),
    "695": ("23", "Turismo"),
    # 24 - Comunicações
    "721": ("24", "Comunicações Postais"),
    "722": ("24", "Telecomunicações"),
    # 25 - Energia
    "751": ("25", "Conservação de Energia"),
    "752": ("25", "Energia Elétrica"),
    "753": ("25", "Petróleo"),
    "754": ("25", "Álcool"),
    # 26 - Transporte
    "781": ("26", "Transporte Aéreo"),
    "782": ("26", "Transporte Rodoviário"),
    "783": ("26", "Transporte Ferroviário"),
    "784": ("26", "Transporte Hidroviário"),
    "785": ("26", "Transportes Especiais"),
    # 27 - Desporto e Lazer
    "811": ("27", "Desporto de Rendimento"),
    "812": ("27", "Desporto Comunitário"),
    "813": ("27", "Lazer"),
    # 28 - Encargos Especiais
    "841": ("28", "Refinanciamento da Dívida Interna"),
    "842": ("28", "Refinanciamento da Dívida Externa"),
    "843": ("28", "Serviço da Dívida Interna"),
    "844": ("28", "Serviço da Dívida Externa"),
    "845": ("28", "Outras Transferências"),
    "846": ("28", "Outros Encargos Especiais"),
}


def seed():
    db = SessionLocal()
    try:
        # Verificar se já existem dados
        count = db.execute(
            text("SELECT COUNT(*) FROM classificacao_orcamentaria")
        ).scalar()

        if count > 0:
            print(f"Tabela já possui {count} registros. Limpando para re-seed...")
            db.execute(text("DELETE FROM classificacao_orcamentaria"))
            db.commit()

        registros = []

        # 1. Inserir cada função como registro standalone
        for cod, nome in FUNCOES.items():
            registros.append({
                "funcao": cod,
                "funcao_nome": nome,
                "subfuncao": None,
                "subfuncao_nome": None,
                "programa": None,
                "programa_nome": None,
                "descricao": nome,
            })

        # 2. Inserir cada subfunção com sua função típica
        for cod_sub, (cod_func, nome_sub) in SUBFUNCOES.items():
            nome_func = FUNCOES[cod_func]
            registros.append({
                "funcao": cod_func,
                "funcao_nome": nome_func,
                "subfuncao": cod_sub,
                "subfuncao_nome": nome_sub,
                "programa": None,
                "programa_nome": None,
                "descricao": f"{nome_func} - {nome_sub}",
            })

        # 3. Inserir em batch
        for r in registros:
            db.execute(text("""
                INSERT INTO classificacao_orcamentaria
                    (funcao, funcao_nome, subfuncao, subfuncao_nome,
                     programa, programa_nome, descricao)
                VALUES
                    (:funcao, :funcao_nome, :subfuncao, :subfuncao_nome,
                     :programa, :programa_nome, :descricao)
            """), r)

        db.commit()
        print(f"Seed concluído: {len(registros)} registros inseridos.")
        print(f"  - {len(FUNCOES)} funções")
        print(f"  - {len(SUBFUNCOES)} subfunções")
        print()
        print("Próximo passo: gere os embeddings com:")
        print("  python scripts/generate_embeddings.py")

    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
