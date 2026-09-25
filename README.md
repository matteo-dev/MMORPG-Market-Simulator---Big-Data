# 📈 MMORPG Market Simulator - Big Data

Simulateur de salle des marchés inspiré de l'économie des MMORPG (Hôtel des Ventes), conçu pour relever les défis du Big Data (Vélocité et Volume) à travers une architecture robuste et asynchrone.

## 🚀 Fonctionnalités Clés

1. **Architecture Asynchrone & File d'attente :** Séparation des écritures et des lectures pour encaisser une charge intense (*Heavy Writes*) sans bloquer l'interface.
2. **Event Sourcing (SQLite) :** Journalisation immuable de chaque transaction pour garantir la persistance et la sécurité des données financières.
3. **Trading Live (OLTP) :** Gestion en temps réel du portefeuille joueur, des prix du marché en mémoire vive (RAM) et simulation de bots de trading autonomes.
4. **Analytique (OLAP) :** Exploitation de la base de données persistante pour analyser les volumes échangés et l'historique sans impacter les performances en direct.
5. **Simulation d'événements :** Fonctionnalité "Tweet d'Elon Musk" pour injecter massivement des ordres d'achat ou de vente et tester la résilience du système.

## English Below

An auction house trading floor simulator inspired by MMORPG economies, designed to handle Big Data challenges (Velocity and Volume) through a robust, asynchronous architecture.

## 🚀 Key Features
1. **Asynchronous Architecture & Message Queue:** Separation of writes and reads to absorb heavy loads (Heavy Writes) without blocking the interface.
2. **Event Sourcing (SQLite):** Immutable logging of every transaction to ensure data persistence and financial security.
3. **Live Trading (OLTP):** Real-time management of player portfolios, in-memory (RAM) market prices, and autonomous trading bot simulation.
4. **Analytics (OLAP):** Leveraging the persistent database to analyze traded volumes and history without impacting live performance.
5. **Event Simulation:** "Elon Musk Tweet" feature to massively inject buy or sell orders and test system resilience.

---

## 🛠️ Installation et Lancement

1. **Cloner le dépôt / Clone the reposit :**
   ```bash
   git clone [https://github.com/votre-nom-d-utilisateur/mmo-market-simulator.git](https://github.com/votre-nom-d-utilisateur/mmo-market-simulator.git)
   cd mmo-market-simulator
2. **Installer les dépendances / Install requirements :**
   ```bash
   pip install -r requirements.txt
3.**Lancer le backend et le frontend sur deux terminaux distincts / Run the backend and frontend in two separate terminals :**
  ```bash
  uvicorn main:app --reload
  streamlit run dashboard.py
    
