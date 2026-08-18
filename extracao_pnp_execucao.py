import re
import pandas as pd

# Colunas estritamente necessárias para o projeto
COLUNAS_PROJETO = [
    "Original Line",
    "Categoria original",
    "Categoria reclassificada",
    "Hora de início",
    "Data de início",
    "Bottleneck Duration Minutes",
    "Process Order",
    "Comentário",
    "AMM Work Order",
    "Motivo reclassificado"
]


def carregar_dataframe(fonte) -> pd.DataFrame:
    """Função auxiliar: se 'fonte' for caminho (str), lê o Excel otimizado.

    Se já for DataFrame, apenas o retorna.
    """
    if isinstance(fonte, pd.DataFrame):
        return fonte

    # Lê apenas as colunas necessárias e usa engine Rust/calamine para ultra performance
    return pd.read_excel(fonte, engine="calamine", usecols=COLUNAS_PROJETO)


def extrair_linhas(fonte):
    base = carregar_dataframe(fonte)
    return base["Original Line"].dropna().unique().tolist()


def total_de_eventos_de_paradas(fonte):
    base = carregar_dataframe(fonte)
    return len(base)


def extrair_pnp_reclassifica_para_tempo_em_producao(
    fonte, nome_do_recurso: str = None
):
    base = carregar_dataframe(fonte)

    mask = (base["Categoria original"] == "Paradas não planejadas") & (
        base["Categoria reclassificada"] == "Tempo de produção"
    )

    if nome_do_recurso:
        mask &= base["Original Line"] == nome_do_recurso

    resultado = base.loc[mask, COLUNAS_PROJETO].copy()
    resultado["Comentário"] = resultado["Comentário"].fillna("sem comentários")

    return (resultado, resultado["Bottleneck Duration Minutes"].count())


def extrair_pnp_reclassifica_para_tempo_ocioso(
    fonte, nome_do_recurso: str = None
):
    base = carregar_dataframe(fonte)

    mask = (base["Categoria original"] == "Paradas não planejadas") & (
        base["Categoria reclassificada"] == "Não ocupado"
    )

    if nome_do_recurso:
        mask &= base["Original Line"] == nome_do_recurso

    resultado = base.loc[mask, COLUNAS_PROJETO].copy()
    resultado["Comentário"] = resultado["Comentário"].fillna("sem comentários")

    return (resultado, resultado["Bottleneck Duration Minutes"].count())


def extrair_pp_reclassifica_para_tempo_ocioso(
    fonte, nome_do_recurso: str = None
):
    base = carregar_dataframe(fonte)

    mask = (base["Categoria original"] == "Paradas planejadas") & (
        base["Categoria reclassificada"] == "Não ocupado"
    )

    if nome_do_recurso:
        mask &= base["Original Line"] == nome_do_recurso

    resultado = base.loc[mask, COLUNAS_PROJETO].copy()
    resultado["Comentário"] = resultado["Comentário"].fillna("sem comentários")

    return (resultado, resultado["Bottleneck Duration Minutes"].count())


def extrair_parada_planejada_com_comentario_suspeito(
    fonte, nome_do_recurso: str = None
):
    base = carregar_dataframe(fonte)

    lista_de_paradas_suspeitas = r"\b(?:quebr|urgên|urgen|vazam|imprevist|falha|trav|estour|emergên|emergen|repent|corretiv|queim|defeit|barulh|ruid|estral|aquec|esquent|fumac|ping|empac|fura|trinc|rasg|rach|desgast|desalinh|desregul|emperr|fuga|folga|vibra|oscil|consert|repar|desentup|desobstru|gambiarra|socorr|entup|acumul|embuch|engargal|enrosc|preso|caid|tombad|chamad|solicit|chamei|avisa)\b"

    cond_categoria = (
        base["Categoria reclassificada"] == "Paradas planejadas"
    ) | (base["Categoria original"] == "Paradas planejadas")

    comentarios = base["Comentário"].fillna("sem comentários").astype(str)
    cond_suspeita = comentarios.str.lower().str.contains(
        lista_de_paradas_suspeitas, regex=True, na=False
    )

    mask = cond_categoria & cond_suspeita

    if nome_do_recurso:
        mask &= base["Original Line"] == nome_do_recurso

    resultado = base.loc[mask, COLUNAS_PROJETO].copy()
    resultado["Comentário"] = resultado["Comentário"].fillna("sem comentários")

    return (resultado, resultado["Bottleneck Duration Minutes"].count())

