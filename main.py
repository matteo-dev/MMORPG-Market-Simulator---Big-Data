# Projet Big Data - MMORPG Backend
# Code gérant le stockage (Event Sourcing), le moteur de marché asynchrone, les bots de trading, et les routes API pour OLTP et OLAP.

import asyncio # Pour la gestion asynchrone du moteur de marché et des bots
import random # Pour les décisions aléatoires des bots et les impacts de marché
import sqlite3 # Pour le stockage des événements de marché (Event Sourcing)
from datetime import datetime # Pour timestamp des événements
from fastapi import FastAPI # Framework web pour les routes API
from pydantic import BaseModel # Pour la validation des données d'entrée

app = FastAPI(title="Projet Big Data - MMORPG Backend")


# --- 1. STOCKAGE (Event Sourcing) ---

# Utilisation de SQLite pour stocker les événements de marché. 
# Chaque événement représente une action d'achat ou de vente, avec un timestamp, l'entité (joueur ou bot), la ressource, la quantité et le prix.
db_conn = sqlite3.connect("market_events.db", check_same_thread=False)
cursor = db_conn.cursor()

# Création de la table pour stocker les événements de marché
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        entity TEXT,
        action TEXT,
        resource TEXT,
        qty INTEGER,
        price_per_unit REAL
    )
