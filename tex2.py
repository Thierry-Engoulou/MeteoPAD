import streamlit as st
import pandas as pd
import numpy as np
import glob
import os

# Configuration de la page
st.set_page_config(page_title="Dashboard Météo PAD", layout="wide")

# Titre de l'application
st.title("🌦️ Dashboard Météo - Port Autonome de Douala")

# Répertoire contenant les fichiers Excel
DATA_DIR = r"B:\Marine Weather Data\Data Update"

# Lister les fichiers Excel
excel_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))

if not excel_files:
    st.error("Aucun fichier Excel trouvé dans le répertoire spécifié.")
    st.stop()

# Sélection du fichier à afficher
selected_file = st.sidebar.selectbox("Choisissez un fichier météo :", excel_files)

# Lecture du fichier
df = pd.read_excel(selected_file)

# Normalisation des noms de colonnes
df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

# Conversion des valeurs avec virgules
for col in df.columns:
    if col not in ["DATETIME", "STATION_ID"]:
        df[col] = (df[col].astype(str)
                   .str.replace(",", ".", regex=False)
                   .replace("9999.999", np.nan)
                   .astype(float))

# Remplacer les 9999.999 résiduels par NaN
df.replace(9999.999, np.nan, inplace=True)

# Interpolation linéaire
df.interpolate(method='linear', limit_direction='both', inplace=True)

# On conserve le jeu de données complet pour le téléchargement si besoin
full_df = df.copy()

# On travaille sur les 10 dernières observations pour les affichages et graphiques
recent_data = df.tail(10).copy()

# Affichage des 10 dernières valeurs
st.subheader("📊 Dernières Observations")
for _, row in recent_data.iterrows():
    st.markdown(
        f"""
        **🕒 {row['DATETIME']}**  
        🌡️ **{row.get('AIR_TEMPERATURE', np.nan):.1f} °C** &nbsp;&nbsp;
        💧 **{row.get('HUMIDITY', np.nan):.0f}%** &nbsp;&nbsp;
        💨 **{row.get('WIND_SPEED', 0):.1f} km/h** &nbsp;&nbsp;
        📈 **{row.get('AIR_PRESSURE', 0):.1f} hPa**
        ---
        """,
        unsafe_allow_html=True
    )

# Affichage de métriques moyennes calculées sur ces 10 dernières observations
st.subheader("📌 Statistiques Moyennes (10 dernières observ.)")
cols = st.columns(3)
metrics = {
    "AIR_TEMPERATURE": ("Température", "°C"),
    "HUMIDITY": ("Humidité", "%"),
    "AIR_PRESSURE": ("Pression", "hPa"),
    "DEWPOINT": ("Point de rosée", "°C"),
    "WIND_SPEED": ("Vent", "km/h")
}
for i, (col, (label, unit)) in enumerate(metrics.items()):
    if col in recent_data.columns:
        mean_val = recent_data[col].mean()
        cols[i % 3].metric(label, f"{mean_val:.1f} {unit}")

# Préparation des données graphiques à partir des 10 dernières observations
st.subheader("📈 Évolution des paramètres (10 dernières observations)")
if "DATETIME" in recent_data.columns:
    # Assurez-vous que DATETIME est de type datetime si ce n'est pas déjà le cas
    recent_data["DATETIME"] = pd.to_datetime(recent_data["DATETIME"])
    recent_data.set_index("DATETIME", inplace=True)
elif recent_data.index.name != "DATETIME":
    st.warning("La colonne DATETIME n'est pas trouvée ou n'est pas reconnue.")

# Pour chaque paramètre, on affiche une courbe de tendance
for param in ["AIR_TEMPERATURE", "AIR_PRESSURE", "HUMIDITY", "WIND_SPEED", "DEWPOINT"]:
    if param in recent_data.columns:
        st.markdown(f"**Évolution de {param.replace('_', ' ')}**")
        st.line_chart(recent_data[param], height=200)

# Option de téléchargement : les données complètes corrigées
st.sidebar.download_button(
    label="📥 Télécharger les données corrigées",
    data=full_df.to_csv(index=False).encode("utf-8"),
    file_name="donnees_meteo_corrigees.csv",
    mime="text/csv"
)