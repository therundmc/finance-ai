"""
News Fetcher - Récupération et résumé IA des actualités financières (Claude API)
"""

import os
import json
import time
import finnhub
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Configuration
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CACHE_DURATION = timedelta(minutes=30)

# Tickers nécessitant une recherche par keyword
TICKER_KEYWORDS = {
    'LOGN.SW': 'Logitech',
}

# Catégories disponibles
NEWS_CATEGORIES = ['general', 'forex', 'crypto', 'merger']


def _get_claude_model() -> str:
    """Récupère le modèle Claude pour news depuis config.json"""
    try:
        with open('/app/config.json', 'r') as f:
            config = json.load(f)
            # Utiliser le modèle deep_analysis pour les news (qualité)
            return config.get('claude_models', {}).get('deep_analysis', 'claude-sonnet-4-5-20250929')
    except:
        return 'claude-sonnet-4-5-20250929'


def _get_tickers() -> List[str]:
    """Récupère les tickers depuis config.json"""
    try:
        with open('/app/config.json', 'r') as f:
            return json.load(f).get('tickers', [])
    except:
        return []


class NewsCache:
    """Cache en mémoire avec expiration"""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < CACHE_DURATION:
                return data
            del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = (value, datetime.now())


class NewsFetcher:
    """Client Finnhub avec cache"""
    
    def __init__(self):
        self.client = None
        self.cache = NewsCache()
        
        print(f"🔧 NewsFetcher init - Finnhub API Key: {bool(FINNHUB_API_KEY)}")
        print(f"🔧 Claude API Key: {bool(ANTHROPIC_API_KEY)}")
        
        if FINNHUB_API_KEY:
            try:
                self.client = finnhub.Client(api_key=FINNHUB_API_KEY)
                print("✅ Finnhub client initialisé avec succès")
            except Exception as e:
                print(f"❌ Erreur initialisation Finnhub: {e}")
        else:
            print("⚠️ FINNHUB_API_KEY manquante - news désactivées")
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_company_news(self, ticker: str, days: int = 3) -> List[Dict]:
        """Récupère les news d'une entreprise"""
        print(f"📰 get_company_news({ticker}, days={days})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        cache_key = f"company_{ticker}"
        if cached := self.cache.get(cache_key):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        articles = []
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        try:
            if ticker in TICKER_KEYWORDS:
                # Recherche par keyword pour certains tickers
                keyword = TICKER_KEYWORDS[ticker].lower()
                raw = self.client.general_news('general', min_id=0)
                for item in raw:
                    if keyword in item.get('headline', '').lower() or keyword in item.get('summary', '').lower():
                        articles.append(self._parse(item, ticker))
            else:
                # Recherche native
                clean_ticker = ticker.replace('.SW', '')
                raw = self.client.company_news(clean_ticker, _from=from_date.strftime('%Y-%m-%d'), to=to_date.strftime('%Y-%m-%d'))
                articles = [self._parse(item, ticker) for item in raw]
            
            articles = sorted(articles, key=lambda x: x['datetime'], reverse=True)[:15]
            self.cache.set(cache_key, articles)
            print(f"   ✅ {len(articles)} articles récupérés et mis en cache")
            
        except Exception as e:
            print(f"   ❌ Erreur news {ticker}: {e}")
            import traceback
            traceback.print_exc()
        
        return articles
    
    def get_market_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news générales du marché"""
        print(f"🌍 get_market_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("market"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        try:
            raw = self.client.general_news('general', min_id=0)
            print(f"   📥 {len(raw)} articles bruts reçus")
            articles = [self._parse(item) for item in raw[:limit]]
            self.cache.set("market", articles)
            print(f"   ✅ {len(articles)} articles mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news marché: {e}")
            return []
    
    def get_tech_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news tech via filtrage par keywords"""
        print(f"💻 get_tech_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("tech"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['tech', 'ai', 'chip', 'semiconductor', 'nvidia', 'apple', 'google', 'software']
        articles = []
        
        try:
            raw = self.client.general_news('general', min_id=0)
            print(f"   📥 {len(raw)} articles bruts, filtrage par keywords...")
            for item in raw:
                text = (item.get('headline', '') + item.get('summary', '')).lower()
                if any(kw in text for kw in keywords):
                    articles.append(self._parse(item))
                    if len(articles) >= limit:
                        break
            self.cache.set("tech", articles)
            print(f"   ✅ {len(articles)} articles tech mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news tech: {e}")
            return []
    
    def _parse(self, item: Dict, ticker: str = None) -> Dict:
        """Parse un article brut"""
        ts = item.get('datetime', 0)
        dt = datetime.fromtimestamp(ts) if isinstance(ts, int) else datetime.now()
        
        return {
            'headline': item.get('headline', ''),
            'summary': item.get('summary', ''),
            'source': item.get('source', 'Unknown'),
            'url': item.get('url', ''),
            'datetime': dt.isoformat(),
            'ticker': ticker
        }


# Singleton
_fetcher: Optional[NewsFetcher] = None

def get_news_fetcher() -> NewsFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = NewsFetcher()
    return _fetcher


def generate_news_summary(tickers: List[str], category: str = 'all') -> Dict[str, Any]:
    """
    Génère un résumé IA des actualités en français.
    
    Args:
        tickers: Liste des tickers suivis
        category: 'my_stocks', 'market', 'tech', ou 'all'
    """
    print(f"\n{'='*50}")
    print(f"🤖 generate_news_summary(tickers={tickers}, category={category})")
    print(f"{'='*50}")
    
    fetcher = get_news_fetcher()
    
    if not fetcher.is_available():
        print("❌ News service non disponible")
        return {'success': False, 'error': 'News service unavailable', 'summaries': {}}
    
    # Collecter les articles par catégorie
    news = {
        'my_stocks': [],
        'market': fetcher.get_market_news(),
        'tech': fetcher.get_tech_news()
    }
    
    # News des actions suivies
    for ticker in tickers:
        for article in fetcher.get_company_news(ticker)[:8]:  # Augmenté de 5 à 8 par ticker
            news['my_stocks'].append(article)
    news['my_stocks'] = sorted(news['my_stocks'], key=lambda x: x['datetime'], reverse=True)[:25]  # Augmenté de 15 à 25
    
    # Générer les résumés
    categories = ['my_stocks', 'market', 'tech'] if category == 'all' else [category]
    summaries = {}
    
    print(f"\n📊 Articles collectés:")
    for cat, arts in news.items():
        print(f"   {cat}: {len(arts)} articles")
    
    for cat in categories:
        articles = news.get(cat, [])
        if not articles:
            print(f"\n⚠️ Pas d'articles pour {cat}")
            summaries[cat] = {'summary': "Aucune actualité disponible.", 'article_count': 0}
            continue
        used_count = min(len(articles), max_articles := {'my_stocks': 20, 'market': 15, 'tech': 15}.get(cat, 15))
        print(f"\n🔄 Génération résumé pour {cat} ({used_count}/{len(articles)} articles)...")
        summaries[cat] = _generate_summary(cat, articles, tickers)
        print(f"   ✅ Résumé généré: {len(summaries[cat].get('summary', ''))} chars")
    
    print(f"\n✅ Tous les résumés générés")
    return {'success': True, 'summaries': summaries, 'generated_at': datetime.now().isoformat()}


def _generate_summary(category: str, articles: List[Dict], tickers: List[str]) -> Dict[str, Any]:
    """Génère un résumé IA pour une catégorie"""
    from config import CLAUDE_CONFIG
    
    # Adapter le nombre d'articles selon la catégorie
    max_articles = {
        'my_stocks': 20,  # Plus d'articles pour ton portfolio
        'market': 15,     # Vue d'ensemble macro
        'tech': 15        # Secteur tech
    }
    article_limit = max_articles.get(category, 15)
    
    # Contexte des articles - filtrer et formater proprement
    context = "\n".join([
        f"• [{a.get('source', 'Unknown')}] {a['headline']} — {a['summary'][:200]}"
        for a in articles[:article_limit]
    ])
    
    # Instructions selon la catégorie
    tickers_str = ', '.join(tickers[:5])
    
    prompts = {
        'my_stocks': f"""Analyse ces actualités sur mon portefeuille ({tickers_str}).

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. 2-3 événements majeurs
2. Impact court terme (1 phrase)
3. Catalyseurs (1 phrase)
4. Risques (1 phrase)
5. Sentiment global avec justification (1 phrase)

Sois CONCIS et PRÉCIS.""",

        'market': f"""Analyse l'état des marchés.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. Indices principaux (1 phrase)
2. Facteurs macro (Fed, inflation, emploi) (1 phrase)
3. Secteurs leaders/retardataires (1 phrase)
4. Événements clés (1 phrase)
5. Perspective court terme (1 phrase)

Sois CONCIS.""",

        'tech': f"""Analyse l'actualité tech.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. GAFAM & mega-caps (1 phrase)
2. Semi-conducteurs (1 phrase)
3. IA et cloud (1 phrase)
4. Valorisations secteur (1 phrase)
5. Perspective (1 phrase)

Sois CONCIS."""
    }
    
    prompt = prompts.get(category, prompts['market'])

    # Utiliser config Claude pour news
    news_config = CLAUDE_CONFIG['news']
    model = news_config['model']
    max_tokens = news_config['max_tokens']
    
    print(f"   🤖 Appel Claude API: {model} ({max_tokens} tokens)")
    
    # System prompt pour Claude
    system_prompt = """Tu es un analyste financier senior avec 20 ans d'expérience.
Tu analyses les actualités financières avec précision et profondeur.
Réponds en français, de manière fluide et professionnelle.
Ne mets PAS de balises de raisonnement, commence directement par l'analyse.
SOIS CONCIS: 5-7 phrases maximum."""
    
    try:
        if not ANTHROPIC_API_KEY:
            print(f"   ⚠️ ANTHROPIC_API_KEY manquante - Fallback Ollama")
            return _fallback_ollama_news(prompt, category, articles)
        
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=60)
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            summary_text = result["content"][0]["text"] if "content" in result else ""
            
            print(f"   ✅ Résumé reçu: {len(summary_text)} chars")
            return {
                'summary': summary_text,
                'article_count': len(articles),
                'sources': list(set(a['source'] for a in articles[:5])),
                'generated_at': datetime.now().isoformat()
            }
        else:
            error_msg = response.text[:200] if hasattr(response, 'text') else str(response)
            print(f"   ❌ Erreur Claude API: {error_msg}")
            print(f"   🔄 Fallback vers Ollama...")
            return _fallback_ollama_news(prompt, category, articles)
    except Exception as e:
        print(f"   ❌ Exception Claude: {e}")
        print(f"   🔄 Fallback vers Ollama...")
        return _fallback_ollama_news(prompt, category, articles)
    
    # Fallback
    return {
        'summary': "Points clés: " + " • ".join(a['headline'] for a in articles[:3]),
        'article_count': len(articles),
        'sources': list(set(a['source'] for a in articles[:5])),
        'is_fallback': True
    }


def _fallback_ollama_news(prompt: str, category: str, articles: List[Dict]) -> Dict[str, Any]:
    """
    Fallback vers Ollama local pour génération de résumé news
    """
    try:
        import ollama
        
        # Récupérer config Ollama
        try:
            with open('/app/config.json', 'r') as f:
                config = json.load(f)
                local_model = config.get('model', 'mistral-nemo')
                num_threads = config.get('num_threads', 12)
        except:
            local_model = 'mistral-nemo'
            num_threads = 12
        
        print(f"   🤖 Ollama local: {local_model}")
        
        # Nettoyer le prompt (enlever instructions spécifiques Claude)
        clean_prompt = f"""{prompt}

IMPORTANT: Réponds UNIQUEMENT avec l'analyse demandée. Ne mets PAS de balises <think>. Commence directement par l'analyse."""
        
        response = ollama.chat(
            model=local_model,
            messages=[
                {'role': 'user', 'content': clean_prompt}
            ],
            options={
                'temperature': 0.7,
                'num_predict': 500,
                'num_thread': num_threads
            }
        )
        
        summary_text = response['message']['content'] if 'message' in response else ""
        
        # Nettoyer balises thinking si présentes
        summary_text = summary_text.replace('<think>', '').replace('</think>', '').strip()
        
        print(f"   ✅ Ollama résumé: {len(summary_text)} chars")
        
        return {
            'summary': summary_text,
            'article_count': len(articles),
            'sources': list(set(a['source'] for a in articles[:5])),
            'generated_at': datetime.now().isoformat(),
            'fallback': 'ollama'
        }
        
    except ImportError:
        print(f"   ❌ Module ollama non installé")
        return {
            'summary': "Points clés: " + " • ".join(a['headline'] for a in articles[:3]),
            'article_count': len(articles),
            'sources': list(set(a['source'] for a in articles[:5])),
            'is_fallback': True,
            'error': 'ollama_not_installed'
        }
    except Exception as e:
        print(f"   ❌ Erreur Ollama: {e}")
        return {
            'summary': "Points clés: " + " • ".join(a['headline'] for a in articles[:3]),
            'article_count': len(articles),
            'sources': list(set(a['source'] for a in articles[:5])),
            'is_fallback': True,
            'error': str(e)
        }
