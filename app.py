import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# CONFIG PAGINA

st.set_page_config(
    page_title="Radar Comercial — Detección de Clientes en Riesgo",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)
pg = st.navigation([
   
   st.Page("pages/1_Vision_General.py", title="Visión General", default=True),
    st.Page("pages/2_Clientes_en_Riesgo.py", title="Clientes en Riesgo"),
    st.Page("pages/3_Comerciales.py", title="Comerciales"),  
    st.Page("pages/4_Pais_Origen.py", title="País de Origen"),
    st.Page("pages/5_Equipo.py", title="Equipo"),
])
pg.run()


