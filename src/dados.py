"""Carga e limpeza da base de vendas.

Resolve os problemas mapeados na secao 3 do planejamento (Qualidade dos Dados):
nulos em Avaliacao_Cliente, inconsistencia de texto em colunas categoricas,
outliers em valores numericos e registros invalidos.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_PADRAO = RAIZ / "Vendas_Organizado.xlsx"

COLUNAS_CATEGORICAS = [
    "Regiao",
    "Estado",
    "Cidade",
    "Categoria_Produto",
    "Produto",
    "Vendedor",
    "Canal_Venda",
    "Forma_Pagamento",
    "Status_Venda",
]

COLUNAS_OUTLIER = ["Quantidade", "Preco_Unitario", "Valor_Total", "Lucro"]

ORDEM_MESES = [
    "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _chave(texto: str) -> str:
    """Reduz o texto a uma chave comparavel: sem acento, sem caixa, sem espaco extra."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def _qtd_acentos(texto: str) -> int:
    return sum(1 for c in texto if unicodedata.combining(unicodedata.normalize("NFKD", c)[-1]))


def _canonizar(serie: pd.Series) -> pd.Series:
    """Unifica variantes do mesmo valor ('APLICATIVO', '  Casa  ', 'Acessorios').

    Entre as variantes que compartilham a mesma chave, elege a grafia mais
    frequente. Empate desempata pela presenca de acentos - assim 'PIX' nao vira
    'pix' e 'Acessorios' vira 'Acessorios' com acento.
    """
    limpa = serie.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    frequencia = Counter(limpa.dropna())

    canonicos: dict[str, str] = {}
    for variante, vezes in frequencia.items():
        chave = _chave(variante)
        candidato = (vezes, _qtd_acentos(variante))
        if chave not in canonicos or candidato > canonicos[chave][0]:
            canonicos[chave] = (candidato, variante)

    return limpa.map(lambda v: canonicos[_chave(v)][1] if pd.notna(v) else v)


def _marcar_datas_suspeitas(df: pd.DataFrame) -> pd.Series:
    """Isola datas fora do bloco continuo de operacao.

    A base concentra as vendas num periodo continuo; meses soltos depois de um
    intervalo vazio indicam erro de digitacao e criariam buracos no grafico de
    linha. Aqui eles sao apenas sinalizados, nunca apagados.
    """
    meses = df["Ano_Mes"].dropna().drop_duplicates().sort_values()
    if meses.empty:
        return pd.Series(False, index=df.index)

    ordinais = meses.dt.year * 12 + meses.dt.month
    bloco = (ordinais.diff().fillna(1) > 1).cumsum()

    bloco_da_linha = df["Ano_Mes"].map(dict(zip(meses, bloco)))
    return bloco_da_linha.ne(bloco_da_linha.value_counts().idxmax())


def _marcar_outliers(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Sinaliza outliers pelo criterio de Tukey (1.5 x IQR) sem descartar linhas."""
    for coluna in colunas:
        q1, q3 = df[coluna].quantile([0.25, 0.75])
        iqr = q3 - q1
        df[f"outlier_{coluna}"] = (df[coluna] < q1 - 1.5 * iqr) | (df[coluna] > q3 + 1.5 * iqr)
    df["eh_outlier"] = df[[f"outlier_{c}" for c in colunas]].any(axis=1)
    return df


def carregar_bruto(caminho: str | Path = ARQUIVO_PADRAO) -> pd.DataFrame:
    return pd.read_excel(caminho)


def limpar(bruto: pd.DataFrame) -> pd.DataFrame:
    df = bruto.copy()

    for coluna in COLUNAS_CATEGORICAS:
        df[coluna] = _canonizar(df[coluna])

    df["Data_Venda"] = pd.to_datetime(df["Data_Venda"], errors="coerce")
    df["Ano"] = df["Data_Venda"].dt.year
    df["Ano_Mes"] = df["Data_Venda"].dt.to_period("M").dt.to_timestamp()
    df["Mes_Nome"] = df["Data_Venda"].dt.strftime("%b/%Y")

    df["data_suspeita"] = _marcar_datas_suspeitas(df)

    # Venda concluida com quantidade zerada nao representa receita real.
    df["registro_valido"] = (df["Quantidade"] > 0) & (df["Valor_Total"] > 0)

    # Sem avaliacao != avaliacao ruim: mantem NaN nas metricas e isola numa flag.
    df["Avaliacao_Cliente"] = pd.to_numeric(df["Avaliacao_Cliente"], errors="coerce")
    df["sem_avaliacao"] = df["Avaliacao_Cliente"].isna()

    df = _marcar_outliers(df, COLUNAS_OUTLIER)
    return df


def relatorio_qualidade(bruto: pd.DataFrame, limpo: pd.DataFrame) -> dict:
    """Numeros da secao 3 do planejamento, para exibir no dashboard."""
    variantes = {}
    for coluna in COLUNAS_CATEGORICAS:
        antes = bruto[coluna].nunique()
        depois = limpo[coluna].nunique()
        if antes != depois:
            variantes[coluna] = (antes, depois)

    return {
        "linhas": len(limpo),
        "nulos": bruto.isna().sum()[lambda s: s > 0].to_dict(),
        "duplicados": int(bruto.duplicated().sum()),
        "ids_duplicados": int(bruto["ID_Venda"].duplicated().sum()),
        "variantes_corrigidas": variantes,
        "outliers": int(limpo["eh_outlier"].sum()),
        "outliers_por_coluna": {c: int(limpo[f"outlier_{c}"].sum()) for c in COLUNAS_OUTLIER},
        "registros_invalidos": int((~limpo["registro_valido"]).sum()),
        "datas_suspeitas": int(limpo["data_suspeita"].sum()),
        "periodo_principal": (
            limpo.loc[~limpo["data_suspeita"], "Data_Venda"].min(),
            limpo.loc[~limpo["data_suspeita"], "Data_Venda"].max(),
        ),
        "cardinalidade": {c: int(limpo[c].nunique()) for c in ["ID_Venda", "Data_Venda", *COLUNAS_CATEGORICAS]},
    }


def carregar(caminho: str | Path = ARQUIVO_PADRAO) -> tuple[pd.DataFrame, dict]:
    bruto = carregar_bruto(caminho)
    limpo = limpar(bruto)
    return limpo, relatorio_qualidade(bruto, limpo)
