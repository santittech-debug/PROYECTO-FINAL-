import pandas as pd
import streamlit as st

RUTA_DATOS = "data/datos_finales.parquet"

SERVICIOS = [
    "Importación Aérea (AIO)",
    "Full Container Load Impo (FCLI)",
    "Less Container Load Impo (LCLI)",
    "Importación Aérea Miami (AIM)",
]
ESTADOS = [
    "4. Carga en Destino", "7. Carga en Destino",
    "5. Carga liberada", "Terminado", "Facturacion",
]


@st.cache_data
def cargar_raw():
    """Lee el parquet completo (todas las sedes / servicios)."""
    return pd.read_parquet(RUTA_DATOS)


@st.cache_data
def cargar_datos():
    """Devuelve (df_f, ops):

    - df_f: filas filtradas a Importaciones MDE con estados efectivos.
    - ops:  operaciones únicas por FileID (una fila por operación).
    """
    df = cargar_raw()
    df_f = df[
        df["Servicio"].isin(SERVICIOS)
        & df["StatusNegocio"].isin(ESTADOS)
        & df["FileID"].str.contains("MDE", na=False)
    ].copy()
    df_f["Fecha Inicio"] = pd.to_datetime(df_f["Fecha Inicio"], dayfirst=True, errors="coerce")
    df_f["Año"] = df_f["Fecha Inicio"].dt.year
    df_f["Mes"] = df_f["Fecha Inicio"].dt.month
    ops = df_f.drop_duplicates(subset="FileID").copy()
    return df_f, ops


@st.cache_data
def kpis_globales():
    """KPIs históricos sobre TODO el dataset (todas las sedes y servicios)."""
    df = cargar_raw()
    fechas = pd.to_datetime(df["Fecha Inicio"], dayfirst=True, errors="coerce")
    años = sorted(fechas.dt.year.dropna().astype(int).unique().tolist())
    return {
        "total_ops": int(df["FileID"].nunique()),
        "total_clientes": int(df["Cliente"].nunique()),
        "años": años,
    }


def estadisticas_clientes(ops, hoy=None):
    """Estadísticas de compra por cliente a partir de las operaciones únicas."""
    if hoy is None:
        hoy = pd.Timestamp.today().normalize()
    cs = ops.groupby("Cliente").agg(
        total_compras=("FileID", "count"),
        ultima_compra=("Fecha Inicio", "max"),
        primera_compra=("Fecha Inicio", "min"),
    ).reset_index()
    cs["dias_inactivo"] = (hoy - cs["ultima_compra"]).dt.days
    return cs
