# Projet Big Data - MMORPG Frontend (Streamlit)
# Ce dashboard Streamlit se connecte à l'API FastAPI pour afficher les données du marché en temps réel (OLTP) et 
# fournir des analyses historiques (OLAP).

import streamlit as st # Bibliothèque pour créer des applications web interactives en Python, utilisée ici pour construire le dashboard du marché.
import requests # Bibliothèque pour faire des requêtes HTTP, utilisée pour communiquer avec l'API FastAPI du backend et récupérer les données du marché.
import pandas as pd # Bibliothèque pour la manipulation et l'analyse de données, utilisée ici pour structurer les données récupérées de l'API et les afficher dans le dashboard.
import time # Bibliothèque pour gérer les délais et les rafraîchissements automatiques du dashboard.

st.set_page_config(page_title="MMO Market Simulator", layout="wide", page_icon="📈")

API_URL = "http://127.0.0.1:8000/api"

# Fonction utilitaire pour faire des requêtes GET à l'API et récupérer les données au format JSON.
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        return response.json()
    except:
        return None

# Fonction pour envoyer une requête de trading (achat ou vente) à l'API. Elle prend en paramètre l'action (buy/sell) et la ressource concernée,
def send_trade(action, resource):
    requests.post(f"{API_URL}/trade", json={"action": action, "resource": resource, "qty": 1})

# Fonction pour déclencher un tweet de Musk. En fonction de l'action (buy/sell), 
# elle appelle l'API correspondante et affiche une notification dans le dashboard.
def trigger_musk_tweet(action):
    # Appelle l'API en précisant si c'est un achat (buy) ou une vente (sell)
    requests.post(f"{API_URL}/musk_tweet?action={action}")
    # Boucle if pour afficher une notification différente selon le type de tweet simulé (positif pour les achats, négatif pour les ventes)
    if action == "buy":
        st.toast("🚀 TWEET POSITIF ! 30 ordres d'ACHAT injectés d'un coup...")
    else:
        st.toast("📉 TWEET NÉGATIF ! 30 ordres de VENTE injectés d'un coup...")

st.title("📈 MMORPG Market Simulator - Big Data")

# Création de deux onglets pour séparer l'opérationnel (OLTP) de l'analytique (OLAP)
tab_live, tab_analytics = st.tabs(["⚡ Trading Live (OLTP)", "📊 Analytics (OLAP)"])


# ONGLET 1 : TRADING EN TEMPS RÉEL (OLTP)

# Dans cet onglet, nous affichons les données en temps réel du marché : les prix actuels, l'inventaire du joueur, 
# un graphique de l'évolution des prix, et l'historique des transactions.
with tab_live:
    inventory = fetch_data("inventory")
    prices = fetch_data("prices")
    chart_data = fetch_data("chart")
    history_data = fetch_data("history")

    # Message d'erreur si le backend n'est pas joignable, avec une instruction pour lancer le serveur FastAPI. 
    # Le dashboard s'arrête ensuite pour éviter des erreurs de données manquantes.
    if not inventory or not prices:
        st.error("Serveur Backend (FastAPI) injoignable. Lance uvicorn main:app --reload")
        st.stop()

