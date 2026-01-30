"""Récupération des données de marché - Multi-sources enrichies"""
import yfinance as yf
import requests
import feedparser
import os
from datetime import datetime

# API Keys
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
FRED_API_KEY = os.getenv('FRED_API_KEY', '')

# Cache global pour données macro (1x par session)
_macro_cache = None


def fetch_stock_data(ticker):
    """
    Récupère les données historiques d'une action
    Retourne: (hist_5d, hist_1mo, hist_3mo, info) ou None en cas d'erreur
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Données sur différentes périodes
        hist_5d = stock.history(period="5d", interval="1h")
        hist_1mo = stock.history(period="1mo", interval="1d")
        hist_3mo = stock.history(period="3mo", interval="1d")
        
        if hist_5d.empty:
            print(f"⚠️ Aucune donnée disponible pour {ticker}")
            return None
        
        info = stock.info
        return hist_5d, hist_1mo, hist_3mo, info
    
    except Exception as e:
        print(f"❌ Erreur récupération données pour {ticker}: {e}")
        return None


def fetch_enhanced_stock_data(ticker):
    """
    Récupère les données enrichies d'une action - MULTI-SOURCES
    Retourne: (hist_1mo, analysis_data, actions) ou None en cas d'erreur
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 1. Historique
        hist_1mo = stock.history(period="1mo", interval="1d")
        if hist_1mo.empty:
            print(f"⚠️ Aucune donnée historique pour {ticker}")
            return None
        
        # 2. Recommandations (sécurisé)
        try:
            recos = stock.recommendations
            recos_data = recos.tail(5) if recos is not None and not recos.empty else None
        except:
            recos_data = None
        
        # 3. News Yahoo (fallback si Google échoue)
        try:
            yahoo_news = stock.news[:5] if stock.news else []
        except:
            yahoo_news = []
        
        # 4. Calendar
        try:
            calendar_data = stock.calendar
        except:
            calendar_data = None
        
        # 5. Major holders
        try:
            major_holders_data = stock.major_holders
        except:
            major_holders_data = None
        
        # === NOUVELLES SOURCES ===
        
        # 6. Google News RSS (prioritaire)
        company_name = stock.info.get('longName') if hasattr(stock, 'info') else None
        google_news = fetch_google_news(ticker, company_name)
        
        # Combiner news (Google prioritaire, Yahoo en fallback)
        all_news = google_news if google_news else yahoo_news
        
        # 7. Alpha Vantage (fondamentaux détaillés)
        alpha_vantage_data = fetch_alpha_vantage_overview(ticker)
        
        # 8. FRED (macro - 1x par session)
        fred_data = fetch_fred_macro()
        
        analysis_data = {
            "info": stock.info,
            "calendar": calendar_data,
            "recommendations": recos_data,
            "major_holders": major_holders_data,
            "news": all_news,
            "alpha_vantage": alpha_vantage_data,  # NOUVEAU
            "fred_macro": fred_data  # NOUVEAU
        }
        
        # 9. Actions (Dividendes et Splits)
        try:
            actions = stock.actions
        except:
            actions = None
        
        return hist_1mo, analysis_data, actions
    
    except Exception as e:
        print(f"❌ Erreur récupération données enrichies pour {ticker}: {e}")
        return None


def fetch_google_news(ticker, company_name=None):
    """
    Récupère les actualités depuis Google News RSS (gratuit)
    
    Returns:
        list: Liste de news ou [] si erreur
    """
    try:
        import urllib.parse
        
        query = company_name if company_name else ticker.replace('.', ' ')
        # Encoder l'URL pour gérer les espaces et caractères spéciaux
        encoded_query = urllib.parse.quote(f"{query} stock")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(url)
        news_list = []
        
        for entry in feed.entries[:10]:
            news_list.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')
            })
        
        if news_list:
            print(f"  ✅ Google News: {len(news_list)} articles")
        return news_list
    except Exception as e:
        print(f"  ⚠️ Google News erreur: {e}")
        return []


