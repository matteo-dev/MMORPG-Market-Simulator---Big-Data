# Projet Big Data - MMORPG Frontend (Streamlit)

import streamlit as st 
import requests 
import pandas as pd 
import time 
import subprocess
import sys

API_URL = "http://127.0.0.1:8000/api"

# Vérifie si le backend répond déjà. Si ce n'est pas le cas, on le lance.
# L'utilisation de @st.cache_resource empêche de multiplier 
# les tentatives de connexion en boucle à chaque rafraîchissement de page.
@st.cache_resource
def start_fastapi():
    try:
        requests.get(f"{API_URL}/prices", timeout=1)
    except requests.exceptions.ConnectionError:
        # Lancement du serveur uvicorn en tâche de fond
        subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"])
        time.sleep(3) # Délai pour laisser au backend le temps de démarrer
    return True

start_fastapi()

st.set_page_config(page_title="MMO Market Simulator", layout="wide", page_icon="📈")

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
        st.toast("🚀 POSITIVE TWEET! 30 BUY orders injected at once...")
    else:
        st.toast("📉 NEGATIVE TWEET! 30 SELL orders injected at once...")

def trigger_reset():
    try:
        requests.post(f"{API_URL}/reset")
        st.toast("🧹 Market has been completely reset to zero!")
        time.sleep(1) # Le temps que le toast s'affiche
        st.rerun() # Recharge la page
    except:
        st.error("Error during reset.")

st.sidebar.button("🧹 Reset the entire market", type="secondary", on_click=trigger_reset)

st.title("📈 MMORPG Market Simulator - Big Data")

tab_live, tab_analytics = st.tabs(["⚡ Live Trading (OLTP)", "📊 Analytics (OLAP)"])

# ONGLET 1 : TRADING EN TEMPS RÉEL (OLTP)
with tab_live:
    inventory = fetch_data("inventory")
    prices = fetch_data("prices")
    chart_data = fetch_data("chart")
    history_data = fetch_data("history")

    if not inventory or not prices:
        st.error("Backend Server (FastAPI) starting up... Please wait a few seconds and refresh the page.")
        st.stop()

    col_balance, col_pump, col_dump = st.columns([2, 1, 1])
    with col_balance:
        st.subheader(f"💰 Current balance: **{inventory['balance']:.2f} $**")
    with col_pump:
        st.button("🚀 Positive Tweet", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("buy",))
    with col_dump:
        st.button("📉 Negative Tweet", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("sell",))

    cols = st.columns(3)
    resources = [
        {"id": "wood", "name": "Wood", "emoji": "🌲"},
        {"id": "iron", "name": "Iron", "emoji": "⛏️️"},
        {"id": "gold", "name": "Gold", "emoji": "👑"}
    ]

    for i, res in enumerate(resources):
        with cols[i]:
            res_id = res["id"]
            st.markdown(f"### {res['emoji']} {res['name']}")
            st.metric(label=f"Market price", value=f"{prices[res_id]:.2f} $")
            st.write(f"**In stock:** {inventory[res_id]} units")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"🟩 Buy ({res['name']})", key=f"buy_{res_id}", use_container_width=True):
                    send_trade("buy", res_id)
            with btn_col2:
                if st.button(f"🟥 Sell ({res['name']})", key=f"sell_{res_id}", use_container_width=True):
                    send_trade("sell", res_id)

    st.divider()
    col_chart, col_hist = st.columns([2, 1])

    with col_chart:
        st.subheader("📊 Price Evolution")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.line_chart(df_chart, height=350)

    with col_hist:
        st.subheader("📜 Recent Transactions")
        if history_data:
            df_history = pd.DataFrame(history_data)
            df_history["action"] = df_history["action"].map({"buy": "Buy", "sell": "Sell"})
            st.dataframe(df_history[["time", "entity", "action", "resource", "qty", "price"]], hide_index=True, height=350)

# ONGLET 2 : ANALYTIQUE DE DONNÉES (OLAP)
with tab_analytics:
    st.markdown("This section reads the persistent database (SQLite) to perform analytics on the entire history, without slowing down the live market.")
    analytics_data = fetch_data("analytics")
    
    if analytics_data:
        df_analytics = pd.DataFrame(analytics_data)
        col_metrics, col_bar = st.columns([1, 2])
        
        with col_metrics:
            st.subheader("Global Metrics")
            df_display = df_analytics.rename(columns={
                "resource": "Resource", 
                "total_trades": "Total Trades", 
                "total_qty": "Traded Volume", 
                "total_volume": "Total Value ($)"
            })
            st.dataframe(df_display, hide_index=True)

        with col_bar:
            st.subheader("Total Traded Value ($) by Resource")
            st.bar_chart(df_analytics.set_index("resource")["total_volume"])
            
        if st.button("Refresh Analytics Data"):
            st.rerun()

time.sleep(1)
st.rerun()