# Layout avec 3 colonnes : Le solde, le bouton pour simuler un tweet positif, et le bouton pour simuler un tweet négatif.
    col_balance, col_pump, col_dump = st.columns([2, 1, 1])
    with col_balance:
        st.subheader(f"💰 Solde actuel : **{inventory['balance']:.2f} $**")
    with col_pump:
        st.button("🚀 Tweet Positif", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("buy",))
    with col_dump:
        st.button("📉 Tweet Négatif", type="primary", use_container_width=True, on_click=trigger_musk_tweet, args=("sell",))

    # Affichage des ressources disponibles avec id, nom et emoji
    cols = st.columns(3)
    resources = [
        {"id": "wood", "name": "Bois", "emoji": "🌲"},
        {"id": "iron", "name": "Fer", "emoji": "⛏️"},
        {"id": "gold", "name": "Or", "emoji": "👑"}
    ]

    # Boucle pour afficher les informations de chaque ressource dans sa propre colonne : 
    # le prix du marché, la quantité en stock, et les boutons d'achat/vente.
    for i, res in enumerate(resources):
        with cols[i]:
            res_id = res["id"]
            st.markdown(f"### {res['emoji']} {res['name']}")
            st.metric(label=f"Prix du marché", value=f"{prices[res_id]:.2f} $")
            st.write(f"**En stock :** {inventory[res_id]} unités")
            
            btn_col1, btn_col2 = st.columns(2)
            # Bouton d'achat : lorsqu'il est cliqué, il envoie une requête de trading pour acheter la ressource correspondante.
            with btn_col1:
                if st.button(f"🟩 Acheter ({res['name']})", key=f"buy_{res_id}", use_container_width=True):
                    send_trade("buy", res_id)
            # Bouton de vente : lorsqu'il est cliqué, il envoie une requête de trading pour vendre la ressource correspondante.
            with btn_col2:
                if st.button(f"🟥 Vendre ({res['name']})", key=f"sell_{res_id}", use_container_width=True):
                    send_trade("sell", res_id)

    # Affichage de l'évolution des prix dans un graphique linéaire, et de l'historique des transactions dans un tableau.
    st.divider()
    col_chart, col_hist = st.columns([2, 1])

    # Graphique de l'évolution des prix : si les données sont disponibles, elles sont converties en DataFrame et affichées avec st.line_chart.
    with col_chart:
        st.subheader("📊 Évolution des prix")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.line_chart(df_chart, height=350)

    # Tableau de l'historique des transactions : si les données sont disponibles, elles sont converties en DataFrame,
    with col_hist:
        st.subheader("📜 Dernières Transactions")
        if history_data:
            df_history = pd.DataFrame(history_data)
            df_history["action"] = df_history["action"].map({"buy": "Achat", "sell": "Vente"})
            st.dataframe(df_history[["time", "entity", "action", "resource", "qty", "price"]], hide_index=True, height=350)


# ONGLET 2 : ANALYTIQUE DE DONNÉES (OLAP)

# Dans cet onglet, nous affichons des analyses historiques basées sur les données agrégées de la base de données SQLite.
with tab_analytics:
    st.markdown("Cette section lit la base de données persistante (SQLite) pour faire de l'analytique sur tout l'historique, sans ralentir le marché en direct.")
    analytics_data = fetch_data("analytics")
    
    # Boucle if pour vérifier si les données analytiques sont disponibles. 
    # Si oui, elles sont converties en DataFrame et affichées dans deux colonnes :
    if analytics_data:
        df_analytics = pd.DataFrame(analytics_data)
        
        col_metrics, col_bar = st.columns([1, 2])
        
        # Affichage des données globales : un tableau avec le nombre total de transactions, 
        # le volume échangé, et la valeur totale pour chaque ressource.
        with col_metrics:
            st.subheader("Données globales")
            df_display = df_analytics.rename(columns={
                "resource": "Ressource", 
                "total_trades": "Nb Transactions", 
                "total_qty": "Volume Échangé", 
                "total_volume": "Valeur Totale ($)"
            })
            st.dataframe(df_display, hide_index=True)

        # Affichage d'un graphique à barres pour la valeur totale échangée par ressource, 
        # en utilisant st.bar_chart avec la colonne "total_volume" indexée par "resource".      
        with col_bar:
            st.subheader("Valeur Totale Échangée ($) par Ressource")
            st.bar_chart(df_analytics.set_index("resource")["total_volume"])
            
        # Bouton manuel pour rafraîchir l'analytique
        if st.button("Rafraîchir les données Analytiques"):
            st.rerun()

# Rafraîchissement automatique toutes les 1 secondes pour l'onglet OLTP, afin de maintenir les données à jour sans surcharger le backend.
time.sleep(1)
st.rerun()