""")
db_conn.commit()

# L'ensemble des ressources disponibles sur le marché, avec leurs prix initiaux. 
# Ces prix seront ajustés dynamiquement en fonction des transactions effectuées par les joueurs et les bots.
market_prices = {"wood": 10.0, "iron": 50.0, "gold": 200.0}
price_history = {"wood": [10.0], "iron": [50.0], "gold": [200.0]}

# Inventaire de base du joueur
player_inventory = {
    "balance": 1000.0,
    "wood": 20,
    "iron": 20,
    "gold": 20
}

# File d'attente asynchrone pour les ordres de marché. Les joueurs et les bots placeront leurs ordres dans cette file, 
# et le moteur du marché les traitera de manière asynchrone.
order_queue = asyncio.Queue()


# --- 2. MOTEUR ASYNCHRONE ---

# Fonction asynchrone qui représente le moteur du marché. Il traite les ordres de la file d'attente, met à jour les prix en fonction de l'offre 
# et de la demande, et enregistre chaque transaction dans la base de données.
async def market_engine():
    print("Moteur du marché démarré...")
    # Boucle infinie pour traiter les ordres de marché en continu. Le moteur attend les ordres dans la file d'attente et les traite un par un.
    while True:
        order = await order_queue.get()
        
        # Extraction des détails de l'ordre
        resource = order["resource"]
        action = order["action"]
        qty = order["qty"]
        entity = order["entity"]
        is_player = (entity == "player")

        # Calcul du coût total de la transaction en fonction du prix actuel de la ressource. 
        current_price = market_prices[resource]
        total_cost = current_price * qty
        transaction_success = False

        # Structure "if" pour vérifier si le joueur a suffisamment de fonds pour acheter ou suffisamment de ressources pour vendre. 
        # Si c'est un bot, on suppose que la transaction réussit toujours.
        if is_player:
            if action == "buy" and player_inventory["balance"] >= total_cost:
                player_inventory["balance"] -= total_cost
                player_inventory[resource] += qty
                transaction_success = True
            elif action == "sell" and player_inventory[resource] >= qty:
                player_inventory["balance"] += total_cost
                player_inventory[resource] -= qty
                transaction_success = True
        else:
            transaction_success = True

        # Sructure "if" pour enregistrer la transaction dans la base de données si elle a réussi, 
        # et pour ajuster les prix du marché en fonction de l'offre et de la demande.
        if transaction_success:
            cursor.execute(
                "INSERT INTO events (timestamp, entity, action, resource, qty, price_per_unit) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().strftime("%H:%M:%S"), entity, action, resource, qty, current_price)
            )
            db_conn.commit()

            # Ajustement des prix du marché : plus la quantité est élevée, plus l'impact sur le prix est important.
            impact = 0.02 * qty
            if action == "buy":
                market_prices[resource] *= (1 + impact)
            elif action == "sell":
                market_prices[resource] *= (1 - impact)

            # Garantie que les prix ne deviennent pas négatifs ou trop bas                
            market_prices[resource] = max(1.0, market_prices[resource])
            
            # MAJ de l'historique des prix pour le graphique (dernier 50 points)
            for res in market_prices.keys():
                price_history[res].append(market_prices[res])
                if len(price_history[res]) > 50:
                    price_history[res].pop(0)

        # Marque l'ordre comme traité dans la file d'attente
        order_queue.task_done()


# --- 3. BOTS ---

# Fonction asynchrone qui représente un bot de trading. 
# Chaque bot prend des décisions aléatoires pour acheter ou vendre des ressources à des intervalles de temps aléatoires,
async def trading_bot(bot_id: int):
    resources = ["wood", "iron", "gold"]
    actions = ["buy", "sell"]
    # Boucle infinie pour simuler le comportement continu du bot. 
    # Le bot attend un intervalle de temps aléatoire entre 0.5 et 3 secondes avant de placer un nouvel ordre.
    while True:
        await asyncio.sleep(random.uniform(0.5, 3.0))
        await order_queue.put({
            "entity": f"bot_{bot_id}",
            "resource": random.choice(resources),
            "action": random.choice(actions),
            "qty": random.randint(1, 3)
        })

# Lors du démarrage de l'application, le moteur du marché et plusieurs bots de trading sont lancés en tant que tâches asynchrones.
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_engine())
    for i in range(5):
        asyncio.create_task(trading_bot(i))


# --- 4. API ROUTES (OLTP & OLAP) ---
# OlTP (Online Transaction Processing) : Routes pour les opérations de trading en temps réel (achat/vente).
# OlAP (Online Analytical Processing) : Routes pour les analyses de marché, l'historique des transactions, et les données de prix pour les graphiques.

# Classe de modèle de données pour valider les requêtes de trading.
class TradeRequest(BaseModel):
    action: str
    resource: str
    qty: int

# Route API pour récupérer les prix actuels du marché. Cette route est utilisée par le frontend pour afficher les prix en temps réel.
@app.get("/api/prices")
def get_prices():
    return market_prices

# Route API pour récupérer l'inventaire du joueur. Cette route permet au frontend d'afficher les ressources et le solde du joueur.
@app.get("/api/inventory")
def get_inventory():
    return player_inventory

# Route API pour récupérer l'historique des transactions. Cette route renvoie les 15 dernières transactions enregistrées dans la base de données,
@app.get("/api/history")
def get_history():
    cursor.execute("SELECT timestamp, entity, action, resource, qty, price_per_unit FROM events ORDER BY id DESC LIMIT 15")
    rows = cursor.fetchall()
    return [{"time": r[0], "entity": r[1], "action": r[2], "resource": r[3], "qty": r[4], "price": round(r[5], 2)} for r in rows]

# Route API pour récupérer les données de prix pour le graphique. 
# Cette route fournit les données nécessaires pour afficher l'évolution des prix des ressources dans le frontend.
@app.get("/api/chart")
def get_chart_data():
    return price_history

# Route API pour placer un ordre de trading. Cette route reçoit les demandes d'achat ou de vente du joueur, les valide, 
# et les place dans la file d'attente pour être traitées par le moteur du marché.
@app.post("/api/trade")
# Fonction asynchrone pour traiter les demandes de trading. Elle ajoute l'ordre à la file d'attente et retourne une réponse de succès.
async def place_order(trade: TradeRequest):
    await order_queue.put({
        "entity": "player",
        "resource": trade.resource,
        "action": trade.action,
        "qty": trade.qty
    })
    return {"status": "ok"}

# Route API pour récupérer les données analytiques du marché. 
# Cette route effectue une requête SQL pour agréger les données de transactions par ressource,
@app.get("/api/analytics")
# Fonction pour récupérer les données analytiques du marché. Elle agrège les transactions par ressource 
def get_analytics():
    cursor.execute("""
        SELECT resource, COUNT(*), SUM(qty), SUM(qty * price_per_unit) 
        FROM events 
        GROUP BY resource
    """)
    # Les résultats de la requête sont formatés en une liste de dictionnaires, 
    # avec des clés pour la ressource, le nombre total de transactions, la quantité totale échangée, et le volume total (quantité * prix).
    rows = cursor.fetchall()
    return [{"resource": r[0], "total_trades": r[1], "total_qty": r[2], "total_volume": round(r[3] or 0, 2)} for r in rows]

# Route API pour simuler un tweet d'Elon Musk. 
# Cette route permet de simuler l'impact d'un tweet positif ou négatif sur le marché, 
# en générant une série d'ordres d'achat ou de vente pour les bots.
@app.post("/api/musk_tweet")
# Fonction asynchrone pour simuler un tweet d'Elon Musk. En fonction de l'action spécifiée ("buy" ou "sell"),
async def musk_tweet(action: str):
    resources = ["wood", "iron", "gold"]
    for _ in range(30):
        # Les bots réagissent au tweet en plaçant des ordres d'achat ou de vente aléatoires pour les ressources,
        await order_queue.put({
            "entity": "ELON_BOT",
            "resource": random.choice(resources),
            "action": action, # 'buy' ou 'sell' selon le bouton
            "qty": random.randint(5, 15)
        })
    return {"status": f"Tweet {action} initié"}