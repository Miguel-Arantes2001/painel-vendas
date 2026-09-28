"""Metricas da secao 5 e estatistica descritiva da secao 6 do planejamento."""

from __future__ import annotations

import pandas as pd


MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def formatar_reais(valor: float) -> str:
    inteiro = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {inteiro}"


def formatar_pct(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def formatar_mes(data) -> str:
    return f"{MESES_PT[data.month - 1]}/{data.year}"


def kpis_gerais(df: pd.DataFrame) -> dict:
    """Cartoes do topo: faturamento, lucro, margem, ticket medio e volume."""
    if df.empty:
        return dict.fromkeys(
            ["faturamento", "lucro", "margem", "ticket_medio", "vendas", "itens", "avaliacao"], 0.0
        )

    faturamento = df["Valor_Total"].sum()
    lucro = df["Lucro"].sum()
    return {
        "faturamento": faturamento,
        "lucro": lucro,
        # Margem consolidada = lucro/receita da carteira, nao a media das margens.
        "margem": lucro / faturamento if faturamento else 0.0,
        "ticket_medio": faturamento / len(df),
        "vendas": len(df),
        "itens": int(df["Quantidade"].sum()),
        "avaliacao": df["Avaliacao_Cliente"].mean(),
    }


def serie_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Pergunta 1: evolucao do faturamento e do lucro ao longo dos meses."""
    if df.empty:
        return pd.DataFrame(columns=["Ano_Mes", "Faturamento", "Lucro", "Vendas", "Margem", "Ticket_Medio"])

    mensal = (
        df.groupby("Ano_Mes")
        .agg(Faturamento=("Valor_Total", "sum"), Lucro=("Lucro", "sum"), Vendas=("ID_Venda", "count"))
        .reset_index()
        .sort_values("Ano_Mes")
    )
    mensal["Margem"] = mensal["Lucro"] / mensal["Faturamento"]
    mensal["Ticket_Medio"] = mensal["Faturamento"] / mensal["Vendas"]
    mensal["Variacao_Faturamento"] = mensal["Faturamento"].pct_change()
    return mensal


def por_dimensao(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Perguntas 2 e 3: receita, lucro, margem e ticket por regiao/estado/categoria/produto."""
    colunas = ["Faturamento", "Lucro", "Vendas", "Itens", "Margem", "Ticket_Medio", "Lucro_Medio"]
    if df.empty:
        return pd.DataFrame(columns=[coluna, *colunas])

    agrupado = (
        df.groupby(coluna)
        .agg(
            Faturamento=("Valor_Total", "sum"),
            Lucro=("Lucro", "sum"),
            Vendas=("ID_Venda", "count"),
            Itens=("Quantidade", "sum"),
        )
        .reset_index()
    )
    agrupado["Margem"] = agrupado["Lucro"] / agrupado["Faturamento"]
    agrupado["Ticket_Medio"] = agrupado["Faturamento"] / agrupado["Vendas"]
    agrupado["Lucro_Medio"] = agrupado["Lucro"] / agrupado["Vendas"]
    return agrupado.sort_values("Faturamento", ascending=False)


def estatistica_descritiva(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Secao 6: media, mediana, desvio padrao, minimo/maximo e quartis."""
    if df.empty:
        return pd.DataFrame()

    resumo = df[colunas].agg(["mean", "median", "std", "min", "max"]).T
    quartis = df[colunas].quantile([0.25, 0.75]).T
    resumo["Q1"] = quartis[0.25]
    resumo["Q3"] = quartis[0.75]
    resumo["IQR"] = resumo["Q3"] - resumo["Q1"]
    resumo = resumo.rename(
        columns={
            "mean": "Media",
            "median": "Mediana",
            "std": "Desvio_Padrao",
            "min": "Minimo",
            "max": "Maximo",
        }
    )
    return resumo[["Media", "Mediana", "Desvio_Padrao", "Minimo", "Q1", "Q3", "Maximo", "IQR"]]
