import streamlit as st 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt 
import json 
import os 
 
#configuro la pagina
st.set_page_config(page_title="Aria Milano Monitor", layout="wide", initial_sidebar_state="expanded")  #impostazioni base della pagina
 
#grafico personalizzato
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
 
apply_custom_style()  #applico subito lo stile ai grafici
 
#carico i dati
@st.cache_data  #memorizzo i dati per evitare ricarichi inutili
def load_environmental_data():
    base_path = os.path.dirname(__file__)  #prendo il percorso della cartella del file
 
    path_geo = os.path.join(base_path, "qaria_stazione.geojson")  #costruisco il percorso del file geojson
    with open(path_geo, "r", encoding="utf-8") as f:
        geo_data = json.load(f)  #leggo il file
 
   #estrazione stazioni
        stations_list = [
        {
            "id": f["properties"]["id_amat"],  #id stazione
            "nome": f["properties"]["nome"],  #nome stazione
            "coord": f["geometry"]["coordinates"]  #coordinate geografiche
        } for f in geo_data["features"]  #scorro tutte le feature del geojson
    ]
 
    df_meta = pd.DataFrame(stations_list)  #trasformo in dataframe
  
    #carico i dati storici
    all_records = []  #lista dove accumulo tutti i dati
    for year in range(2016, 2026):  #ciclo sugli anni
        file_p = os.path.join(base_path, f"{year}_stazioni.json")  #costruisco nome file
        if os.path.exists(file_p):  #controllo se il file esiste
            with open(file_p, "r", encoding="utf-8") as f:
                all_records.extend(json.load(f))  #aggiungo i dati alla lista
 
    #traformo in dataframe
    df_main = pd.DataFrame(all_records)  #creo dataframe principale
 
    df_main['data'] = pd.to_datetime(df_main['data'])  #converto la data
    df_main['valore'] = pd.to_numeric(df_main['valore'], errors='coerce')  #valori numerici
    df_main['anno'] = df_main['data'].dt.year  #estraggo anno
    df_main['mese'] = df_main['data'].dt.month  #estraggo mese
 
 
    #unisco i dati
    df_meta['id'] = df_meta['id'].astype(str)  #conversione tipo
    df_main['stazione_id'] = df_main['stazione_id'].astype(str)  #conversione tipo
 
    return pd.merge(df_main, df_meta, left_on='stazione_id', right_on='id', how='left')  #merge tra dati e metadati
 
df_final = load_environmental_data()  #carico tutto il dataset finale
 
# titolo e descrizione dell app
st.markdown("# 🌆 Osservatorio Ambientale: **Milano Respira**")  #titolo
st.caption("Dieci anni di monitoraggio della qualità dell'aria nella rete AMAT (2016-2025)")  #sottotitolo
 
#spiegazioni inquinanti
with st.expander("🔬 Cosa respiriamo? Guida agli inquinanti"):  #sezione espandibile
    cols = st.columns(2)  #creo 2 colonne
 
    pollutants = {
        "NO2 (Biossido di Azoto)": "Irritante prodotto da motori diesel. Causa infiammazioni respiratorie.",
        "O3 (Ozono)": "Inquinante secondario estivo. Potente ossidante per polmoni e vegetazione.",
        "SO2 (Biossido di Zolfo)": "Deriva da combustibili fossili. Responsabile delle piogge acide.",
        "C6H6 (Benzene)": "Idrocarburo cancerogeno derivante dal traffico veicolare.",
        "CO (Monossido di Carbonio)": "Gas tossico da combustione incompleta; riduce l'ossigeno nel sangue.",
        "PM10 / PM2.5": "Particolato fine capace di penetrare in profondità nell'apparato circolatorio."
    }
 
    for i, (name, desc) in enumerate(pollutants.items()):  #scorro dizionario
        cols[i % 2].info(f"**{name}**: {desc}")  #distribuisco su due colonne
 
st.divider()  #linea separatrice
 
#statistiche e grafico
col_stats, col_graph = st.columns([1, 2])  #layout 1/3 e 2/3
 
with col_stats:
    st.subheader("📦 Consistenza Archivi")  #titolo sezione
    st.write("Distribuzione annua dei campionamenti effettuati dalla rete di rilevamento.")
    total_obs = len(df_final)  #conto totale osservazioni
    st.metric("Rilevazioni Complessive", f"{total_obs:,}".replace(",", "."))  #mostro il numero
 
