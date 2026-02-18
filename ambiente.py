import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import os

# --- CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="Aria Milano Monitor", layout="wide", initial_sidebar_state="expanded")

def apply_custom_style():
    """Applica un tema scuro personalizzato per tutti i grafici."""
    plt.rcParams.update({
        "grid.alpha": 0.2,
        "axes.edgecolor": "#3A4A5E",
        "patch.edgecolor": "none",
        "font.family": "sans-serif",
        "figure.facecolor": "#1A1F2C",
        "axes.facecolor": "#1A1F2C",
        "text.color": "#F0F4FA",
        "axes.labelcolor": "#B0C0D0",
        "xtick.color": "#B0C0D0",
        "ytick.color": "#B0C0D0"
    })

apply_custom_style()

# --- LOGICA DI CARICAMENTO DATI ---
@st.cache_data
def load_environmental_data():
    base_path = os.path.dirname(__file__)
    # Caricamento Metadati Stazioni
    path_geo = os.path.join(base_path, "qaria_stazione.geojson")
    with open(path_geo, "r", encoding="utf-8") as f:
        geo_data = json.load(f)
    stations_list = [
        {
            "id": f["properties"]["id_amat"],
            "nome": f["properties"]["nome"],
            "coord": f["geometry"]["coordinates"]
        } for f in geo_data["features"]
    ]
    df_meta = pd.DataFrame(stations_list)
    # Caricamento Serie Storiche (2016-2025)
    all_records = []
    for year in range(2016, 2026):
        file_p = os.path.join(base_path, f"{year}_stazioni.json")
        if os.path.exists(file_p):
            with open(file_p, "r", encoding="utf-8") as f:
                all_records.extend(json.load(f))
    df_main = pd.DataFrame(all_records)
    df_main['data'] = pd.to_datetime(df_main['data'])
    df_main['valore'] = pd.to_numeric(df_main['valore'], errors='coerce')
    df_main['anno'] = df_main['data'].dt.year
    df_main['mese'] = df_main['data'].dt.month
    # Merge unico e pulito
    df_meta['id'] = df_meta['id'].astype(str)
    df_main['stazione_id'] = df_main['stazione_id'].astype(str)
    return pd.merge(df_main, df_meta, left_on='stazione_id', right_on='id', how='left')

df_final = load_environmental_data()

# --- INTERFACCIA UTENTE ---
st.markdown("# 🌆 Osservatorio Ambientale: **Milano Respira**")
st.caption("Dieci anni di monitoraggio della qualità dell'aria nella rete AMAT (2016-2025)")

with st.expander("🔬 Cosa respiriamo? Guida agli inquinanti"):
    cols = st.columns(2)
    pollutants = {
        "NO2 (Biossido di Azoto)": "Irritante prodotto da motori diesel. Causa infiammazioni respiratorie.",
        "O3 (Ozono)": "Inquinante secondario estivo. Potente ossidante per polmoni e vegetazione.",
        "SO2 (Biossido di Zolfo)": "Deriva da combustibili fossili. Responsabile delle piogge acide.",
        "C6H6 (Benzene)": "Idrocarburo cancerogeno derivante dal traffico veicolare.",
        "CO (Monossido di Carbonio)": "Gas tossico da combustione incompleta; riduce l'ossigeno nel sangue.",
        "PM10 / PM2.5": "Particolato fine capace di penetrare in profondità nell'apparato circolatorio."
    }
    for i, (name, desc) in enumerate(pollutants.items()):
        cols[i % 2].info(f"**{name}**: {desc}")

st.divider()

# --- SEZIONE 1: VOLUME DATI ---
col_stats, col_graph = st.columns([1, 2])

with col_stats:
    st.subheader("📦 Consistenza Archivi")
    st.write("Distribuzione annua dei campionamenti effettuati dalla rete di rilevamento.")
    total_obs = len(df_final)
    st.metric("Rilevazioni Complessive", f"{total_obs:,}".replace(",", "."))

with col_graph:
    fig_vol, ax_vol = plt.subplots(figsize=(8, 4))
    sns.countplot(data=df_final, x='anno', palette="magma", ax=ax_vol)
    ax_vol.set_ylabel("Frequenza Campionamenti")
    ax_vol.set_xlabel("Anno di Riferimento")
    st.pyplot(fig_vol)

# --- SEZIONE 2: TREND TEMPORALE ---
st.divider()
st.subheader("⏳ Serie Storiche")
selected_year = st.select_slider("Indica l'anno da esaminare", options=range(2016, 2026), value=2025)

mask_year = df_final[df_final['anno'] == selected_year]
available_gas = sorted(mask_year['inquinante'].unique())
selected_gas = st.selectbox("Sostanza da analizzare:", available_gas)

monthly_trend = mask_year[mask_year['inquinante'] == selected_gas].groupby('mese')['valore'].mean().reset_index()

fig_trend, ax_trend = plt.subplots(figsize=(12, 4))
sns.lineplot(data=monthly_trend, x='mese', y='valore', marker='D', color='#E83F6F', linewidth=3, markersize=8)
ax_trend.fill_between(monthly_trend['mese'], monthly_trend['valore'], alpha=0.15, color='#E83F6F')
ax_trend.set_xticks(range(1, 13))
ax_trend.set_xticklabels(['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'])
ax_trend.set_title(f"Andamento {selected_gas} nel {selected_year} (medie mensili)", loc='left', fontweight='bold')
st.pyplot(fig_trend)

# --- SEZIONE 3: RANKING STAZIONI ---
st.divider()
st.subheader("🗺️ Dislocazione Territoriale")

tab1, tab2 = st.tabs(["📋 Graduatoria Stazioni", "🎯 Analisi Puntuale"])

with tab1:
    gas_comp = st.selectbox("Parametro di confronto:", available_gas, key="comp_gas")
    ranking = df_final[df_final['inquinante'] == gas_comp].groupby('nome')['valore'].mean().sort_values(ascending=False).reset_index()
    fig_rank, ax_rank = plt.subplots(figsize=(10, 6))
    sns.barplot(data=ranking, x='valore', y='nome', palette="Spectral", ax=ax_rank)
    ax_rank.set_title(f"Concentrazione media {gas_comp} sul decennio", fontweight='bold')
    st.pyplot(fig_rank)

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        staz_focus = st.selectbox("Punto di monitoraggio:", sorted(df_final['nome'].unique()))
    with c2:
        gas_focus = st.selectbox("Inquinante specifico:", sorted(df_final[df_final['nome'] == staz_focus]['inquinante'].unique()))
    data_focus = df_final[(df_final['nome'] == staz_focus) & (df_final['inquinante'] == gas_focus) & (df_final['anno'] == selected_year)]
    monthly_focus = data_focus.groupby('mese')['valore'].mean().reset_index()
    if not monthly_focus.empty:
        fig_f, ax_f = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=monthly_focus, x='mese', y='valore', color="#2DD4BF", marker='*', linewidth=2.5)
        ax_f.set_title(f"Dettaglio {gas_focus} - Stazione {staz_focus} ({selected_year})", fontweight='bold')
        st.pyplot(fig_f)
    else:
        st.warning("Serie storica non disponibile per questa selezione.")

# --- FOOTER ---
st.sidebar.image("https://www.comune.milano.it/o/comune-milano-theme/images/logo-comune-milano.svg", width=100)
st.sidebar.markdown("---")
st.sidebar.info("🌱 Progetto di data visualization per la sensibilizzazione ambientale sui dati del Comune di Milano.")