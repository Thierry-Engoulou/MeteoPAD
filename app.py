import streamlit as st
st.set_page_config(page_title="Dashboard Météo", layout="wide")

import pandas as pd
import numpy as np
import glob
import os

# --- CSS Personnalisé ---
custom_css = """
<style>
    /* Personnalisation du titre et du fond */
    .main .block-container{
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: #F2F4F7;
    }
    h1 {
        color: #0077B6;
        text-align: center;
    }
    h2 {
        color: #005f73;
    }
    /* Style pour le container des métriques */
    .metric {
        background: #CAF0F8;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    /* Style pour les graphiques */
    .chart-container {
        padding: 1rem;
        background: #EDF6F9;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Titre de l'application ---
st.title("🌦️ Dashboard Météo du Port Autonorme de Douala- Vue en Direct")

# --- Description/informations ---
st.markdown("Ce dashboard vous présente les dernières observations météorologiques extrait des differente station du PAD.")

# --- Répertoire contenant les fichiers Excel ---
DATA_DIR = r"B:\Marine Weather Data\Data Update"
excel_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))

if not excel_files:
    st.error("Aucun fichier Excel trouvé dans le répertoire spécifié.")
    st.stop()

# --- Sélection du fichier ---
selected_file = st.sidebar.selectbox("Choisissez un fichier météo :", excel_files)

# --- Lecture et préparation des données ---
df = pd.read_excel(selected_file)
df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

# Conversion des valeurs (on évite les erreurs sur DATETIME ou STATION_ID)
for col in df.columns:
    if col not in ["DATETIME", "STATION_ID"]:
        df[col] = (df[col].astype(str)
                   .str.replace(",", ".", regex=False)
                   .replace("9999.999", np.nan)
                   .astype(float))
df.replace(9999.999, np.nan, inplace=True)
df.interpolate(method='linear', limit_direction='both', inplace=True)

# Conserver le jeu complet pour le téléchargement
full_df = df.copy()

# --- Utilisation des 10 dernières données ---
recent_data = df.tail(10).copy()

# --- Affichage des dernières observations sous forme de "carte météo" ---
st.subheader("📊 Dernières Observations")
for _, row in recent_data.iterrows():
    st.markdown(
        f"""
        <div style="background:#CAF0F8;padding:10px;margin:5px;border-radius:8px;">
          <p style="margin:0;font-size:1.1rem;"><strong>🕒 {row['DATETIME']}</strong></p>
          <p style="margin:0;">🌡️ Température : <strong>{row.get('AIR_TEMPERATURE', np.nan):.1f} °C</strong></p>
          <p style="margin:0;">💧 Humidité : <strong>{row.get('HUMIDITY', np.nan):.0f}%</strong></p>
          <p style="margin:0;">💨 Vent : <strong>{row.get('WIND_SPEED', 0):.1f} km/h</strong></p>
          <p style="margin:0;">📈 Pression : <strong>{row.get('AIR_PRESSURE', 0):.1f} hPa</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Statistiques Moyennes sur les 10 dernières observations ---
st.subheader("📌 Statistiques Moyennes (10 dernières observ.)")
cols = st.columns(5)
metrics = {
    "AIR_TEMPERATURE": ("Température", "°C"),
    "HUMIDITY": ("Humidité", "%"),
    "AIR_PRESSURE": ("Pression", "hPa"),
    "DEWPOINT": ("Point de rosée", "°C"),
    "WIND_SPEED": ("Vent", "km/h")
}
for idx, (col_name, (label, unit)) in enumerate(metrics.items()):
    if col_name in recent_data.columns:
        mean_val = recent_data[col_name].mean()
        cols[idx].markdown(f"<div class='metric'>{label}<br><span style='font-size:1.5rem'>{mean_val:.1f} {unit}</span></div>", unsafe_allow_html=True)

# --- Graphiques d'évolution des paramètres ---
st.subheader("📈 Évolution des paramètres récents")
if "DATETIME" in recent_data.columns:
    recent_data["DATETIME"] = pd.to_datetime(recent_data["DATETIME"])
    recent_data.set_index("DATETIME", inplace=True)

chart_params = ["AIR_TEMPERATURE", "AIR_PRESSURE", "HUMIDITY", "WIND_SPEED", "DEWPOINT"]
for param in chart_params:
    if param in recent_data.columns:
        with st.container():
            st.markdown(f"<div class='chart-container'><h2>{param.replace('_', ' ').title()}</h2></div>", unsafe_allow_html=True)
            st.line_chart(recent_data[param], height=200)

# --- Option de téléchargement des données complètes ---
st.sidebar.download_button(
    label="📥 Télécharger les données corrigées",
    data=full_df.to_csv(index=False).encode("utf-8"),
    file_name="donnees_meteo_corrigees.csv",
    mime="text/csv"
)