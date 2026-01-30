"""Gestion de la configuration - Version Claude API"""
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# API Keys depuis l'environnement
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')

# Configuration Claude (remplace Ollama)
CLAUDE_CONFIG = {
    # Screening rapide avec Haiku
    'screening': {
        'model': 'claude-3-5-haiku-20241022',
        'max_tokens': 256,
        'temperature': 0.2
    },
    # Analyse approfondie avec Sonnet
    'deep_analysis': {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 4000,
        'temperature': 0.3
    },
    # Portfolio analysis
    'portfolio': {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 3000,
        'temperature': 0.3
    }
}

DEFAULT_CONFIG = {
    "tickers": ["AAPL", "AMD", "NVDA", "GOOG", "MSFT"],
    "save_history": True,
    "advanced_analysis": True,
    "parallel_analysis": True,
    "num_threads": 12,  # Gardé pour compatibilité mais non utilisé avec Claude
    
    # NOUVEAU: Configuration Claude
    "use_claude": True,
    "screening_threshold": 60,  # Score minimum pour deep analysis
    "max_deep_analyses_per_day": 20,
    
    "trading": {
        "buy_commission": 10.0,
        "sell_commission": 12.0,
        "commission_currency": "CHF"
    }
}

def load_config(config_path='/app/config.json'):
    """Charge la configuration depuis config.json"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"✅ Configuration chargée: {len(config.get('tickers', []))} actions à surveiller")
                
                # Afficher le mode (Claude ou Ollama pour compatibilité)
                if config.get('use_claude', True):
                    print(f"🤖 Mode: Claude API (Hybride Haiku→Sonnet)")
                else:
                    # Fallback Ollama si configuré (compatibilité)
                    model = config.get('model', 'mistral-nemo')
                    print(f"🤖 Mode: Ollama Local ({model})")
                
                print(f"⚡ Parallélisme: {'Activé' if config.get('parallel_analysis', False) else 'Désactivé'}")
                
                return config
        else:
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            print(f"⚙️ Fichier de configuration créé: {config_path}")
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement de la config: {e}")
        return DEFAULT_CONFIG
