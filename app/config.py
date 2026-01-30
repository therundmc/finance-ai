"""Gestion de la configuration"""
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# API Keys depuis l'environnement
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

DEFAULT_CONFIG = {
    "tickers": ["LOGN.SW", "AAPL"],
    "model": "mistral-nemo",
    "save_history": True,
    "advanced_analysis": True,
    "parallel_analysis": True,
    "num_threads": 12
}

def load_config(config_path='/app/config.json'):
    """Charge la configuration depuis config.json"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"✅ Configuration chargée: {len(config.get('tickers', []))} actions à surveiller")
                print(f"🤖 Modèle: {config.get('model', 'non spécifié')}")
                print(f"⚡ Parallélisme: {'Activé' if config.get('parallel_analysis', False) else 'Désactivé'}")
                print(f"🔧 Threads: {config.get('num_threads', 12)}")
                return config
        else:
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            print(f"⚙️ Fichier de configuration créé: {config_path}")
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement de la config: {e}")
        return DEFAULT_CONFIG
