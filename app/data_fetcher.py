"""Récupération des données de marché via Yahoo Finance (CORRIGÉ)"""
import yfinance as yf


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
    Récupère les données enrichies d'une action
    Retourne: (hist_1mo, analysis_data, actions) ou None en cas d'erreur
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 1. Historique
        hist_1mo = stock.history(period="1mo", interval="1d")
        if hist_1mo.empty:
            print(f"⚠️ Aucune donnée historique pour {ticker}")
            return None
        
        # 2. Indicateurs Clés (Dictionnaire personnalisé)
        # Gestion sécurisée des recommendations
        try:
            recos = stock.recommendations
            recos_data = recos.tail(5) if recos is not None and not recos.empty else None
        except Exception:
            recos_data = None
        
        # Gestion sécurisée des news
        try:
            news_data = stock.news[:5] if stock.news else []
        except Exception:
            news_data = []
        
        # Gestion sécurisée du calendar
        try:
            calendar_data = stock.calendar
        except Exception:
            calendar_data = None
        
        # Gestion sécurisée des major_holders
        try:
            major_holders_data = stock.major_holders
        except Exception:
            major_holders_data = None
        
        analysis_data = {
            "info": stock.info,
            "calendar": calendar_data,
            "recommendations": recos_data,
            "major_holders": major_holders_data,
            "news": news_data
        }
        
        # 3. Actions (Dividendes et Splits)
        try:
            actions = stock.actions
        except Exception:
            actions = None
        
        return hist_1mo, analysis_data, actions
    
    except Exception as e:
        print(f"❌ Erreur récupération données enrichies pour {ticker}: {e}")
        return None


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
