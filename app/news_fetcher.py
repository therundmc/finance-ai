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
        for article in fetcher.get_company_news(ticker)[:5]:
            news['my_stocks'].append(article)
    news['my_stocks'] = sorted(news['my_stocks'], key=lambda x: x['datetime'], reverse=True)[:15]
    
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
        used_count = min(len(articles), 8)
        print(f"\n🔄 Génération résumé pour {cat} ({used_count}/{len(articles)} articles)...")
        summaries[cat] = _generate_summary(cat, articles, tickers)
        print(f"   ✅ Résumé généré: {len(summaries[cat].get('summary', ''))} chars")
    
    print(f"\n✅ Tous les résumés générés")
    return {'success': True, 'summaries': summaries, 'generated_at': datetime.now().isoformat()}


def _generate_summary(category: str, articles: List[Dict], tickers: List[str]) -> Dict[str, Any]:
    """Génère un résumé IA pour une catégorie"""
    
    # Contexte des articles - filtrer et formater proprement (limité à 8 pour rapidité)
    context = "\n".join([
        f"• [{a.get('source', 'Unknown')}] {a['headline']} — {a['summary'][:200]}"
        for a in articles[:8]
    ])
    
    # Instructions selon la catégorie
    tickers_str = ', '.join(tickers[:5])
    
    prompts = {
        'my_stocks': f"""Tu es un analyste financier senior avec 20 ans d'expérience. Analyse en profondeur ces actualités concernant mon portefeuille d'actions ({tickers_str}).

ACTUALITÉS À ANALYSER:
{context}

ANALYSE REQUISE:
1. **Synthèse des événements majeurs** : Identifie les 2-3 actualités les plus impactantes pour ces actions
2. **Impact sur les cours** : Explique comment ces nouvelles pourraient affecter les prix à court terme (1-5 jours) et moyen terme (1-3 mois)
3. **Catalyseurs identifiés** : Repère les éléments qui pourraient déclencher des mouvements (earnings, annonces, rumeurs M&A, etc.)
4. **Risques à surveiller** : Mentionne les menaces potentielles ou signaux d'alerte
5. **Sentiment de marché** : Évalue le sentiment global (très haussier/haussier/neutre/baissier/très baissier) avec justification

FORMAT: Rédige 5-7 phrases fluides en français, sans listes à puces. Sois précis avec les chiffres et pourcentages quand disponibles.

ANALYSE:""",

        'market': f"""Tu es un stratégiste de marché senior. Analyse l'état actuel des marchés financiers mondiaux.

ACTUALITÉS À ANALYSER:
{context}

ANALYSE REQUISE:
1. **Tendance des indices** : État du S&P 500, Nasdaq, Dow Jones, et marchés européens
2. **Facteurs macro-économiques** : Politique monétaire (Fed, BCE), inflation, emploi, croissance
3. **Secteurs en mouvement** : Identifie les secteurs leaders et retardataires du jour
4. **Événements clés** : Rappelle les catalyseurs importants (earnings saison, données économiques, géopolitique)
5. **Volatilité et sentiment** : VIX, flux institutionnels, sentiment des investisseurs
6. **Perspective court terme** : Ton avis sur la direction probable des prochains jours

FORMAT: Rédige 5-7 phrases fluides en français, sans listes à puces. Utilise des données chiffrées quand disponibles.

ANALYSE:""",

        'tech': f"""Tu es un analyste spécialisé dans le secteur technologique. Analyse en profondeur l'actualité tech et son impact boursier.

ACTUALITÉS À ANALYSER:
{context}

ANALYSE REQUISE:
1. **GAFAM & Mega-caps** : Actualités Apple, Microsoft, Google, Amazon, Meta, Nvidia, Tesla
2. **Semiconducteurs** : État du secteur (Nvidia, AMD, Intel, TSMC, ASML) et chaîne d'approvisionnement
3. **Intelligence Artificielle** : Développements IA, investissements, compétition, régulation
4. **Cloud & SaaS** : Tendances du cloud computing et software
5. **Startups & IPO** : Mouvements notables dans l'écosystème tech
6. **Valorisations** : Commentaire sur les multiples du secteur et risques de correction
7. **Perspective** : Ton avis sur l'attractivité du secteur tech actuellement

FORMAT: Rédige 5-7 phrases fluides en français, sans listes à puces. Mentionne les variations de cours quand pertinent.

ANALYSE:"""
    }
    
    prompt = prompts.get(category, prompts['market'])

    model = _get_claude_model()
    print(f"   🤖 Appel Claude API avec modèle {model}")
    
    # System prompt pour Claude
    system_prompt = """Tu es un analyste financier senior avec 20 ans d'expérience.
Tu analyses les actualités financières avec précision et profondeur.
Réponds en français, de manière fluide et professionnelle.
Ne mets PAS de balises de raisonnement, commence directement par l'analyse."""
    
    try:
        if not ANTHROPIC_API_KEY:
            print(f"   ❌ ANTHROPIC_API_KEY manquante")
            return {
                'summary': "Clé API Claude manquante. Configurer ANTHROPIC_API_KEY dans .env",
                'article_count': len(articles),
                'error': 'missing_api_key'
            }
        
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": model,
            "max_tokens": 1000,
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
    except Exception as e:
        print(f"   ❌ Exception génération résumé: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback
    return {
        'summary': "Points clés: " + " • ".join(a['headline'] for a in articles[:3]),
        'article_count': len(articles),
        'sources': list(set(a['source'] for a in articles[:5])),
        'is_fallback': True
    }
