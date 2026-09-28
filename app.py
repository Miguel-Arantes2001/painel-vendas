
from __future__ import annotations

import pandas as pd
import streamlit as st

from src import graficos as g
from src import kpis as k
from src.dados import carregar

st.set_page_config(page_title="Painel de Vendas", page_icon="📊", layout="wide")

st.markdown(
    f"""
    <style>
      [data-testid="stMetricValue"] {{ font-size: 1.7rem; color: {g.AZUL}; }}
      [data-testid="stMetricLabel"] {{ color: #566573; }}
      h1, h2, h3 {{ color: {g.AZUL}; }}
      .block-container {{ padding-top: 2.2rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Carregando e limpando a base...")
def obter_dados():
    return carregar()


df, qualidade = obter_dados()

# ----------------------------------------------------------------------- FILTROS
st.sidebar.title("Filtros")

data_min, data_max = df["Data_Venda"].min().date(), df["Data_Venda"].max().date()
# Abre no bloco continuo de operacao, ignorando datas soltas que esticariam o eixo.
padrao_inicio, padrao_fim = (d.date() for d in qualidade["periodo_principal"])
periodo = st.sidebar.date_input(
    "Período", value=(padrao_inicio, padrao_fim), min_value=data_min, max_value=data_max
)
inicio, fim = periodo if isinstance(periodo, tuple) and len(periodo) == 2 else (padrao_inicio, padrao_fim)

regioes = st.sidebar.multiselect("Região", sorted(df["Regiao"].unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df["Categoria_Produto"].unique()))
status = st.sidebar.multiselect("Status da venda", sorted(df["Status_Venda"].unique()))

with st.sidebar.expander("Ajustes de dados"):
    excluir_outliers = st.toggle(
        "Excluir outliers (1,5 x IQR)", value=False, help=f"{qualidade['outliers']} registros marcados como outlier."
    )
    excluir_invalidos = st.toggle(
        "Excluir registros inválidos", value=True, help="Vendas com quantidade ou valor zerados."
    )

filtro = df["Data_Venda"].between(pd.Timestamp(inicio), pd.Timestamp(fim))
if regioes:
    filtro &= df["Regiao"].isin(regioes)
if categorias:
    filtro &= df["Categoria_Produto"].isin(categorias)
if status:
    filtro &= df["Status_Venda"].isin(status)
if excluir_outliers:
    filtro &= ~df["eh_outlier"]
if excluir_invalidos:
    filtro &= df["registro_valido"]

dados = df[filtro]

# ------------------------------------------------------------------ KPIS NO TOPO
st.title("Painel de Vendas")

if dados.empty:
    st.warning("Nenhuma venda atende aos filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

m = k.kpis_gerais(dados)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento", k.formatar_reais(m["faturamento"]))
c2.metric("Lucro", k.formatar_reais(m["lucro"]))
c3.metric("Margem de lucro", k.formatar_pct(m["margem"]))
c4.metric("Ticket médio", k.formatar_reais(m["ticket_medio"]))

st.divider()

# --------------------------------------------------------------------- PERGUNTA 1
st.subheader("1. Qual foi a evolução do faturamento e do lucro ao longo dos meses?")
mensal = k.serie_mensal(dados)
st.plotly_chart(g.evolucao_mensal(mensal), width="stretch")

melhor = mensal.loc[mensal["Faturamento"].idxmax()]
pior = mensal.loc[mensal["Faturamento"].idxmin()]
resumo = (
    f"Melhor mês: {k.formatar_mes(melhor.Ano_Mes)} com {k.formatar_reais(melhor.Faturamento)}  •  "
    f"Pior mês: {k.formatar_mes(pior.Ano_Mes)} com {k.formatar_reais(pior.Faturamento)}"
)
# Sem escapar, o Streamlit lê o par de cifroes como formula LaTeX.
st.caption(resumo.replace("$", r"\$"))

st.divider()

# ---------------------------------------------------------------- PERGUNTAS 2 E 3
esquerda, direita = st.columns(2)

with esquerda:
    st.subheader("2. Quais regiões geram maior receita e lucro?")
    por_regiao = k.por_dimensao(dados, "Regiao")
    st.plotly_chart(g.faturamento_e_lucro(por_regiao, "Regiao", "Faturamento e lucro por região"), width="stretch")

with direita:
    st.subheader("3. Quais categorias vendem mais e são mais lucrativas?")
    por_categoria = k.por_dimensao(dados, "Categoria_Produto")
    st.plotly_chart(
        g.faturamento_e_lucro(por_categoria, "Categoria_Produto", "Faturamento e lucro por categoria"),
        width="stretch",
    )

# ------------------------------------------------------ APOIO (fica fora da tela)
with st.expander("Estatística descritiva e qualidade dos dados"):
    st.markdown("**Estatística descritiva** — média, mediana, desvio padrão, mínimo/máximo e quartis.")
    colunas_num = ["Quantidade", "Preco_Unitario", "Valor_Total", "Lucro", "Margem_Lucro", "Avaliacao_Cliente"]
    st.dataframe(k.estatistica_descritiva(dados, colunas_num).style.format("{:,.2f}"), width="stretch")

    st.markdown("**Qualidade dos dados**")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Registros na base", f"{qualidade['linhas']:,}".replace(",", "."))
    q2.metric("Duplicados", qualidade["duplicados"])
    q3.metric("Outliers marcados", qualidade["outliers"])
    q4.metric("Registros inválidos", qualidade["registros_invalidos"] + qualidade["datas_suspeitas"])

    nulos = ", ".join(f"{coluna}: {n}" for coluna, n in qualidade["nulos"].items()) or "nenhum"
    corrigidas = ", ".join(
        f"{coluna} ({antes} → {depois})" for coluna, (antes, depois) in qualidade["variantes_corrigidas"].items()
    )
    st.caption(
        f"Valores nulos — {nulos} (ficam fora do cálculo da média, não viram zero).  \n"
        f"Inconsistência de texto corrigida em {corrigidas} valores distintos."
    )

st.caption("DADO → PERGUNTA → MÉTRICA → VISUAL → DECISÃO")