with col_graph:
    fig_vol, ax_vol = plt.subplots(figsize=(8, 4))  #creo figura
    sns.countplot(data=df_final, x='anno', palette="magma", ax=ax_vol)  #grafico a barre
    ax_vol.set_ylabel("Frequenza Campionamenti")  #etichetta asse y
    ax_vol.set_xlabel("Anno di Riferimento")  #etichetta asse x
    st.pyplot(fig_vol)  #mostro grafico
 
st.divider()
 
st.subheader("⏳ Serie Storiche")  #titolo sezione
 
selected_year = st.select_slider("Indica l'anno da esaminare", options=range(2016, 2026), value=2025)  #slider anno
 
mask_year = df_final[df_final['anno'] == selected_year]  #filtro per anno
available_gas = sorted(mask_year['inquinante'].unique())  #lista gas disponibili
selected_gas = st.selectbox("Sostanza da analizzare:", available_gas)  #selezione gas
 
#media mensile
monthly_trend = mask_year[mask_year['inquinante'] == selected_gas].groupby('mese')['valore'].mean().reset_index()  #calcolo media mensile
 
fig_trend, ax_trend = plt.subplots(figsize=(12, 4))  #figura
 
#grafico linea
sns.lineplot(data=monthly_trend, x='mese', y='valore', marker='D', color='#E83F6F', linewidth=3, markersize=8)
ax_trend.fill_between(monthly_trend['mese'], monthly_trend['valore'], alpha=0.15, color='#E83F6F')  #riempimento area
 
ax_trend.set_xticks(range(1, 13))  #mesi
ax_trend.set_xticklabels(['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'])  #nomi mesi
 
ax_trend.set_title(f"Andamento {selected_gas} nel {selected_year} (medie mensili)", loc='left', fontweight='bold')  #titolo
 
st.pyplot(fig_trend)  #mostro grafico
 
st.divider()
 
st.subheader("Dislocazione Territoriale")  #titolo
 
#analisi territoriale
tab1, tab2 = st.tabs(["Graduatoria Stazioni", "Analisi Puntuale"])  #creo due tab
 
#ranking stazioni
with tab1:
    gas_comp = st.selectbox("Parametro di confronto:", available_gas, key="comp_gas")  #selezione gas
    ranking = df_final[df_final['inquinante'] == gas_comp].groupby('nome')['valore'].mean().sort_values(ascending=False).reset_index()  #ranking
 
    fig_rank, ax_rank = plt.subplots(figsize=(10, 6))  #figura
    sns.barplot(data=ranking, x='valore', y='nome', palette="Spectral", ax=ax_rank)  #grafico
    ax_rank.set_title(f"Concentrazione media {gas_comp} sul decennio", fontweight='bold')  #titolo
 
    st.pyplot(fig_rank)  #mostro
 
#analisi puntuali
with tab2:
    c1, c2 = st.columns(2)  #due colonne
 
    with c1:
        staz_focus = st.selectbox("Punto di monitoraggio:", sorted(df_final['nome'].unique()))  #selezione stazione
 
    with c2:
        gas_focus = st.selectbox("Inquinante specifico:", sorted(df_final[df_final['nome'] == staz_focus]['inquinante'].unique()))  #selezione gas
 
    data_focus = df_final[(df_final['nome'] == staz_focus) & (df_final['inquinante'] == gas_focus) & (df_final['anno'] == selected_year)]  #filtro
 
    monthly_focus = data_focus.groupby('mese')['valore'].mean().reset_index()  #media mensile
 
    if not monthly_focus.empty:  #se ci sono dati
        fig_f, ax_f = plt.subplots(figsize=(10, 4))  #figura
        sns.lineplot(data=monthly_focus, x='mese', y='valore', color="#2DD4BF", marker='*', linewidth=2.5)  #grafico
        ax_f.set_title(f"Dettaglio {gas_focus} - Stazione {staz_focus} ({selected_year})", fontweight='bold')  #titolo
        st.pyplot(fig_f)  #mostro grafico
    else:
        st.warning("Serie storica non disponibile per questa selezione.")  #messaggio se vuoto
 
#sidebar
st.sidebar.image("https://www.comune.milano.it/o/comune-milano-theme/images/logo-comune-milano.svg", width=100)  #logo
st.sidebar.markdown("---")  #separatore
st.sidebar.info("🌱 Progetto di data visualization per la sensibilizzazione ambientale sui dati del Comune di Milano.")  #descrizione
