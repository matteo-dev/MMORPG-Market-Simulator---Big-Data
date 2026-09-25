# Projet Big Data - MMORPG Frontend (Streamlit)

import streamlit as st 
import requests 
import pandas as pd 
import time 
import subprocess

# --- CORRECTION POUR STREAMLIT CLOUD ---
@st.cache_resource
def start_fastapi():
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=1)
    except requests.ConnectionError:
        subprocess.Popen(["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"])
        time.sleep(3) # Laisse le temps au serveur de démarrer
    return True

start_fastapi()
# ---------------------------------------

st.set_page_config(page_title="MMO Market Simulator", layout="wide", page_icon="📈")

API_URL = "http://127.0.0.1:8000/api"

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=1.5)
        return response.json()
    except:
        return None

def send_trade(action, resource):
    requests.post(f"{API_URL}/trade", json={"action": action, "resource": resource, "qty": 1})

def trigger_musk_tweet(action):
    requests.post(f"{API_URL}/musk_tweet?action={action}")
    if action == "buy":
        st.toast("🚀 TWEET POSITIF ! 30 ordres d'ACHAT injectés d'un coup...")
    else:
        st.toast("📉 TWEET NÉGATIF ! 30 ordres de VENTE injectés d'un coup...")

st.title("📈 MMORPG Market Simulator - Big Data")

tab_live, tab_analytics = st.tabs(["⚡ Trading Live (OLTP)", "📊 Analytics (OLAP)"])

# ONGLET 1 : TRADING EN TEMPS RÉEL (OLTP)
with tab_live:
    inventory = fetch_data("inventory")
    prices = fetch_data("prices")
    chart_data = fetch_data("chart")
    history_data = fetch_data("history")

    if not inventory or not prices:
        st.error("Serveur Backend (FastAPI) en cours de démarrage... Patiente quelques secondes et rafraîchis la page.")
        st.stop()

    col_balance, col_pump, col_dump = st.columns([2, 1, 1])
    with col_balance:
        st.subheader(f"💰 Solde actuel : **{inventory['balance']:.2f} $**")
    with col_pump:
        st.button("🚀 Tweet Positif", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("buy",))
    with col_dump:
        st.button("📉 Tweet Négatif", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("sell",))

    cols = st.columns(3)
    resources = [
        {"id": "wood", "name": "Bois", "emoji": "🌲"},
        {"id": "iron", "name": "Fer", "emoji": "⛏️"},
        {"id": "gold", "name": "Or", "emoji": "👑"}
    ]

    for i, res in enumerate(resources):
        with cols[i]:
            res_id = res["id"]
            st.markdown(f"### {res['emoji']} {res['name']}")
            st.metric(label=f"Prix du marché", value=f"{prices[res_id]:.2f} $")
            st.write(f"**En stock :** {inventory[res_id]} unités")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"🟩 Acheter ({res['name']})", key=f"buy_{res_id}", use_container_width=True):
                    send_trade("buy", res_id)
            with btn_col2:
                if st.button(f"🟥 Vendre ({res['name']})", key=f"sell_{res_id}", use_container_width=True):
                    send_trade("sell", res_id)

    st.divider()
    col_chart, col_hist = st.columns([2, 1])

    with col_chart:
        st.subheader("📊 Évolution des prix")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.line_chart(df_chart, height=350)

    with col_hist:
        st.subheader("📜 Dernières Transactions")
        if history_data:
            df_history = pd.DataFrame(history_data)
            df_history["action"] = df_history["action"].map({"buy": "Achat", "sell": "Vente"})
            st.dataframe(df_history[["time", "entity", "action", "resource", "qty", "price"]], hide_index=True, height=350)

# ONGLET 2 : ANALYTIQUE DE DONNÉES (OLAP)
with tab_analytics:
    st.markdown("Cette section lit la base de données persistante (SQLite) pour faire de l'analytique sur tout l'historique, sans ralentir le marché en direct.")
    analytics_data = fetch_data("analytics")
    
    if analytics_data:
        df_analytics = pd.DataFrame(analytics_data)
        col_metrics, col_bar = st.columns([1, 2])
        
        with col_metrics:
            st.subheader("Données globales")
            df_display = df_analytics.rename(columns={
                "resource": "Ressource", 
                "total_trades": "Nb Transactions", 
                "total_qty": "Volume Échangé", 
                "total_volume": "Valeur Totale ($)"
            })
            st.dataframe(df_display, hide_index=True)

        with col_bar:
            st.subheader("Valeur Totale Échangée ($) par Ressource")
            st.bar_chart(df_analytics.set_index("resource")["total_volume"])
            
        if st.button("Rafraîchir les données Analytiques"):
            st.rerun()

time.sleep(1)
st.rerun()
