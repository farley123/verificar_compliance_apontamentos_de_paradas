import pandas as pd
import numpy as np
import openpyxl


def extrair_pnp_reclassifica_para_tempo_em_producao(
    planilha: str, nome_do_recurso: str = None
):
    base = pd.read_excel(planilha, engine="openpyxl")

    # Condição base para todos os recursos
    query_str = "`Categoria original` == 'Paradas não planejadas' and `Categoria reclassificada` == 'Tempo de produção'"

    # Se um nome de recurso for informado, adiciona a trava da linha
    if nome_do_recurso:
        query_str += " and `Original Line` == @nome_do_recurso"

    base = base.query(query_str)

    base = base[
        [
            "Original Line",
            "Categoria original",
            "Categoria reclassificada",
            "Hora de início",
            "Hora de Fim",
            "Bottleneck Duration Minutes",
            "Process Order",
            "Comentário"
        ]
    ]
    base['Comentário']=base['Comentário'].fillna('sem comentários')
    return (base, base["Bottleneck Duration Minutes"].count())

def extrair_linhas(planilha:str):
    base = pd.read_excel(planilha,engine='openpyxl')
    base = base['Original Line'].unique().tolist()
    return base


def tempo_total_de_paradas(planilha:str):
    base = pd.read_excel(planilha,engine='openpyxl')
    base = base['Bottleneck Duration Minutes'].count()
    return base


def extrair_pnp_reclassifica_para_tempo_ocioso(planilha: str, nome_do_recurso: str = None):
    base = pd.read_excel(planilha, engine="openpyxl")

    # Condição base para todos os recursos
    query_str = "`Categoria original` == 'Paradas não planejadas' and `Categoria reclassificada` == 'Não ocupado'"

    # Se um nome de recurso for informado, adiciona a trava da linha
    if nome_do_recurso:
        query_str += " and `Original Line` == @nome_do_recurso"

    base = base.query(query_str)

    base = base[
        [
            "Original Line",
            "Categoria original",
            "Categoria reclassificada",
            "Hora de início",
            "Hora de Fim",
            "Bottleneck Duration Minutes",
            "Process Order",
            "Comentário"
        ]
    ]
    base['Comentário'] = base['Comentário'].fillna('sem comentários')
    return (base, base["Bottleneck Duration Minutes"].count())


def extrair_pp_reclassifica_para_tempo_ocioso(planilha: str, nome_do_recurso: str = None):
    base = pd.read_excel(planilha, engine="openpyxl")

    # Condição base para todos os recursos
    query_str = "`Categoria original` == 'Paradas planejadas' and `Categoria reclassificada` == 'Não ocupado'"

    # Se um nome de recurso for informado, adiciona a trava da linha
    if nome_do_recurso:
        query_str += " and `Original Line` == @nome_do_recurso"

    base = base.query(query_str)

    base = base[
        [
            "Original Line",
            "Categoria original",
            "Categoria reclassificada",
            "Hora de início",
            "Hora de Fim",
            "Bottleneck Duration Minutes",
            "Process Order",
            "Comentário"
        ]
    ]
    base['Comentário'] = base['Comentário'].fillna('sem comentários')
    return (base, base["Bottleneck Duration Minutes"].count())


import pandas as pd


def extrair_parada_planejada_com_comentario_suspeito(planilha: str, nome_do_recurso: str = None):
    base = pd.read_excel(planilha, engine="openpyxl")

    # 1. Trata valores nulos logo no início
    base['Comentário'] = base['Comentário'].fillna('sem comentários')

    # 2. Regex sem parênteses (evita avisos de 'match groups' no pandas)
    lista_de_paradas_suspeitas = r'quebr|urgên|urgen|vazam|imprevist|falha|trav|estour|emergên|emergen|repent|corretiv|queim'

    # 3. Cria as condições de filtro
    condicao_categoria = base['Categoria reclassificada'] == 'Paradas planejadas'
    condicao_suspeita = base['Comentário'].str.lower().str.contains(lista_de_paradas_suspeitas, regex=True, na=False)

    mask_final = condicao_categoria & condicao_suspeita

    # 4. Adiciona a trava por linha/recurso se informada
    if nome_do_recurso:
        mask_final = mask_final & (base['Original Line'] == nome_do_recurso)

    colunas_desejadas = [
        "Original Line",
        "Categoria original",
        "Categoria reclassificada",
        "Hora de início",
        "Hora de Fim",
        "Bottleneck Duration Minutes",
        "Process Order",
        "Comentário"
    ]

    # 5. Aplica o filtro e seleciona as colunas
    resultado = base.loc[mask_final, colunas_desejadas]

    return (resultado, resultado["Bottleneck Duration Minutes"].count())