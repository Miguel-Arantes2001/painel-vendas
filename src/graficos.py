"""Os tres graficos do rascunho (secao 8) com a paleta da secao 9.

Paleta com significado fixo:
  azul     -> faturamento / valor principal
  verde    -> lucro / positivo
  vermelho -> alerta (abaixo da meta de margem)
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .kpis import formatar_mes

AZUL = "#1F4E79"
VERDE = "#2E8B57"
VERMELHO = "#C0392B"
CINZA = "#7F8C8D"

_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, Arial", size=13, color="#2C3E50"),
    margin=dict(l=10, r=10, t=60, b=10),
    hoverlabel=dict(font_size=12),
    title_font=dict(size=16, color=AZUL),
    # Legenda no rodape: no topo ela disputa espaco com o titulo do grafico.
    legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, title=None),
)


def evolucao_mensal(mensal: pd.DataFrame) -> go.Figure:
    """Pergunta 1: evolucao do faturamento e do lucro ao longo dos meses."""
    rotulos = [formatar_mes(d) for d in mensal["Ano_Mes"]]
    fig = go.Figure()
    for nome, cor in [("Faturamento", AZUL), ("Lucro", VERDE)]:
        fig.add_trace(
            go.Scatter(
                x=mensal["Ano_Mes"], y=mensal[nome], name=nome, customdata=rotulos,
                mode="lines+markers", line=dict(color=cor, width=3), marker=dict(size=7),
                hovertemplate=f"%{{customdata}}<br>{nome}: R$ %{{y:,.2f}}<extra></extra>",
            )
        )
    fig.update_layout(
        **_LAYOUT,
        title="Faturamento e lucro por mês",
        yaxis_title="R$",
        xaxis_title=None,
        hovermode="x unified",
    )
    # Plotly rotula os meses em ingles; aqui o eixo recebe os nomes em portugues.
    fig.update_xaxes(tickmode="array", tickvals=mensal["Ano_Mes"], ticktext=rotulos)
    return fig


def faturamento_e_lucro(dados: pd.DataFrame, dimensao: str, titulo: str) -> go.Figure:
    """Perguntas 2 e 3: comparacao de faturamento e lucro por regiao ou categoria."""
    dados = dados.sort_values("Faturamento")
    fig = go.Figure()
    for nome, cor in [("Lucro", VERDE), ("Faturamento", AZUL)]:
        fig.add_trace(
            go.Bar(
                x=dados[nome], y=dados[dimensao], name=nome, orientation="h", marker_color=cor,
                text=[f"R$ {v:,.0f}".replace(",", ".") for v in dados[nome]],
                textposition="outside", cliponaxis=False,
                hovertemplate=f"%{{y}}<br>{nome}: R$ %{{x:,.2f}}<extra></extra>",
            )
        )
    fig.update_layout(**_LAYOUT, title=titulo, barmode="group", xaxis_title=None, yaxis_title=None)
    # Eixo escondido: o valor ja esta na ponta de cada barra.
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, dados["Faturamento"].max() * 1.25])
    fig.update_layout(height=max(320, 70 * len(dados)))
    return fig