def extrair_tempo_em_execucao_com_comentario(fonte, nome_do_recurso: str = None):
    base = carregar_dataframe(fonte)
    base['Comentário']=base['Comentário'].fillna('').astype(str).str.strip()
    comentarios_invalidos =["", ".", "-", "sem comentários", "sem comentario"]
    condicao_categoria = base['Categoria reclassificada'] == 'Tempo de produção'
    condicao_comentario = ~base['Comentário'].str.lower().isin(comentarios_invalidos)& (base['Comentário'].str.len()>1)
    mask_final = condicao_categoria & condicao_comentario
    if nome_do_recurso:
        mask_final = mask_final & (base["Original Line"] == nome_do_recurso)
    resultado = base.loc[mask_final]
    return(resultado, resultado["Bottleneck Duration Minutes"].count())

def extrair_parada_tecnica_sem_amm(fonte, nome_do_recurso: str = None):
    base = carregar_dataframe(fonte)
    base['AMM Work Order']=base['AMM Work Order'].fillna('sem ordem')
    motivos=[
        'Manut Corret Elétrica/Autom/Instrum',
        'Pequena Parada Técnica',
        'Manutenção Corret. Mec. de Embalagem',
        'Manutenção Corret. Mecânica geral',
        'Manut Planejada Mec Geral',
        'Manut. Planej. Autônoma',
        'Manut. Planej. Técnica Elétrica Automação',
        'Manut. Planej. Técnica Mecânica',
        'Manut. Planej. Técnica Mecânica de Embalagem'

    ]
    query_str="`Motivo reclassificado` in @motivos and `AMM Work Order`=='sem ordem'"
    if nome_do_recurso:
        query_str +='and `Original Line` == @nome_do_recurso'
    base=base.query(query_str)
    return (base,base["Bottleneck Duration Minutes"].count())

def extrair_tempo_ocioso_com_comentario_suspeito(fonte, nome_do_recurso: str = None):
    base = carregar_dataframe(fonte)
    base['Comentário'] = base['Comentário'].fillna('').astype(str).str.strip()
    lista_de_ocioso_suspeito = r"\b(?:quebr|urgên|urgen|vazam|imprevist|falha|trav|estour|emergên|emergen|repent|corretiv|queim|defeit|barulh|ruid|estral|aquec|esquent|fumac|ping|empac|fura|trinc|rasg|rach|desgast|desalinh|desregul|emperr|fuga|folga|vibra|oscil|consert|repar|desentup|desobstru|gambiarra|socorr|entup|acumul|embuch|engargal|enrosc|preso|caid|tombad|chamad|solicit|chamei|avisa|limpez|limp|geral|intermediar|setup|set up|set-up|troca|regulag|preventiv|lubrific|inspec|inspeç|aferic|aferição|calibr|sanitiz|cip|sanitize|organiz|5s|manutenc|manutenç)\b"
    condicao_categoria = base["Categoria reclassificada"] == "Não ocupado"

    # Força a conversão para minúsculo antes de aplicar a regex
    condicao_suspeita = (
        base["Comentário"]
        .astype(str)
        .str.lower()
        .str.contains(lista_de_ocioso_suspeito, regex=True, na=False)
    )

    mask_final = condicao_categoria & condicao_suspeita

    # 4. Adiciona a trava por linha/recurso se informada
    if nome_do_recurso:
        mask_final = mask_final & (base["Original Line"] == nome_do_recurso)
    resultado = base.loc[mask_final]

    return (resultado, resultado["Bottleneck Duration Minutes"].count())