def fetch_alpha_vantage_overview(ticker):
    """
    Récupère données Alpha Vantage (25/jour gratuit)
    
    Returns:
        dict ou None
    """
    if not ALPHA_VANTAGE_API_KEY:
        return None
    
    try:
        clean_ticker = ticker.split('.')[0]
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'OVERVIEW',
            'symbol': clean_ticker,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Symbol' in data:
            print(f"  ✅ Alpha Vantage: Fondamentaux détaillés")
            return {
                'pe_ratio': data.get('PERatio'),
                'peg_ratio': data.get('PEGRatio'),
                'profit_margin': data.get('ProfitMargin'),
                'operating_margin': data.get('OperatingMarginTTM'),
                'roe': data.get('ReturnOnEquityTTM'),
                'debt_to_equity': data.get('DebtToEquity')
            }
        return None
    except Exception as e:
        print(f"  ⚠️ Alpha Vantage erreur: {e}")
        return None


def fetch_fred_macro():
    """
    Récupère indicateurs macro US depuis FRED (gratuit)
    Cache pour éviter appels répétés
    
    Returns:
        dict ou {}
    """
    global _macro_cache
    
    if _macro_cache is not None:
        return _macro_cache
    
    if not FRED_API_KEY:
        _macro_cache = {}
        return {}
    
    try:
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        series_ids = {
            'fed_funds_rate': 'DFF',
            'inflation': 'CPIAUCSL',
            'unemployment': 'UNRATE',
            '10y_treasury': 'DGS10'
        }
        
        macro_data = {}
        for name, series_id in series_ids.items():
            try:
                params = {
                    'series_id': series_id,
                    'api_key': FRED_API_KEY,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 1
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'observations' in data and data['observations']:
                    obs = data['observations'][0]
                    value = obs.get('value', '.')
                    macro_data[name] = {
                        'value': float(value) if value != '.' else None,
                        'date': obs.get('date')
                    }
            except:
                continue
        
        if macro_data:
            print(f"  ✅ FRED: {len(macro_data)} indicateurs macro")
        
        _macro_cache = macro_data
        return macro_data
    except Exception as e:
        print(f"  ⚠️ FRED erreur: {e}")
        _macro_cache = {}
        return {}


def calculate_variations(hist_5d, hist_1mo):
    """
    Calcule les variations de prix sur 1 jour et 1 mois
    
    Args:
        hist_5d: DataFrame avec données horaires sur 5 jours
        hist_1mo: DataFrame avec données journalières sur 1 mois
    
    Returns:
        tuple: (variation_1_jour, variation_1_mois) en pourcentage
    """
    var_1d = 0.0
    var_1mo = 0.0
    
    try:
        # Variation sur 1 jour (données horaires)
        if hist_5d is not None and not hist_5d.empty and len(hist_5d) >= 2:
            # Pour les données horaires, on compare avec la clôture du jour précédent
            # Regrouper par jour pour avoir les clôtures journalières
            daily_closes = hist_5d['Close'].resample('D').last().dropna()
            
            if len(daily_closes) >= 2:
                var_1d = ((daily_closes.iloc[-1] - daily_closes.iloc[-2]) / 
                          daily_closes.iloc[-2] * 100)
            else:
                # Alternative: comparer première et dernière valeur
                var_1d = ((hist_5d['Close'].iloc[-1] - hist_5d['Close'].iloc[0]) / 
                          hist_5d['Close'].iloc[0] * 100)
        
        # Variation sur 1 mois (données journalières)
        if hist_1mo is not None and not hist_1mo.empty and len(hist_1mo) >= 2:
            var_1mo = ((hist_1mo['Close'].iloc[-1] - hist_1mo['Close'].iloc[0]) / 
                       hist_1mo['Close'].iloc[0] * 100)
        
        return float(var_1d), float(var_1mo)
    
    except Exception as e:
        print(f"⚠️ Erreur calcul variations: {e}")
        return 0.0, 0.0


def get_current_price(ticker):
    """
    Récupère le prix actuel d'une action
    
    Args:
        ticker: Symbole de l'action
    
    Returns:
        float: Prix actuel ou None en cas d'erreur
    """
    try:
        stock = yf.Ticker(ticker)
        # Essayer d'abord avec regularMarketPrice
        price = stock.info.get('regularMarketPrice')
        if price is None:
            # Fallback sur le dernier prix de clôture
            hist = stock.history(period="1d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
        return price
    except Exception as e:
        print(f"⚠️ Erreur récupération prix pour {ticker}: {e}")
        return None
