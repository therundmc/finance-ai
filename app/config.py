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
# Par défaut - peut être overridé dans config.json
CLAUDE_CONFIG = {
    'screening': {
        'model': 'claude-haiku-4-5-20251001',  # Haiku 4.5 (latest)
        'max_tokens': 256,
        'temperature': 0.2
    },
    'deep_analysis': {
        'model': 'claude-sonnet-4-5-20250929',  # Sonnet 4.5 (latest)
        'max_tokens': 4000,
        'temperature': 0.3
    },
    'portfolio': {
        'model': 'claude-sonnet-4-5-20250929',  # Sonnet 4.5 (latest)
        'max_tokens': 3000,
        'temperature': 0.3
    }
}

DEFAULT_CONFIG = {
    "tickers": ["AAPL", "AMD", "NVDA", "GOOG", "MSFT"],
    "save_history": True,
    "advanced_analysis": True,
    "parallel_analysis": True,
    "num_threads": 12,
    
    # Configuration Claude
    "use_claude": True,
    "screening_threshold": 60,
    "max_deep_analyses_per_day": 20,
    
    # Modèles Claude 4.5 (latest - personnalisable)
    "claude_models": {
        "screening": "claude-haiku-4-5-20251001",
        "deep_analysis": "claude-sonnet-4-5-20250929",
        "portfolio": "claude-sonnet-4-5-20250929"
    },
    
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
                
                # Merger les modèles du fichier avec CLAUDE_CONFIG
                if 'claude_models' in config:
                    for key, model in config['claude_models'].items():
                        if key in CLAUDE_CONFIG:
                            CLAUDE_CONFIG[key]['model'] = model
                
                print(f"✅ Configuration chargée: {len(config.get('tickers', []))} actions à surveiller")
                
                if config.get('use_claude', True):
                    screening_model = CLAUDE_CONFIG['screening']['model']
                    deep_model = CLAUDE_CONFIG['deep_analysis']['model']
                    print(f"🤖 Mode: Claude API (Hybride)")
                    print(f"   📊 Screening: {screening_model}")
                    print(f"   🔍 Deep: {deep_model}")
                else:
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
