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
FRED_API_KEY = os.getenv('FRED_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
GOOGLE_NEWS_ENABLED = os.getenv('GOOGLE_NEWS_ENABLED', 'true').lower() == 'true'

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

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
        
        keywords = ['tech', 'ai', 'artificial intelligence', 'machine learning', 'cloud', 'saas', 'software', 'digital', 'platform']
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
    
    def get_defense_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news défense/aérospatiale"""
        print(f"🛡️ get_defense_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("defense"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['defense', 'aerospace', 'lockheed', 'boeing', 'raytheon', 'military', 'pentagon', 'f-35', 'missile', 'drone', 'northrop', 'general dynamics']
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
            self.cache.set("defense", articles)
            print(f"   ✅ {len(articles)} articles defense mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news defense: {e}")
            return []
    
    def get_healthcare_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news santé/pharma"""
        print(f"🏥 get_healthcare_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("healthcare"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['healthcare', 'pharma', 'pharmaceutical', 'drug', 'fda', 'biotech', 'johnson', 'pfizer', 'eli lilly', 'abbvie', 'medical', 'medicine', 'clinical trial']
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
            self.cache.set("healthcare", articles)
            print(f"   ✅ {len(articles)} articles healthcare mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news healthcare: {e}")
            return []
    
    def get_financial_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news financières/banques"""
        print(f"🏦 get_financial_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("financial"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['bank', 'banking', 'jpmorgan', 'goldman', 'visa', 'mastercard', 'berkshire', 'fed', 'federal reserve', 'interest rate', 'credit', 'loan', 'mortgage', 'financial services']
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
            self.cache.set("financial", articles)
            print(f"   ✅ {len(articles)} articles financial mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news financial: {e}")
            return []
    
    def get_consumer_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news consumer staples"""
        print(f"🛒 get_consumer_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("consumer"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['consumer', 'retail', 'walmart', 'procter', 'gamble', 'coca-cola', 'pepsi', 'staples', 'fmcg', 'cpg', 'consumer goods', 'supermarket']
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
            self.cache.set("consumer", articles)
            print(f"   ✅ {len(articles)} articles consumer mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news consumer: {e}")
            return []
    
    def get_semiconductor_news(self, limit: int = 10) -> List[Dict]:
        """Récupère les news semi-conducteurs spécifiques"""
        print(f"🔬 get_semiconductor_news(limit={limit})")
        
        if not self.is_available():
            print(f"   ⚠️ Client non disponible")
            return []
        
        if cached := self.cache.get("semiconductor"):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        keywords = ['semiconductor', 'chip', 'chipmaker', 'tsmc', 'asml', 'intel', 'amd', 'nvidia', 'micron', 'foundry', 'wafer', 'fabrication', 'node', 'nanometer']
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
            self.cache.set("semiconductor", articles)
            print(f"   ✅ {len(articles)} articles semiconductor mis en cache")
            return articles
        except Exception as e:
            print(f"   ❌ Erreur news semiconductor: {e}")
            return []
    
    def get_google_news(self, query: str, limit: int = 10) -> List[Dict]:
        """Récupère les news via Google News RSS"""
        print(f"📰 get_google_news(query={query}, limit={limit})")
        
        if not GOOGLE_NEWS_ENABLED:
            print(f"   ⚠️ Google News désactivé")
            return []
        
        cache_key = f"google_{query}"
        if cached := self.cache.get(cache_key):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        articles = []
        
        try:
            from gnews import GNews
            
            gnews = GNews(language='en', country='US', max_results=limit)
            raw_articles = gnews.get_news(query)
            
            for item in raw_articles:
                articles.append({
                    'headline': item.get('title', ''),
                    'summary': item.get('description', ''),
                    'source': item.get('publisher', {}).get('title', 'Google News'),
                    'url': item.get('url', ''),
                    'datetime': item.get('published date', datetime.now().isoformat()),
                    'ticker': None
                })
            
            self.cache.set(cache_key, articles)
            print(f"   ✅ {len(articles)} articles Google News mis en cache")
            return articles
            
        except ImportError:
            print(f"   ⚠️ Module gnews non installé - pip install gnews")
            return []
        except Exception as e:
            print(f"   ❌ Erreur Google News: {e}")
            return []
    
    def get_fred_macro_data(self) -> Dict[str, Any]:
        """Récupère les données macro économiques de FRED"""
        print(f"📊 get_fred_macro_data()")
        
        if not FRED_API_KEY:
            print(f"   ⚠️ FRED_API_KEY manquante")
            return {}
        
        if cached := self.cache.get("fred_macro"):
            print(f"   ✅ Cache hit")
            return cached
        
        # Indicateurs clés à surveiller
        indicators = {
            'GDP': 'GDP',                    # PIB
            'UNRATE': 'unemployment',        # Taux chômage
            'CPIAUCSL': 'inflation',         # Inflation CPI
            'DFF': 'fed_funds_rate',         # Taux Fed
            'T10Y2Y': 'yield_curve',         # Courbe 10Y-2Y
            'DEXUSEU': 'eur_usd',           # EUR/USD
            'VIXCLS': 'vix'                  # VIX volatilité
        }
        
        macro_data = {}
        
        try:
            for series_id, label in indicators.items():
                params = {
                    'series_id': series_id,
                    'api_key': FRED_API_KEY,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 1
                }
                
                response = requests.get(FRED_API_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data and data['observations']:
                        obs = data['observations'][0]
                        macro_data[label] = {
                            'value': float(obs['value']) if obs['value'] != '.' else None,
                            'date': obs['date']
                        }
                        print(f"   ✅ {label}: {macro_data[label]['value']}")
                else:
                    print(f"   ⚠️ Erreur FRED {series_id}: {response.status_code}")
            
            self.cache.set("fred_macro", macro_data)
            print(f"   ✅ {len(macro_data)} indicateurs FRED récupérés")
            return macro_data
            
        except Exception as e:
            print(f"   ❌ Erreur FRED: {e}")
            return {}
    
    def get_alpha_vantage_news(self, tickers: List[str] = None, limit: int = 50) -> List[Dict]:
        """Récupère les news via Alpha Vantage (meilleure qualité que Finnhub)"""
        print(f"📈 get_alpha_vantage_news(tickers={tickers}, limit={limit})")
        
        if not ALPHA_VANTAGE_API_KEY:
            print(f"   ⚠️ ALPHA_VANTAGE_API_KEY manquante")
            return []
        
        cache_key = f"alpha_{'_'.join(tickers[:3]) if tickers else 'general'}"
        if cached := self.cache.get(cache_key):
            print(f"   ✅ Cache hit: {len(cached)} articles")
            return cached
        
        articles = []
        
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': ALPHA_VANTAGE_API_KEY,
                'limit': limit
            }
            
            # Ajouter tickers si fournis
            if tickers:
                params['tickers'] = ','.join(tickers[:10])  # Max 10 tickers
            
            response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'feed' in data:
                    for item in data['feed']:
                        # Sentiment score de -1 à 1
                        sentiment_score = float(item.get('overall_sentiment_score', 0))
                        sentiment_label = item.get('overall_sentiment_label', 'Neutral')
                        
                        articles.append({
                            'headline': item.get('title', ''),
                            'summary': item.get('summary', '')[:300],
                            'source': item.get('source', 'Alpha Vantage'),
                            'url': item.get('url', ''),
                            'datetime': item.get('time_published', datetime.now().isoformat()),
                            'ticker': None,
                            'sentiment_score': sentiment_score,
                            'sentiment_label': sentiment_label,
                            'relevance_score': float(item.get('relevance_score', 0)) if 'relevance_score' in item else None
                        })
                
                self.cache.set(cache_key, articles)
                print(f"   ✅ {len(articles)} articles Alpha Vantage récupérés")
                return articles
            else:
                print(f"   ⚠️ Erreur Alpha Vantage: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Erreur Alpha Vantage: {e}")
            import traceback
            traceback.print_exc()
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
    Génère un résumé IA des actualités en français avec sources multiples.
    
    Args:
        tickers: Liste des tickers suivis
        category: 'my_stocks', 'market', 'tech', 'defense', 'healthcare', 'financial', 'consumer', 'semiconductor', ou 'all'
    """
    print(f"\n{'='*50}")
    print(f"🤖 generate_news_summary(tickers={tickers}, category={category})")
    print(f"{'='*50}")
    
    fetcher = get_news_fetcher()
    
    if not fetcher.is_available():
        print("❌ News service non disponible")
        return {'success': False, 'error': 'News service unavailable', 'summaries': {}}
    
    # Collecter les articles par catégorie avec sources multiples
    news = {
        'my_stocks': [],
        'market': fetcher.get_market_news(),
        'tech': fetcher.get_tech_news(),
        'defense': fetcher.get_defense_news(),
        'healthcare': fetcher.get_healthcare_news(),
        'financial': fetcher.get_financial_news(),
        'consumer': fetcher.get_consumer_news(),
        'semiconductor': fetcher.get_semiconductor_news()
    }
    
    # Enrichir avec Alpha Vantage (meilleure qualité + sentiment analysis)
    if ALPHA_VANTAGE_API_KEY:
        print("\n📈 Enrichissement avec Alpha Vantage...")
        alpha_news = fetcher.get_alpha_vantage_news(tickers=tickers, limit=30)
        if alpha_news:
            print(f"   ✅ {len(alpha_news)} articles Alpha Vantage (avec sentiment)")
            # Ajouter aux catégories appropriées
            for article in alpha_news:
                text = (article['headline'] + article['summary']).lower()
                
                # Classifier par secteur
                if any(t.lower() in text for t in tickers):
                    news['my_stocks'].append(article)
                
                # Tech keywords
                if any(kw in text for kw in ['tech', 'ai', 'cloud', 'software']):
                    news['tech'].append(article)
                
                # Defense keywords
                if any(kw in text for kw in ['defense', 'aerospace', 'military']):
                    news['defense'].append(article)
                
                # Healthcare keywords
                if any(kw in text for kw in ['health', 'pharma', 'drug', 'fda']):
                    news['healthcare'].append(article)
                
                # Financial keywords
                if any(kw in text for kw in ['bank', 'fed', 'rate', 'visa', 'mastercard']):
                    news['financial'].append(article)
                
                # Consumer keywords
                if any(kw in text for kw in ['consumer', 'retail', 'walmart']):
                    news['consumer'].append(article)
                
                # Semiconductor keywords
                if any(kw in text for kw in ['chip', 'semiconductor', 'tsmc', 'asml']):
                    news['semiconductor'].append(article)
    
    # Enrichir avec Google News pour certaines catégories
    if GOOGLE_NEWS_ENABLED:
        print("\n📰 Enrichissement avec Google News...")
        
        google_queries = {
            'tech': 'artificial intelligence technology stocks',
            'defense': 'defense aerospace contracts',
            'semiconductor': 'semiconductor chips TSMC ASML',
            'healthcare': 'pharmaceutical FDA approval',
            'financial': 'federal reserve interest rates banks'
        }
        
        for cat, query in google_queries.items():
            if cat in news:
                google_articles = fetcher.get_google_news(query, limit=5)
                if google_articles:
                    print(f"   ✅ {len(google_articles)} articles Google News pour {cat}")
                    news[cat].extend(google_articles)
    
    # Récupérer données macro FRED
    macro_data = {}
    if FRED_API_KEY and category in ['all', 'market', 'financial']:
        print("\n📊 Récupération données macro FRED...")
        macro_data = fetcher.get_fred_macro_data()
        if macro_data:
            print(f"   ✅ {len(macro_data)} indicateurs macro récupérés")
    
    # News des actions suivies (Finnhub)
    for ticker in tickers:
        for article in fetcher.get_company_news(ticker)[:8]:
            news['my_stocks'].append(article)
    
    # Dédupliquer et trier
    for cat in news:
        # Supprimer doublons par URL
        seen_urls = set()
        unique_articles = []
        for article in news[cat]:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        # Trier par date
        news[cat] = sorted(unique_articles, key=lambda x: x.get('datetime', ''), reverse=True)
    
    # Limiter nombre d'articles par catégorie
    max_articles_limits = {
        'my_stocks': 25,
        'market': 20,
        'tech': 20,
        'defense': 15,
        'healthcare': 15,
        'financial': 20,
        'consumer': 15,
        'semiconductor': 20
    }
    
    for cat, limit in max_articles_limits.items():
        if cat in news:
            news[cat] = news[cat][:limit]
    
    # Générer les résumés
    all_categories = ['my_stocks', 'market', 'tech', 'defense', 'healthcare', 'financial', 'consumer', 'semiconductor']
    categories = all_categories if category == 'all' else [category]
    summaries = {}
    
    print(f"\n📊 Articles collectés (après enrichissement):")
    for cat, arts in news.items():
        print(f"   {cat}: {len(arts)} articles")
    
    for cat in categories:
        articles = news.get(cat, [])
        if not articles:
            print(f"\n⚠️ Pas d'articles pour {cat}")
            summaries[cat] = {'summary': "Aucune actualité disponible.", 'article_count': 0}
            continue
        
        print(f"\n🔄 Génération résumé pour {cat} ({len(articles)} articles)...")
        summaries[cat] = _generate_summary(cat, articles, tickers, macro_data)
        print(f"   ✅ Résumé généré: {len(summaries[cat].get('summary', ''))} chars")
    
    print(f"\n✅ Tous les résumés générés")
    return {
        'success': True,
        'summaries': summaries,
        'generated_at': datetime.now().isoformat(),
        'sources': {
            'finnhub': bool(FINNHUB_API_KEY),
            'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY),
            'google_news': GOOGLE_NEWS_ENABLED,
            'fred': bool(FRED_API_KEY)
        },
        'macro_data': macro_data if macro_data else None
    }


def _generate_summary(category: str, articles: List[Dict], tickers: List[str], macro_data: Dict = None) -> Dict[str, Any]:
    """Génère un résumé IA pour une catégorie avec données macro optionnelles"""
    from config import CLAUDE_CONFIG
    
    # Adapter le nombre d'articles selon la catégorie
    max_articles = {
        'my_stocks': 20,
        'market': 20,
        'tech': 20,
        'defense': 15,
        'healthcare': 15,
        'financial': 20,
        'consumer': 15,
        'semiconductor': 20
    }
    article_limit = max_articles.get(category, 15)
    
    # Contexte des articles avec sentiment si disponible
    context_parts = []
    for a in articles[:article_limit]:
        base = f"• [{a.get('source', 'Unknown')}] {a['headline']} — {a['summary'][:200]}"
        
        # Ajouter sentiment si disponible (Alpha Vantage)
        if 'sentiment_label' in a and a.get('sentiment_score') is not None:
            sentiment = a['sentiment_label']
            score = a['sentiment_score']
            base += f" [Sentiment: {sentiment} {score:+.2f}]"
        
        context_parts.append(base)
    
    context = "\n".join(context_parts)
    
    # Ajouter contexte macro si disponible
    macro_context = ""
    if macro_data and category in ['market', 'financial']:
        macro_context = "\n\nDONNÉES MACRO (FRED):\n"
        if 'unemployment' in macro_data and macro_data['unemployment']['value']:
            macro_context += f"• Chômage: {macro_data['unemployment']['value']:.1f}%\n"
        if 'inflation' in macro_data and macro_data['inflation']['value']:
            macro_context += f"• Inflation CPI: {macro_data['inflation']['value']:.1f}\n"
        if 'fed_funds_rate' in macro_data and macro_data['fed_funds_rate']['value']:
            macro_context += f"• Taux Fed: {macro_data['fed_funds_rate']['value']:.2f}%\n"
        if 'yield_curve' in macro_data and macro_data['yield_curve']['value']:
            curve = macro_data['yield_curve']['value']
            macro_context += f"• Courbe 10Y-2Y: {curve:+.2f}% {'(inversée)' if curve < 0 else '(normale)'}\n"
        if 'vix' in macro_data and macro_data['vix']['value']:
            macro_context += f"• VIX: {macro_data['vix']['value']:.1f}\n"
    
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
{context}{macro_context}

FOURNIS (5-7 phrases MAX):
1. Indices principaux (1 phrase)
2. Facteurs macro (Fed, inflation, emploi) - utilise données FRED (1 phrase)
3. Secteurs leaders/retardataires (1 phrase)
4. Événements clés (1 phrase)
5. Perspective court terme avec VIX et courbe (1 phrase)

Sois CONCIS.""",

        'tech': f"""Analyse l'actualité tech.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. GAFAM & mega-caps (1 phrase)
2. Tendances IA/cloud (1 phrase)
3. Valorisations (1 phrase)
4. Perspective (1 phrase)

Sois CONCIS.""",

        'defense': f"""Analyse l'actualité défense et aérospatiale.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. Contrats majeurs et commandes (1 phrase)
2. Géopolitique et budgets (1 phrase)
3. Performances des leaders (LMT, RTX, BA, GD, NOC) (1 phrase)
4. Perspective secteur (1 phrase)

Sois CONCIS.""",

        'healthcare': f"""Analyse l'actualité santé et pharma.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. Approbations FDA et essais cliniques (1 phrase)
2. Performances des leaders (JNJ, UNH, ABBV, LLY) (1 phrase)
3. Tendances réglementaires (1 phrase)
4. Perspective secteur (1 phrase)

Sois CONCIS.""",

        'financial': f"""Analyse l'actualité financière et bancaire.

ACTUALITÉS:
{context}{macro_context}

FOURNIS (5-7 phrases MAX):
1. Banques et résultats (JPM, etc.) (1 phrase)
2. Politique Fed et taux - utilise données FRED (1 phrase)
3. Paiements (Visa, Mastercard) (1 phrase)
4. Perspective secteur (1 phrase)

Sois CONCIS.""",

        'consumer': f"""Analyse l'actualité biens de consommation.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. Performances retail (WMT, etc.) (1 phrase)
2. Marques FMCG (PG, KO, PEP) (1 phrase)
3. Tendances consommation (1 phrase)
4. Perspective secteur (1 phrase)

Sois CONCIS.""",

        'semiconductor': f"""Analyse l'actualité semi-conducteurs.

ACTUALITÉS:
{context}

FOURNIS (5-7 phrases MAX):
1. Leaders (NVDA, AMD, INTC, MU) (1 phrase)
2. Équipements (ASML) et fonderies (1 phrase)
3. Demande IA et cycles (1 phrase)
4. Perspective secteur (1 phrase)

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
            
            # Calculer sentiment moyen si disponible
            avg_sentiment = None
            sentiment_articles = [a for a in articles if 'sentiment_score' in a and a['sentiment_score'] is not None]
            if sentiment_articles:
                avg_sentiment = sum(a['sentiment_score'] for a in sentiment_articles) / len(sentiment_articles)
            
            return {
                'summary': summary_text,
                'article_count': len(articles),
                'sources': list(set(a['source'] for a in articles[:5])),
                'generated_at': datetime.now().isoformat(),
                'avg_sentiment': round(avg_sentiment, 3) if avg_sentiment is not None else None,
                'macro_included': bool(macro_context)
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
        
        # Nettoyer le prompt
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
        
        # Nettoyer balises thinking
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
