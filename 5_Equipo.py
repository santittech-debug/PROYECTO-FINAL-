import streamlit as st
import pandas as pd
import plotly.express as px

from utils.filtros import cargar_datos, estadisticas_clientes

st.title("Clientes en Riesgo — Medellín")

# ─── CARGA DE DATOS ───────────────────────────────────────────
try:
    df_f, ops = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo en: data/datos_finales.parquet")
    st.stop()

# ─── PARÁMETROS ───────────────────────────────────────────────
with st.sidebar:
    st.title("Parámetros")
    umbral_inactividad = st.slider(
        "Umbral inactividad cliente (días)", 90, 365, 180, step=30,
        help="Clientes con más días sin comprar se consideran en riesgo"
    )

hoy = pd.Timestamp.today().normalize()
client_stats = estadisticas_clientes(ops, hoy)

# ─── CLIENTES EN RIESGO ───────────────────────────────────────
st.markdown(
    '<div style="font-size:1.1rem;font-weight:600;color:#cbd5e1;'
    'border-bottom:1px solid #334155;padding-bottom:6px;margin-bottom:8px;">'
    'Clientes activos ordenados por riesgo de fuga</div>',
    unsafe_allow_html=True,
)

ultimo_comercial = (
    ops.sort_values("Fecha Inicio")
    .groupby("Cliente")["Comercial Reponsable"].last()
    .reset_index()
    .rename(columns={"Comercial Reponsable": "Ultimo Comercial"})
)
servicios_cliente = (
    ops.groupby("Cliente")["Servicio"]
    .agg(lambda x: ", ".join(sorted(x.unique())))
    .reset_index()
    .rename(columns={"Servicio": "Servicios Usados"})
)

tabla_riesgo = client_stats.merge(ultimo_comercial, on="Cliente").merge(servicios_cliente, on="Cliente")


def nivel_riesgo(d):
    if d <= 90:
        return "Bajo"
    elif d <= umbral_inactividad:
        return "Medio"
    elif d <= umbral_inactividad * 1.5:
        return "Alto"
    else:
        return "Perdido"


tabla_riesgo["Riesgo"] = tabla_riesgo["dias_inactivo"].apply(nivel_riesgo)
tabla_riesgo["Ultima Compra"] = tabla_riesgo["ultima_compra"].dt.strftime("%d/%m/%Y")

solo_activos = tabla_riesgo[tabla_riesgo["dias_inactivo"] <= umbral_inactividad].sort_values(
    "dias_inactivo", ascending=False
)

st.dataframe(
    solo_activos[[
        "Riesgo", "Cliente", "total_compras", "dias_inactivo",
        "Ultima Compra", "Ultimo Comercial", "Servicios Usados"
    ]].rename(columns={
        "total_compras": "Num Compras",
        "dias_inactivo": "Dias sin comprar",
    }),
    use_container_width=True, height=380,
)

col_r1, col_r2 = st.columns(2)

with col_r1:
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:600;color:#cbd5e1;'
        'margin-bottom:8px;">Dias inactivo vs historial de compras</div>',
        unsafe_allow_html=True,
    )
    if len(solo_activos):
        fig_scatter = px.scatter(
            solo_activos, x="dias_inactivo", y="total_compras",
            text="Cliente", color="Riesgo",
            color_discrete_map={"Bajo": "#10b981", "Medio": "#f59e0b", "Alto": "#f97316", "Perdido": "#ef4444"},
            labels={"dias_inactivo": "Dias sin comprar", "total_compras": "Num Compras"},
            size="total_compras", size_max=30,
        )
        fig_scatter.update_traces(textposition="top center", textfont_size=8)
        fig_scatter.add_vline(
            x=umbral_inactividad, line_dash="dash", line_color="#ef4444",
            annotation_text="Umbral " + str(umbral_inactividad) + "d",
        )
        fig_scatter.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="#e2e8f0", height=400,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No hay clientes activos dentro del umbral seleccionado.")

with col_r2:
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:600;color:#cbd5e1;'
        'margin-bottom:8px;">Distribucion de clientes por nivel de riesgo</div>',
        unsafe_allow_html=True,
    )
    riesgo_counts = tabla_riesgo["Riesgo"].value_counts().reset_index()
    riesgo_counts.columns = ["Riesgo", "Clientes"]
    fig_pie = px.pie(
        riesgo_counts, names="Riesgo", values="Clientes", color="Riesgo",
        color_discrete_map={"Bajo": "#10b981", "Medio": "#f59e0b", "Alto": "#f97316", "Perdido": "#ef4444"},
        hole=0.45,
    )
    fig_pie.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#e2e8f0", height=400,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown(
    '<div style="font-size:1.1rem;font-weight:600;color:#cbd5e1;'
    'margin-bottom:8px;">Top 10 clientes con mayor riesgo de fuga (activos)</div>',
    unsafe_allow_html=True,
)
top10_riesgo = solo_activos.nlargest(10, "dias_inactivo")[
    ["Riesgo", "Cliente", "total_compras", "dias_inactivo", "Ultimo Comercial"]
].rename(columns={"total_compras": "Num Compras", "dias_inactivo": "Dias sin comprar"})
st.dataframe(top10_riesgo, use_container_width=True)
