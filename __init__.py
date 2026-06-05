import streamlit as st
import pandas as pd
import plotly.express as px

from utils.filtros import cargar_datos

# Mapeo ciudad de origen → país
CIUDAD_PAIS = {
    'SHANGHAI': 'China', 'NINGBO': 'China', 'SHENZHEN': 'China',
    'CHONGQING': 'China', 'QINGDAO': 'China', 'GUANGZHOU': 'China',
    'XIAMEN': 'China', 'YANTIAN': 'China', 'HONG KONG': 'China',
    'MIAMI': 'Estados Unidos', 'PORT EVERGLADES': 'Estados Unidos',
    'BARCELONA': 'España', 'MADRID': 'España',
    'MILAN': 'Italia', 'GENOVA': 'Italia',
    'HAMBURGO': 'Alemania', 'FRANKFURT': 'Alemania', 'DUSSELDORF': 'Alemania',
    'LONDON GATEWAY (PUERTO)': 'Reino Unido',
    'Le havre': 'Francia', 'PARIS': 'Francia',
    'CHENNAI': 'India', 'NHAVA SHEVA': 'India', 'MUMBAI': 'India', 'ENNORE': 'India',
    'KARACHI': 'Pakistán',
    'SANTOS': 'Brasil', 'VIRACOPOS': 'Brasil',
    'ESTAMBUL': 'Turquía', 'ISTANBUL': 'Turquía',
    'BUSAN': 'Corea del Sur',
    'CALLAO': 'Perú',
    'ANTWERP': 'Bélgica',
    'KAOHSIUNG': 'Taiwán', 'KEELUNG': 'Taiwán',
}

try:
    _, df = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo: data/datos_finales.parquet")
    st.stop()

df = df.copy()
df['Pais'] = df['Origen_x'].map(CIUDAD_PAIS).fillna('Otros')
 
