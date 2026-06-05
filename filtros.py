import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
 
from utils.filtros import cargar_datos

st.title("Desempeño Comercial")

# ESTILOS
css = """
<style>
    .metric-card {
        background: #666;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #f1f5f9; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }
    .alert-red { border-left-color: #ef4444 !important; }
    .alert-yellow { border-left-color: #f59e0b !important; }
    .alert-green { border-left-color: #10b981 !important; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 8px;
        border-bottom: 1px solid #334155;
        padding-bottom: 6px;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("Parámetros")
    umbral_inactividad = st.slider(
        "Umbral inactividad cliente (días)", 90, 365, 180, step=30,
        help="Clientes con más días sin comprar se consideran en riesgo"
    )
    anos_disponibles = [2022, 2023, 2024, 2025, 2026]
    anos_sel = st.multiselect("Filtrar años", anos_disponibles, default=anos_disponibles)

 
# CARGA
try:
    df_full, ops = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo en: data/datos_finales.parquet")
    st.stop()
 
ops = ops[ops["Año"].isin(anos_sel)]
hoy = pd.Timestamp("2026-06-01")
 
# METRICAS GLOBALES
st.title("Dashboard Riesgo - Medellin Importaciones")
st.caption("Filtros: AIO · FCLI · LCLI · AIM | Estados efectivos | Ciudad MDE | 2022-2026")
 
total_ops = len(ops)
total_clientes = ops["Cliente"].nunique()
total_comerciales = ops["Comercial Reponsable"].nunique()
 
client_stats = ops.groupby("Cliente").agg(
    total_compras=("FileID", "count"),
    ultima_compra=("Fecha Inicio", "max"),
    primera_compra=("Fecha Inicio", "min"),
).reset_index()
client_stats["dias_inactivo"] = (hoy - client_stats["ultima_compra"]).dt.days
activos = client_stats[client_stats["dias_inactivo"] <= umbral_inactividad]
 
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(
        '<div class="metric-card"><div class="metric-value">' + str(round(total_ops/1000, 1)) + '</div>'
        '<div class="metric-label">Operaciones totales <br> en Miles</div></div>',
        unsafe_allow_html=True)
with c2:
    st.markdown(
        '<div class="metric-card"><div class="metric-value">' + str(total_clientes) + '</div>'
        '<div class="metric-label">Clientes <br> únicos</div></div>',
        unsafe_allow_html=True)
with c3:
    st.markdown(
        '<div class="metric-card alert-green"><div class="metric-value">' + str(len(activos)) + '</div>'
        '<div class="metric-label">Clientes <br> activos</div></div>',
        unsafe_allow_html=True)
with c4:
    st.markdown(
        '<div class="metric-card alert-red"><div class="metric-value">' + str(total_clientes - len(activos)) + '</div>'
        '<div class="metric-label">Clientes en riesgo/<br> perdidos</div></div>',
        unsafe_allow_html=True)
with c5:
    st.markdown(
        '<div class="metric-card"><div class="metric-value">' + str(total_comerciales) + '</div>'
        '<div class="metric-label">Comerciales <br> activos</div></div>',
        unsafe_allow_html=True)
 
st.markdown("<br>", unsafe_allow_html=True)
 
# PESTANAS
tab1, tab3, tab4 = st.tabs(
    ["Comerciales", "Frecuencia de Compra", "Explorar Datos"]
)
 
# ─── TAB 1: COMERCIALES ───
with tab1:
    st.markdown('<div class="section-title">Ventas por Comercial por Año — Medellín (menor a mayor total)</div>', unsafe_allow_html=True)
 
    tabla_com = ops.groupby(["Comercial Reponsable", "Año"])["FileID"].count().reset_index()
    tabla_com.columns = ["Comercial", "Año", "Ventas"]
    pivot = tabla_com.pivot_table(index="Comercial", columns="Año", values="Ventas", fill_value=0)
    pivot.columns = [str(int(c)) for c in pivot.columns]
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=True).reset_index()
 
    def badge(v):
        if v <= 5:
            return "BAJO"
        elif v <= 15:
            return "MEDIO"
        else:
            return "ALTO"
 
    pivot["Nivel"] = pivot["Total"].apply(badge)
 
    st.dataframe(
        pivot[["Nivel", "Comercial"] + [c for c in pivot.columns if c not in ["Comercial", "Nivel"]]],
        use_container_width=True,
        height=420,
    )
    st.caption("BAJO = 5 o menos ventas | MEDIO = 6-15 | ALTO = más de 15")
 
    col_a, col_b = st.columns(2)
 
    with col_a:
        st.markdown('<div class="section-title">Ventas totales por comercial</div>', unsafe_allow_html=True)
        fig_bar = px.bar(
            pivot.sort_values("Total"),
            x="Total", y="Comercial", orientation="h",
            color="Total", color_continuous_scale="Blues",
            text="Total", labels={"Total": "Operaciones", "Comercial": ""},
        )
        fig_bar.update_layout(
            plot_bgcolor="#dbdfe6", paper_bgcolor="#dbdfe6",
            font_color="#e2e8f0", coloraxis_showscale=False,
            height=520, margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)
 
    with col_b:
        st.markdown('<div class="section-title">Evolución anual (top 10 comerciales)</div>', unsafe_allow_html=True)
        top10_com = pivot.nlargest(10, "Total")["Comercial"].tolist()
        df_evol = tabla_com[tabla_com["Comercial"].isin(top10_com)]
        fig_line = px.line(
            df_evol, x="Año", y="Ventas", color="Comercial", markers=True,
        )
        fig_line.update_layout(
            plot_bgcolor="#dbdfe6", paper_bgcolor="#dbdfe6",
            font_color="#e2e8f0", height=520,
            legend=dict(font=dict(size=9)),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_line, use_container_width=True)
 
    st.markdown('<div class="section-title">Comerciales de bajo rendimiento (5 o menos ventas totales)</div>', unsafe_allow_html=True)
    bajos = pivot[pivot["Total"] <= 5].sort_values("Total")
    if len(bajos):
        cols_mostrar = ["Comercial", "Total"] + [c for c in bajos.columns if c.isdigit()]
        st.dataframe(bajos[cols_mostrar], use_container_width=True)
        st.info(str(len(bajos)) + " comerciales con 5 o menos operaciones en todo el período.")
    else:
        st.success("No hay comerciales con 5 o menos ventas en el período seleccionado.")
 
 

 
 
# ─── TAB 3: FRECUENCIA DE COMPRA ───
with tab3:
    st.markdown('<div class="section-title">Frecuencia de recompra entre operaciones</div>', unsafe_allow_html=True)
 
    ops_sorted = ops.sort_values(["Cliente", "Fecha Inicio"]).copy()
    ops_sorted["prev_fecha"] = ops_sorted.groupby("Cliente")["Fecha Inicio"].shift(1)
    ops_sorted["gap_dias"] = (ops_sorted["Fecha Inicio"] - ops_sorted["prev_fecha"]).dt.days
    gaps = ops_sorted.dropna(subset=["gap_dias"]).copy()
 
    def segmento(d):
        if d <= 90:
            return "1-3 meses (activo)"
        elif d <= 150:
            return "4-5 meses (alerta)"
        else:
            return "6+ meses (riesgo)"
 
    gaps["Segmento"] = gaps["gap_dias"].apply(segmento)
    freq_df = gaps["Segmento"].value_counts(normalize=True).mul(100).round(1).reset_index()
    freq_df.columns = ["Segmento", "Porcentaje"]
 
    col_f1, col_f2 = st.columns(2)
 
    with col_f1:
        fig_freq = px.bar(
            freq_df, x="Segmento", y="Porcentaje", color="Segmento",
            color_discrete_map={
                "1-3 meses (activo)": "#10b981",
                "4-5 meses (alerta)": "#f59e0b",
                "6+ meses (riesgo)": "#ef4444",
            },
            text="Porcentaje", labels={"Porcentaje": "%"},
        )
        fig_freq.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_freq.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="#e2e8f0", showlegend=False,
            height=380, margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_freq, use_container_width=True)
 
    with col_f2:
        st.markdown('<div class="section-title">Compras por mes del año (estacionalidad)</div>', unsafe_allow_html=True)
        estac = ops.groupby("Mes")["FileID"].count().reset_index()
        estac.columns = ["Mes", "Operaciones"]
        meses_nombre = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        estac["Mes_Nombre"] = estac["Mes"].map(meses_nombre)
        fig_est = px.bar(
            estac, x="Mes_Nombre", y="Operaciones",
            color="Operaciones", color_continuous_scale="Blues", text="Operaciones",
        )
        fig_est.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            font_color="#e2e8f0", coloraxis_showscale=False,
            height=380, margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_est, use_container_width=True)
 
    st.markdown('<div class="section-title">Operaciones por año y tipo de servicio</div>', unsafe_allow_html=True)
    by_servicio = ops.groupby(["Año", "Servicio"])["FileID"].count().reset_index()
    by_servicio.columns = ["Año", "Servicio", "Operaciones"]
    fig_sv = px.bar(
        by_servicio, x="Año", y="Operaciones", color="Servicio",
        barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_sv.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#e2e8f0", height=350,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_sv, use_container_width=True)
 
 
# ─── TAB 4: EXPLORAR DATOS ───
with tab4:
    st.markdown('<div class="section-title">Datos filtrados — operaciones únicas (FileID)</div>', unsafe_allow_html=True)
 
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        filtro_comercial = st.selectbox(
            "Filtrar por comercial",
            ["Todos"] + sorted(ops["Comercial Reponsable"].dropna().unique().tolist()),
        )
    with col_s2:
        filtro_servicio = st.selectbox(
            "Filtrar por servicio",
            ["Todos"] + sorted(ops["Servicio"].dropna().unique().tolist()),
        )
 
    vista = ops.copy()
    if filtro_comercial != "Todos":
        vista = vista[vista["Comercial Reponsable"] == filtro_comercial]
    if filtro_servicio != "Todos":
        vista = vista[vista["Servicio"] == filtro_servicio]
 
    st.dataframe(
        vista[["FileID", "Cliente", "Servicio", "Fecha Inicio", "StatusNegocio", "Comercial Reponsable", "Año"]]
        .sort_values("Fecha Inicio", ascending=False),
        use_container_width=True, height=450,
    )
    st.caption("Mostrando " + str(len(vista)) + " operaciones")
 
 
# FOOTER
st.markdown("---")
st.markdown("Dashboard Riesgo MDE · Filtros: Importaciones AIO/FCLI/LCLI/AIM · Ciudad MDE · Estados efectivos")