# ─── ESTILOS ──────────────────────────────────────────────────
css = """
<style>
    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #cbd5e1;
        margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 6px;
    }
    .insight-box {
        background: #1e293b; border-left: 4px solid #1D9E75;
        border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    }
    .insight-box p { color: #e2e8f0; margin: 0; font-size: 0.92rem; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)
 
BG = "#e6e9f0"
FONT = '#e2e8f0'
PALETTE = [
    '#1D9E75','#3b82f6','#f59e0b','#ef4444','#a78bfa',
    '#f97316','#06b6d4','#84cc16','#ec4899','#64748b',
]
 
# ─── TÍTULO ───────────────────────────────────────────────────
st.title("Análisis por País de Origen")
st.caption("Importaciones MDE · AIO / FCLI / LCLI / AIM · Compras efectivas · 2022–2026")
 
# ─── SIDEBAR: FILTROS ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtros")
    años_disp = sorted(df['Año'].dropna().unique().astype(int))
    años_sel = st.multiselect("Años", años_disp, default=años_disp)
 
    paises_disp = sorted(df['Pais'].unique())
    paises_sel = st.multiselect(
        "Países (dejar vacío = todos)",
        paises_disp, default=[],
        help="Si no seleccionas ninguno, se muestran todos"
    )
 
df_f = df[df['Año'].isin(años_sel)].copy()
if paises_sel:
    df_f = df_f[df_f['Pais'].isin(paises_sel)]
 
# ─── KPIs ─────────────────────────────────────────────────────
total_ops = len(df_f)
total_paises = df_f['Pais'].nunique()
pais_top = df_f['Pais'].value_counts().idxmax() if total_ops > 0 else '-'
pais_top_n = df_f['Pais'].value_counts().max() if total_ops > 0 else 0
pct_top = round(pais_top_n / total_ops * 100, 1) if total_ops > 0 else 0
 
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.metric("Operaciones en período", f"{total_ops:,}")
with c2:
    with st.container(border=True):
        st.metric("Países de origen", f"{total_paises}")
with c3:
    with st.container(border=True):
        st.metric("País dominante", pais_top, delta=f"{pct_top}% del total")
 
st.markdown("<br>", unsafe_allow_html=True)
 
# ─── GRÁFICO 1: TOP PAÍSES (BARRAS HORIZONTALES) ──────────────
st.markdown('<div class="section-title">Top países por volumen de operaciones</div>', unsafe_allow_html=True)
 
top_paises = (
    df_f.groupby('Pais')['FileID'].count()
    .reset_index().rename(columns={'FileID': 'Operaciones'})
    .sort_values('Operaciones', ascending=True)
)
top_paises['Pct'] = (top_paises['Operaciones'] / top_paises['Operaciones'].sum() * 100).round(1)
top_paises['Label'] = top_paises.apply(lambda r: f"{int(r['Operaciones'])}  ({r['Pct']}%)", axis=1)
 
fig_top = px.bar(
    top_paises, x='Operaciones', y='Pais', orientation='h',
    text='Label',
    color='Operaciones', color_continuous_scale='Teal',
    labels={'Operaciones': 'Operaciones', 'Pais': ''},
)
fig_top.update_traces(textposition='outside', textfont_size=11)
fig_top.update_layout(
    plot_bgcolor=BG, paper_bgcolor=BG, font_color=FONT,
    coloraxis_showscale=False,
    height=max(350, len(top_paises) * 38),
    margin=dict(l=10, r=120, t=10, b=10),
    xaxis=dict(gridcolor='#1e293b'),
)
st.plotly_chart(fig_top, use_container_width=True)
 
st.markdown("<br>", unsafe_allow_html=True)
 
# ─── GRÁFICO 2: TENDENCIA POR AÑO (líneas, top 8 países) ──────
st.markdown('<div class="section-title">Tendencia anual por país (top 8 en volumen)</div>', unsafe_allow_html=True)
st.caption("Se excluye 'Otros' para mayor claridad. Usa el sidebar para filtrar países específicos.")
 
top8 = (
    df_f[df_f['Pais'] != 'Otros']
    .groupby('Pais')['FileID'].count()
    .nlargest(8).index.tolist()
)
df_trend = (
    df_f[df_f['Pais'].isin(top8)]
    .groupby(['Año', 'Pais'])['FileID'].count()
    .reset_index().rename(columns={'FileID': 'Operaciones'})
)
df_trend['Año'] = df_trend['Año'].astype(int)
 
fig_line = px.line(
    df_trend, x='Año', y='Operaciones', color='Pais',
    markers=True,
    color_discrete_sequence=PALETTE,
    labels={'Operaciones': 'Operaciones', 'Año': 'Año', 'Pais': 'País'},
)
fig_line.update_traces(line_width=2.5, marker_size=8)
fig_line.update_layout(
    plot_bgcolor=BG, paper_bgcolor=BG, font_color=FONT,
    height=420,
    legend=dict(
        orientation='v', font=dict(size=11),
        bgcolor="#ffffff", bordercolor="#DBE5F4", borderwidth=1
    ),
    xaxis=dict(gridcolor='#1e293b', dtick=1),
    yaxis=dict(gridcolor='#1e293b'),
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_line, use_container_width=True)
 
# Insight automático
if len(df_trend) > 0:
    ultimo_año = df_trend['Año'].max()
    penultimo_año = ultimo_año - 1
    cambios = []
    for pais in top8:
        ops_u = df_trend[(df_trend['Pais'] == pais) & (df_trend['Año'] == ultimo_año)]['Operaciones'].sum()
        ops_p = df_trend[(df_trend['Pais'] == pais) & (df_trend['Año'] == penultimo_año)]['Operaciones'].sum()
        if ops_p > 0:
            pct = (ops_u - ops_p) / ops_p * 100
            cambios.append((pais, pct, ops_u))
    if cambios:
        mayor_caida = min(cambios, key=lambda x: x[1])
        mayor_subida = max(cambios, key=lambda x: x[1])
        st.markdown(
            '<div class="insight-box"><p>'
            f'Comparando {penultimo_año} vs {ultimo_año}: '
            f'<strong>{mayor_subida[0]}</strong> muestra el mayor crecimiento '
            f'({mayor_subida[1]:+.0f}%), mientras que '
            f'<strong>{mayor_caida[0]}</strong> tuvo la mayor caída '
            f'({mayor_caida[1]:+.0f}%).'
            '</p></div>',
            unsafe_allow_html=True
        )
 
st.markdown("<br>", unsafe_allow_html=True)
 
# ─── GRÁFICO 3: MAPA DE CALOR PAÍS × AÑO ──────────────────────
st.markdown('<div class="section-title">Mapa de calor — operaciones por país y año</div>', unsafe_allow_html=True)
st.caption("Útil para identificar de un vistazo qué países crecen o caen en cada período.")
 
heat_data = (
    df_f[df_f['Pais'] != 'Otros']
    .groupby(['Pais', 'Año'])['FileID'].count()
    .reset_index().rename(columns={'FileID': 'Operaciones'})
)
heat_data['Año'] = heat_data['Año'].astype(int)
heat_pivot = heat_data.pivot_table(index='Pais', columns='Año', values='Operaciones', fill_value=0)
heat_pivot = heat_pivot.loc[heat_pivot.sum(axis=1).sort_values(ascending=False).index]
 
fig_heat = px.imshow(
    heat_pivot,
    color_continuous_scale='Teal',
    text_auto=True,
    aspect='auto',
    labels=dict(x='Año', y='País', color='Operaciones'),
)
fig_heat.update_layout(
    plot_bgcolor=BG, paper_bgcolor=BG, font_color=FONT,
    height=max(300, len(heat_pivot) * 40),
    margin=dict(l=10, r=10, t=10, b=10),
    coloraxis_showscale=False,
)
fig_heat.update_traces(textfont_size=11)
st.plotly_chart(fig_heat, use_container_width=True)
 
st.markdown("<br>", unsafe_allow_html=True)
 
# ─── SECCIÓN: COMERCIAL POR PAÍS ──────────────────────────────

st.markdown('<div class="section-title">Concentración comercial</div>', unsafe_allow_html=True)
com_total = (
    df_f[df_f['Pais'] != 'Otros']
    .groupby('Comercial Reponsable')['FileID'].count()
    .reset_index().rename(columns={'FileID': 'Operaciones', 'Comercial Reponsable': 'Comercial'})
    .sort_values('Operaciones', ascending=False)
    .head(8)
)
fig_com = px.pie(
    com_total, names='Comercial', values='Operaciones',
    color_discrete_sequence=PALETTE,
    hole=0.4,
)
fig_com.update_layout(
    plot_bgcolor=BG, paper_bgcolor=BG, font_color=FONT,
    height=400,
    legend=dict(font=dict(size=9), bgcolor="#f1f1f2"),
    margin=dict(l=10, r=10, t=10, b=10),
)
fig_com.update_traces(textposition='inside', textinfo='percent')
st.plotly_chart(fig_com, use_container_width=True)
st.caption("Top 8 comerciales por total de operaciones internacionales (excl. 'Otros')")

st.markdown('<div class="section-title">Comercial principal por país de origen</div>', unsafe_allow_html=True)
st.caption("El comercial con más operaciones cerradas en ese corredor de importación.")
 

com_pais = (
    df_f[df_f['Pais'] != 'Otros']
    .groupby(['Pais', 'Comercial Reponsable'])['FileID']
    .count().reset_index().rename(columns={'FileID': 'Ops'})
    .sort_values(['Pais', 'Ops'], ascending=[True, False])
)
top_com = com_pais.groupby('Pais').first().reset_index()
top_com.columns = ['Pais', 'Comercial Principal', 'Ops']
total_x_pais = df_f[df_f['Pais'] != 'Otros'].groupby('Pais')['FileID'].count().reset_index()
total_x_pais.columns = ['Pais', 'Total']
top_com = top_com.merge(total_x_pais, on='Pais')
top_com['% del país'] = (top_com['Ops'] / top_com['Total'] * 100).round(1).astype(str) + '%'
top_com = top_com.sort_values('Total', ascending=False)

st.dataframe(
    top_com[['Pais', 'Comercial Principal', 'Ops', 'Total', '% del país']],
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.divider()
 
# ─── TABLA DE DETALLE: CIUDADES ────────────────────────────────
with st.expander("Ver detalle por ciudad de origen"):
    st.caption("Origen_x original del DF — útil para identificar ciudades no mapeadas a país")
    ciudad_detail = (
        df_f.groupby(['Origen_x', 'Pais'])['FileID'].count()
        .reset_index().rename(columns={'FileID': 'Operaciones', 'Origen_x': 'Ciudad'})
        .sort_values('Operaciones', ascending=False)
    )
    st.dataframe(ciudad_detail, use_container_width=True, height=350, hide_index=True)
 
st.markdown("---")
st.markdown("Análisis por País de Origen · Importaciones MDE · 2022–2026")
 
