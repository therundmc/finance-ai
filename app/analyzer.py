"""Script principal d'analyse financière - Version Enhanced avec Market Hours"""
import os
import json
from datetime import datetime, time as dtime
from concurrent.futures import ThreadPoolExecutor
import time
import pytz

from config import load_config
from data_fetcher import fetch_stock_data, fetch_enhanced_stock_data, calculate_variations
from indicators import get_technical_indicators
from ai_analysis import build_analysis_prompt, generate_analysis, generate_portfolio_analysis, generate_market_summary
from signal_extractor import extract_signal_from_analysis, validate_signal, format_structured_analysis
from database import (
    save_analysis, init_db, save_all_news_summaries, get_last_analysis_times, 
    get_last_batch_analysis_date, set_last_batch_analysis_date,
    get_positions, get_latest_analyses, save_portfolio_analysis
)

# Import conditionnel news_fetcher
try:
    from news_fetcher import generate_news_summary
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("⚠️ News module non disponible")


# ============================================
# MARKET HOURS CONFIGURATION
# ============================================
MARKET_SCHEDULES = {
    'US': {
        'timezone': 'America/New_York',
        'open': dtime(9, 30),   # 9:30 AM ET
        'close': dtime(16, 0),   # 4:00 PM ET
        'suffixes': ['', '.US'],  # No suffix or .US
        'name': 'NYSE/NASDAQ',
        'currency': 'USD',
        'currency_symbol': '$'
    },
    'CH': {
        'timezone': 'Europe/Zurich',
        'open': dtime(9, 0),     # 9:00 AM CET
        'close': dtime(17, 30),  # 5:30 PM CET
        'suffixes': ['.SW', '.VX'],
        'name': 'SIX Swiss Exchange',
        'currency': 'CHF',
        'currency_symbol': 'CHF '
    },
    'EU': {
        'timezone': 'Europe/Paris',
        'open': dtime(9, 0),
        'close': dtime(17, 30),
        'suffixes': ['.PA', '.DE', '.AS'],
        'name': 'Euronext',
        'currency': 'EUR',
        'currency_symbol': '€'
    },
    'UK': {
        'timezone': 'Europe/London',
        'open': dtime(8, 0),
        'close': dtime(16, 30),
        'suffixes': ['.L'],
        'name': 'London Stock Exchange',
        'currency': 'GBP',
        'currency_symbol': '£'
    }
}


def get_ticker_currency(ticker):
    """Retourne la devise d'une action basée sur son suffixe"""
    market = get_ticker_market(ticker)
    config = MARKET_SCHEDULES.get(market, MARKET_SCHEDULES['US'])
    return {
        'currency': config.get('currency', 'USD'),
        'symbol': config.get('currency_symbol', '$')
    }


def get_ticker_market(ticker):
    """Détermine le marché d'une action basé sur son suffixe"""
    ticker_upper = ticker.upper()
    
    for market, config in MARKET_SCHEDULES.items():
        for suffix in config['suffixes']:
            if suffix and ticker_upper.endswith(suffix.upper()):
                return market
    
    # Par défaut, considérer comme US si pas de suffixe spécial
    return 'US'


def categorize_tickers_by_market(tickers):
    """Catégorise les tickers par marché"""
    by_market = {}
    for ticker in tickers:
        market = get_ticker_market(ticker)
        if market not in by_market:
            by_market[market] = []
        by_market[market].append(ticker)
    return by_market


def get_market_schedule_times(market):
    """Retourne les heures d'analyse pour un marché en heure locale (Zurich)"""
    config = MARKET_SCHEDULES.get(market)
    if not config:
        return []
    
    market_tz = pytz.timezone(config['timezone'])
    zurich_tz = pytz.timezone('Europe/Zurich')
    
    # Créer datetime pour aujourd'hui avec les heures d'open/close
    today = datetime.now(market_tz).date()
    
    # Open time
    open_dt = market_tz.localize(datetime.combine(today, config['open']))
    open_zurich = open_dt.astimezone(zurich_tz)
    
    # Close time
    close_dt = market_tz.localize(datetime.combine(today, config['close']))
    close_zurich = close_dt.astimezone(zurich_tz)
    
    # Retourner les heures en format HH:MM pour le scheduler
    return [
        {'time': open_zurich.strftime('%H:%M'), 'event': 'open', 'market': market},
        {'time': close_zurich.strftime('%H:%M'), 'event': 'close', 'market': market}
    ]


def is_market_day():
    """Vérifie si c'est un jour de trading (lun-ven)"""
    return datetime.now().weekday() < 5


def analyze_stock(ticker, model, advanced=False, num_threads=12):
    """Analyse une action avec approche HYBRIDE (Haiku → Sonnet)"""
    print(f"\n{'='*60}")
    print(f"📊 Analyse HYBRIDE de {ticker} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        # 1. Récupérer les données enrichies (MULTI-SOURCES)
        enhanced_data = fetch_enhanced_stock_data(ticker)
        if not enhanced_data:
            print(f"⚠️ Impossible de récupérer les données enrichies pour {ticker}")
            return None

        hist_1mo, analysis_data, actions = enhanced_data

        # 2. Récupérer les données standard
        stock_data = fetch_stock_data(ticker)
        if not stock_data:
            print(f"⚠️ Impossible de récupérer les données pour {ticker}")
            return None

        hist_5d, hist_1mo_standard, hist_3mo, info_standard = stock_data

        # Extraction des composants
        info = analysis_data.get("info", {})
        news = analysis_data.get("news", [])
        calendar = analysis_data.get("calendar", None)
        recos = analysis_data.get("recommendations", None)
        alpha_vantage = analysis_data.get("alpha_vantage", None)  # NOUVEAU
        fred_macro = analysis_data.get("fred_macro", None)  # NOUVEAU

        # 3. Calculer variations pour screening
        current_price = float(hist_1mo['Close'].iloc[-1]) if not hist_1mo.empty else 0
        if len(hist_1mo) >= 2:
            monthly_change = ((current_price - hist_1mo['Close'].iloc[0]) / hist_1mo['Close'].iloc[0] * 100)
        else:
            monthly_change = 0

        # === PHASE 1: SCREENING HAIKU ===
        from config import load_config
        from ai_analysis import screen_with_haiku
        
        config = load_config()
        use_screening = config.get('use_claude', True) and config.get('screening_threshold') is not None
        
        if use_screening:
            screening_result = screen_with_haiku(ticker, analysis_data, current_price, monthly_change)
            
            # Si score < seuil, skip analyse approfondie
            if not screening_result['should_analyze']:
                print(f"⏭️  Score {screening_result['score']}/100 < seuil - Analyse approfondie skippée")
                print(f"   Raison: {screening_result['reason']}")
                
                # Retourner analyse minimale pour DB
                signal_info = {
                    'signal': 'NEUTRE',
                    'confidence': 'Faible',
                    'summary': f"Screening: {screening_result['reason']}",
                    'structured_data': None
                }
                
                var_1d, var_1mo = calculate_variations(hist_5d, hist_1mo)
                currency_info = get_ticker_currency(ticker)
                
                # Sauvegarder quand même en DB (avec flag screening)
                if config.get('save_history', True):
                    analysis_data_db = {
                        'ticker': ticker,
                        'timestamp': datetime.now(),
                        'price': current_price,
                        'change_1d': var_1d,
                        'change_1mo': var_1mo,
                        'model': f"haiku-screening-{screening_result['score']}",
                        'analysis_time': screening_result['screening_time'],
                        'signal': signal_info['signal'],
                        'confidence': signal_info['confidence'],
                        'summary': signal_info['summary'],
                        'news_analyzed': len(news),
                        'analysis': f"Screening Haiku: Score {screening_result['score']}/100\n{screening_result['reason']}",
                        'raw_response': screening_result['reason'],
                        'currency': currency_info['currency'],
                        'sector': info.get('sector', 'N/A')
                    }
                    
                    save_analysis(analysis_data_db)
                
                return None  # Skip deep analysis
        
        # === PHASE 2: ANALYSE APPROFONDIE SONNET ===
        print(f"✅ Score screening suffisant - Analyse approfondie Sonnet")

        # Small delay between screening and deep analysis to respect rate limits
        time.sleep(5)

        # 4. Calculer les indicateurs techniques
        indicators = get_technical_indicators(hist_1mo)

        # 5. Construire le prompt (avec nouvelles sources)
        context = build_analysis_prompt(
            ticker=ticker,
            hist_1mo=hist_1mo,
            info=info,
            indicators=indicators,
            advanced=advanced,
            news=news,
            calendar=calendar,
            recommendations=recos,
            alpha_vantage=alpha_vantage,  # NOUVEAU
            fred_macro=fred_macro  # NOUVEAU
        )

        # 6. Générer l'analyse IA (Sonnet)
        analysis_text, elapsed_time = generate_analysis(ticker, model, context, num_threads)

        if not analysis_text:
            return None

        # 7. Extraire le signal et résumé
        signal_info = extract_signal_from_analysis(analysis_text)
        signal_info = validate_signal(signal_info)
        
        structured_data = signal_info.get('structured_data')
        if structured_data:
            formatted_text = format_structured_analysis(structured_data)
            print(f"\n✅ Analyse JSON structurée reçue")
        else:
            formatted_text = analysis_text
            print(f"\n⚠️ Fallback mode regex (format texte)")

        # 8. Afficher les résultats
        print(f"\n{formatted_text if formatted_text else analysis_text}")
        print(f"\n⏱️ Temps d'analyse: {elapsed_time:.1f}s")
        print(f"🎯 Signal: {signal_info['signal']} (Conviction: {signal_info['confidence']})")
        print(f"💡 Résumé: {signal_info['summary']}")

        # 9. Calculer variations
        var_1d, var_1mo = calculate_variations(hist_5d, hist_1mo)

        print(f"📈 Variation 1j: {var_1d:.2f}% | Variation 1m: {var_1mo:.2f}%")

        # 10. Récupérer devise
        currency_info = get_ticker_currency(ticker)

        # 10. Sauvegarder les résultats complets
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'price': current_price,
            'currency': currency_info['currency'],
            'currency_symbol': currency_info['symbol'],
            'change_1d': var_1d,
            'change_1mo': var_1mo,
            'model': model,
            'analysis_time': elapsed_time,
            'indicators': indicators,
            'signal': signal_info['signal'],
            'confidence': signal_info['confidence'],
            'summary': signal_info['summary'],
            'news_analyzed': len(news) if news else 0,
            'analysis': formatted_text if formatted_text else analysis_text,
            'structured_data': structured_data,  # Données JSON structurées si disponibles
            'raw_response': analysis_text,  # Réponse brute pour debug
            'sector': info.get('sector', 'N/A')
        }

        # Sauvegarder en base de données SQLite
        saved = save_analysis(result)
        if saved:
            print(f"💾 Sauvegardé en DB: {ticker} (ID: {saved.id})")
        else:
            print(f"⚠️ Échec sauvegarde DB pour {ticker}")

        return result

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse de {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_news_summaries(force: bool = False):
    """
    Génère et sauvegarde les résumés d'actualités en DB.
    Appelé toutes les 30 minutes par le scheduler.
    
    Args:
        force: Si True, force la régénération même si récent
    """
    if not NEWS_AVAILABLE:
        print("⚠️ News module non disponible, skip résumés")
        return
    
    # Smart scheduling: skip si déjà généré aujourd'hui
    if not force:
        from database import get_latest_news_summaries
        recent = get_latest_news_summaries(max_age_minutes=1440)  # 24h max pour récupérer
        if recent.get('success') and recent.get('summaries'):
            generated_at = recent.get('generated_at', '')
            if generated_at:
                # Comparer la date (pas l'heure)
                generated_date = generated_at[:10]  # YYYY-MM-DD
                today = datetime.now().strftime('%Y-%m-%d')
                if generated_date == today:
                    print(f"📰 Résumés d'actualités déjà générés aujourd'hui ({generated_at}) - skip")
                    return
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"📰 GÉNÉRATION DES RÉSUMÉS D'ACTUALITÉS")
    print(f"🕐 Début: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    config = load_config()
    tickers = config.get('tickers', [])
    
    if not tickers:
        print("⚠️ Aucun ticker configuré")
        return
    
    try:
        # Générer les résumés via le news_fetcher
        result = generate_news_summary(tickers, category='all')
        
        if result.get('success') and result.get('summaries'):
            # Sauvegarder en DB
            count = save_all_news_summaries(result['summaries'])
            elapsed = time.time() - start_time
            end_datetime = datetime.now()
            
            print(f"\n{'='*60}")
            print(f"📰 RÉCAP NEWS FETCHER")
            print(f"{'='*60}")
            print(f"🕐 Début:    {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 Fin:      {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Durée:    {elapsed:.1f}s")
            print(f"📊 Résumés:  {count} catégories générées")
            print(f"{'='*60}\n")
        else:
            print(f"⚠️ Échec génération résumés: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Erreur update_news_summaries: {e}")
        import traceback
        traceback.print_exc()


def run_analysis(market_filter=None):
    """Lance l'analyse sur les actions configurées (filtrées par marché si spécifié)"""
    config = load_config()
    tickers = config.get('tickers', [])
    model = config.get('model', 'mistral-nemo')
    advanced = config.get('advanced_analysis', False)
    parallel = config.get('parallel_analysis', False)
    num_threads = config.get('num_threads', 12)

    if not tickers:
        print("⚠️ Aucune action configurée dans config.json")
        return

    start_total = time.time()
    start_datetime = datetime.now()
    
    # Filtrer par marché si spécifié
    if market_filter:
        tickers_by_market = categorize_tickers_by_market(tickers)
        tickers = tickers_by_market.get(market_filter, [])
        if not tickers:
            print(f"⚠️ Aucune action pour le marché {market_filter}")
            return
        market_name = MARKET_SCHEDULES.get(market_filter, {}).get('name', market_filter)
        print(f"\n{'🔥'*30}")
        print(f"🏛️ Analyse pour {market_name}")
        print(f"🔄 Démarrage de l'analyse pour {len(tickers)} action(s): {', '.join(tickers)}")
    else:
        print(f"\n{'🔥'*30}")
        print(f"🔄 Démarrage de l'analyse ENHANCED pour {len(tickers)} action(s)")
    
    print(f"🕐 Début: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Mode: {'Approfondi (+News/Calendar)' if advanced else 'Standard'}")
    print(f"⚡ Parallélisme: {'Activé' if parallel else 'Désactivé'}")
    print(f"{'🔥'*30}\n")

    analysis_count = 0
    successful_count = 0
    successful_results = []

    if parallel and len(tickers) > 1:
        # Limit to 2 workers to avoid rate limits (each analysis = 2 API calls)
        with ThreadPoolExecutor(max_workers=min(2, len(tickers))) as executor:
            futures = [executor.submit(analyze_stock, t, model, advanced, num_threads) for t in tickers]
            for future in futures:
                result = future.result()
                analysis_count += 1
                if result:
                    successful_count += 1
                    successful_results.append(result)
    else:
        for ticker in tickers:
            result = analyze_stock(ticker, model, advanced, num_threads)
            analysis_count += 1
            if result:
                successful_count += 1
                successful_results.append(result)
            time.sleep(3)  # Wait between analyses to respect rate limits

    total_time = time.time() - start_total
    end_datetime = datetime.now()

    print(f"\n{'='*60}")
    print(f"🤖 RÉCAP AI ANALYZER")
    print(f"{'='*60}")
    print(f"🕐 Début:      {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Fin:        {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Durée:      {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"📊 Analyses:   {successful_count}/{analysis_count} réussies")
    print(f"📈 Actions:    {', '.join(tickers)}")
    print(f"{'='*60}\n")

    # Generate daily market summary
    if successful_results:
        _generate_and_save_market_summary(successful_results)


def _generate_and_save_market_summary(analyses_results):
    """Generate and save daily market summary after all analyses complete."""
    try:
        print(f"\n{'='*60}")
        print(f"📋 GENERATION DU RESUME MARCHE QUOTIDIEN")
        print(f"{'='*60}")

        summary, elapsed = generate_market_summary(analyses_results)

        if summary and not summary.get('error'):
            from database import save_news_summary

            summary_data = {
                'summary': json.dumps(summary, ensure_ascii=False),
                'article_count': len(analyses_results),
                'sources': [a['ticker'] for a in analyses_results],
                'is_fallback': False
            }
            save_news_summary('market_daily_summary', summary_data)
            print(f"   ✅ Resume marche sauvegarde ({elapsed:.1f}s)")
        else:
            print(f"   ⚠️ Echec generation resume marche")
    except Exception as e:
        print(f"   ❌ Erreur resume marche: {e}")
        import traceback
        traceback.print_exc()


def run_single_analysis(ticker):
    """Run analysis on a single ticker (for on-demand requests)"""
    config = load_config()
    model = config.get('model', 'mistral-nemo')
    advanced = config.get('advanced_analysis', False)
    num_threads = config.get('num_threads', 12)
    
    print(f"\n{'🎯'*30}")
    print(f"🎯 ON-DEMAND ANALYSIS: {ticker}")
    print(f"{'🎯'*30}\n")
    
    start_time = time.time()
    result = analyze_stock(ticker, model, advanced, num_threads)
    elapsed = time.time() - start_time
    
    if result:
        print(f"\n✅ Analysis completed for {ticker} in {elapsed:.1f}s")
        return True
    else:
        print(f"\n❌ Analysis failed for {ticker}")
        return False


# ============================================
# SMART SCHEDULING FUNCTIONS
# ============================================

# Track last known tickers for new ticker detection
_last_known_tickers = set()
_config_file_mtime = 0


def get_config_mtime():
    """Get modification time of config file"""
    import os
    config_path = '/app/config.json'
    try:
        return os.path.getmtime(config_path)
    except:
        return 0


def check_for_new_tickers():
    """
    Check if new tickers were added to config.
    Returns list of new tickers that need immediate analysis.
    """
    global _last_known_tickers, _config_file_mtime

    current_mtime = get_config_mtime()
    if current_mtime == _config_file_mtime and _last_known_tickers:
        return []

    _config_file_mtime = current_mtime
    config = load_config()
    current_tickers = set(config.get('tickers', []))

    if not _last_known_tickers:
        # First run, initialize without triggering analysis
        _last_known_tickers = current_tickers
        return []

    new_tickers = current_tickers - _last_known_tickers
    _last_known_tickers = current_tickers

    if new_tickers:
        print(f"\n🆕 Nouveaux tickers détectés: {', '.join(new_tickers)}")

    return list(new_tickers)


def should_run_daily_analysis():
    """
    Check if daily analysis should run based on the last batch analysis DATE.
    Uses date comparison (not hours) to avoid issues with long-running analyses.
    
    Returns:
        (should_run: bool, reason: str)
    """
    today = datetime.now().strftime('%Y-%m-%d')
    last_batch_date = get_last_batch_analysis_date()
    
    if last_batch_date is None:
        return True, "Première analyse (jamais exécutée)"
    
    if last_batch_date < today:
        return True, f"Dernière analyse le {last_batch_date}, nouvelle journée"
    
    return False, f"Déjà analysé aujourd'hui ({last_batch_date})"


def get_tickers_needing_analysis():
    """
    Get list of tickers that have never been analyzed.
    Used for new tickers or first-time setup.
    
    Returns:
        List of tickers needing analysis
    """
    config = load_config()
    tickers = config.get('tickers', [])
    
    if not tickers:
        return []
    
    # Get last analysis times from DB
    last_analysis_times = get_last_analysis_times(tickers)
    
    tickers_needing_analysis = []
    
    for ticker in tickers:
        if ticker not in last_analysis_times or last_analysis_times.get(ticker) is None:
            tickers_needing_analysis.append(ticker)
    
    return tickers_needing_analysis


def run_smart_analysis(force=False, on_startup=False):
    """
    Run analysis with smart scheduling based on DATE (not hours).
    
    Args:
        force: If True, analyze all tickers regardless of last analysis date
        on_startup: If True, this is a startup check (more verbose)
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    if force:
        print(f"\n🔄 FORCE MODE: Analyse de tous les tickers configurés")
        set_last_batch_analysis_date(today)
        run_analysis()
        return
    
    should_run, reason = should_run_daily_analysis()
    
    print(f"\n📅 Vérification de l'analyse quotidienne:")
    print(f"   📆 Date du jour: {today}")
    print(f"   📋 Dernière analyse batch: {get_last_batch_analysis_date() or 'Jamais'}")
    print(f"   {'✅' if should_run else '⏸️'} {reason}")
    
    if should_run:
        # Check for tickers never analyzed
        never_analyzed = get_tickers_needing_analysis()
        if never_analyzed:
            print(f"   🆕 Tickers jamais analysés: {', '.join(never_analyzed)}")
        
        print(f"\n🚀 Lancement de l'analyse quotidienne...")
        set_last_batch_analysis_date(today)  # Mark as started BEFORE running
        run_analysis()
    else:
        if on_startup:
            # On startup, still check for tickers that were never analyzed
            never_analyzed = get_tickers_needing_analysis()
            if never_analyzed:
                print(f"\n🆕 {len(never_analyzed)} tickers jamais analysés: {', '.join(never_analyzed)}")
                print(f"🚀 Lancement de l'analyse pour les nouveaux tickers...")
                run_analysis_for_tickers(never_analyzed)
            else:
                print(f"\n✅ Rien à faire - analyse déjà effectuée aujourd'hui")
        else:
            print(f"\n✅ Analyse déjà effectuée aujourd'hui - skip")


def run_analysis_for_tickers(tickers):
    """Run analysis for a specific list of tickers"""
    if not tickers:
        return
    
    config = load_config()
    model = config.get('model', 'mistral-nemo')
    advanced = config.get('advanced_analysis', False)
    parallel = config.get('parallel_analysis', False)
    num_threads = config.get('num_threads', 12)

    start_total = time.time()
    start_datetime = datetime.now()
    
    print(f"\n{'🔥'*30}")
    print(f"🔄 Analyse pour {len(tickers)} action(s): {', '.join(tickers)}")
    print(f"🕐 Début: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Mode: {'Approfondi (+News/Calendar)' if advanced else 'Standard'}")
    print(f"⚡ Parallélisme: {'Activé' if parallel else 'Désactivé'}")
    print(f"{'🔥'*30}\n")

    analysis_count = 0
    successful_count = 0
    
    if parallel and len(tickers) > 1:
        with ThreadPoolExecutor(max_workers=min(4, len(tickers))) as executor:
            futures = [executor.submit(analyze_stock, t, model, advanced, num_threads) for t in tickers]
            for future in futures:
                result = future.result()
                analysis_count += 1
                if result:
                    successful_count += 1
    else:
        for ticker in tickers:
            result = analyze_stock(ticker, model, advanced, num_threads)
            analysis_count += 1
            if result:
                successful_count += 1
            time.sleep(1)

    total_time = time.time() - start_total
    end_datetime = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"🤖 RÉCAP AI ANALYZER")
    print(f"{'='*60}")
    print(f"🕐 Début:      {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Fin:        {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Durée:      {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"📊 Analyses:   {successful_count}/{analysis_count} réussies")
    print(f"📈 Actions:    {', '.join(tickers)}")
    print(f"{'='*60}\n")


def nightly_job():
    """Job pour l'analyse quotidienne nocturne à 3h du matin"""
    print(f"\n{'='*60}")
    print(f"🌙 ANALYSE NOCTURNE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 1. D'abord générer les résumés d'actualités
    if NEWS_AVAILABLE:
        print("\n📰 Génération des résumés d'actualités...")
        update_news_summaries()
    
    # 2. Ensuite lancer l'analyse avec smart scheduling
    print("\n📊 Lancement de l'analyse des tickers...")
    run_smart_analysis(force=False)
    
    # 3. Enfin, analyse du portefeuille
    print("\n💼 Lancement de l'analyse du portefeuille...")
    run_portfolio_analysis()


def run_portfolio_analysis(force: bool = False):
    """
    Analyse le portefeuille avec l'IA et génère des conseils du jour.
    Inclut toutes les actions surveillées, les news et le profil investisseur.

    Args:
        force: Si True, force la régénération même si récent
    """
    # Smart scheduling: skip si déjà généré aujourd'hui
    if not force:
        from database import get_latest_portfolio_analysis
        recent = get_latest_portfolio_analysis()
        if recent:
            analysis_date = datetime.fromisoformat(recent['date']) if isinstance(recent['date'], str) else recent['date']
            if analysis_date.date() == datetime.now().date():
                print(f"💼 Analyse portfolio déjà générée aujourd'hui ({recent['date']}) - skip")
                return None

    print(f"\n{'='*60}")
    print(f"💼 ANALYSE AI DU PORTEFEUILLE - CONSEILLER FINANCIER")
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    start_time = time.time()

    try:
        # 1. Configuration
        config = load_config()
        model = config.get('model', 'mistral-nemo')
        num_threads = config.get('num_threads', 12)

        # 2. Récupérer les positions ouvertes
        positions = get_positions(status='open')
        n_positions = len(positions) if positions else 0
        print(f"📊 {n_positions} positions ouvertes")

        # 3. Récupérer les analyses de TOUS les tickers surveillés
        all_tickers = config.get('tickers', [])
        all_analyses = get_latest_analyses(all_tickers)
        print(f"📈 Analyses disponibles pour {len(all_analyses)}/{len(all_tickers)} tickers")

        # 4. Récupérer les news
        from database import get_latest_news_summaries
        news_data = get_latest_news_summaries(max_age_minutes=1440)
        news_summaries = news_data.get('summaries', {}) if news_data.get('success') else {}
        print(f"📰 {len(news_summaries)} catégories de news disponibles")

        # 5. Générer l'analyse IA du portefeuille
        analysis_result, elapsed_time = generate_portfolio_analysis(
            positions=positions or [],
            all_analyses=all_analyses,
            news_summaries=news_summaries,
            config=config,
            model=model,
            num_threads=num_threads
        )

        if not analysis_result:
            print("❌ Échec de l'analyse portefeuille")
            return None

        # 6. Calculate baseline for projection tracking
        from database import get_positions_summary, get_portfolio_performance
        summary = get_positions_summary()
        perf = get_portfolio_performance()

        baseline_value = summary.get('current_value', 0) if summary else 0
        baseline_pnl_pct = perf.get('total_pnl_pct', 0) if perf else 0

        # 7. Sauvegarder en DB
        saved = save_portfolio_analysis(
            analysis_data=analysis_result,
            model=model,
            elapsed_time=elapsed_time,
            positions_count=n_positions,
            baseline_portfolio_value=baseline_value,
            baseline_pnl_pct=baseline_pnl_pct
        )

        # 7. Afficher le résumé
        total_time = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"💼 RÉCAP ANALYSE PORTEFEUILLE")
        print(f"{'='*60}")
        print(f"⏱️  Durée:      {total_time:.1f}s")
        print(f"📊 Positions:  {n_positions}")
        print(f"📈 Tickers:    {len(all_analyses)} analysés")

        if analysis_result and 'resume_global' in analysis_result:
            resume = analysis_result['resume_global']
            print(f"🏥 État:       {resume.get('etat_portfolio', 'N/A')}")
            print(f"📈 Tendance:   {resume.get('tendance', 'N/A')}")
            print(f"💯 Score:      {resume.get('score_sante', 'N/A')}/100")

            # Plan d'action
            plan = analysis_result.get('plan_action', [])
            if plan:
                print(f"\n📋 PLAN D'ACTION:")
                for i, step in enumerate(plan, 1):
                    print(f"   {i}. {step}")

            # Achats recommandés
            achats = analysis_result.get('achats_recommandes', [])
            if achats:
                print(f"\n🛒 ACHATS RECOMMANDÉS:")
                for a in achats:
                    print(f"   → {a.get('ticker')}: {a.get('conviction', '')} | Entrée: {a.get('prix_entree', '?')}$ | SL: {a.get('stop_loss', '?')}$ | Obj: {a.get('objectif', '?')}$")

            # Ventes recommandées
            ventes = analysis_result.get('ventes_recommandees', [])
            if ventes:
                print(f"\n🔴 VENTES RECOMMANDÉES:")
                for v in ventes:
                    print(f"   → {v.get('ticker')}: {v.get('urgence', '')} | {v.get('raison', '')}")

            # Projections
            proj = analysis_result.get('projections', {})
            if proj:
                print(f"\n📊 PROJECTIONS:")
                print(f"   1 semaine: {proj.get('expected_pnl_1w', '?')}%")
                print(f"   1 mois:    {proj.get('expected_pnl_1m', '?')}%")
                print(f"   1 an:      {proj.get('expected_pnl_1y', '?')}%")

            # Conseils par position
            conseils = analysis_result.get('conseils_positions', [])
            if conseils:
                print(f"\n📋 CONSEILS PAR POSITION:")
                for conseil in conseils:
                    ticker = conseil.get('ticker', 'N/A')
                    action = conseil.get('action', 'N/A')
                    urgence = conseil.get('urgence', '')
                    urgence_icon = '🔴' if urgence == 'Haute' else '🟡' if urgence == 'Moyenne' else '🟢'
                    print(f"   {urgence_icon} {ticker}: {action}")

        print(f"{'='*60}\n")

        return analysis_result

    except Exception as e:
        print(f"❌ Erreur analyse portefeuille: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_new_tickers_job():
    """Job pour vérifier les nouveaux tickers (toutes les 5 minutes)"""
    new_tickers = check_for_new_tickers()
    if new_tickers:
        print(f"🆕 Lancement de l'analyse pour les nouveaux tickers: {', '.join(new_tickers)}")
        run_analysis_for_tickers(new_tickers)


if __name__ == "__main__":
    import schedule
    import argparse
    import pytz
    
    # Timezone Suisse
    TZ_SWISS = pytz.timezone('Europe/Zurich')
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Financial AI Analyzer')
    parser.add_argument('--single', type=str, help='Run single analysis for specified ticker')
    parser.add_argument('--force', action='store_true', help='Force analysis of all tickers regardless of last analysis time')
    parser.add_argument('--check', action='store_true', help='Check which tickers need analysis (dry run)')
    parser.add_argument('--portfolio', action='store_true', help='Run portfolio analysis')
    parser.add_argument('--portfolio-force', action='store_true', help='Force portfolio analysis regardless of last analysis date')
    parser.add_argument('--news', action='store_true', help='Run news summary only')
    parser.add_argument('--force-news', action='store_true', help='Force news summary update (even if already generated today)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon with smart scheduler')
    args = parser.parse_args()
    
    # Handle single ticker analysis mode
    if args.single:
        success = run_single_analysis(args.single.upper())
        exit(0 if success else 1)
    
    # Handle check mode (dry run)
    if args.check:
        should_run, reason = should_run_daily_analysis()
        print(f"\n📅 Statut de l'analyse quotidienne:")
        print(f"   📆 Date du jour: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"   📋 Dernière analyse batch: {get_last_batch_analysis_date() or 'Jamais'}")
        print(f"   {'✅ À lancer' if should_run else '⏸️ Déjà fait'}: {reason}")
        
        never_analyzed = get_tickers_needing_analysis()
        if never_analyzed:
            print(f"\n🆕 Tickers jamais analysés: {', '.join(never_analyzed)}")
        exit(0)
    
    # Handle news summary only
    if args.news:
        if NEWS_AVAILABLE:
            print("\n📰 Génération résumés news...")
            update_news_summaries(force=False)
        else:
            print("⚠️ News module non disponible")
        exit(0)

    # Handle force news summary
    if args.force_news:
        if NEWS_AVAILABLE:
            print("\n📰 MODE FORCÉ: Génération résumés news...")
            update_news_summaries(force=True)
        else:
            print("⚠️ News module non disponible")
        exit(0)
    
    # Handle portfolio analysis modes
    if args.portfolio or args.portfolio_force:
        if args.portfolio_force:
            print("\n💼 MODE FORCÉ: Analyse du portefeuille")
            run_portfolio_analysis(force=True)
        else:
            print("\n💼 Analyse du portefeuille")
            run_portfolio_analysis(force=False)
        exit(0)
    
    # Handle force mode
    if args.force:
        print("\n🔄 MODE FORCÉ: Analyse de tous les tickers")
        today = datetime.now().strftime('%Y-%m-%d')
        set_last_batch_analysis_date(today)
        run_analysis()
        exit(0)

    # Si pas de mode daemon, exécuter analyse unique et quitter
    if not args.daemon:
        print("\n🚀 Exécution unique (pas de scheduler)")
        print("   Utiliser --daemon pour lancer le scheduler en continu\n")
        
        if NEWS_AVAILABLE:
            print("📰 Génération des résumés d'actualités...")
            update_news_summaries()
        
        run_smart_analysis(force=False, on_startup=True)
        
        print("\n💼 Analyse portefeuille...")
        run_portfolio_analysis()
        
        print("\n✅ Analyse terminée")
        exit(0)

    # ============================================
    # MODE DAEMON - SMART SCHEDULER EFFICACE
    # ============================================
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║         SMART SCHEDULER - CONFIGURATION EFFICACE               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  📰 NEWS SUMMARY - 1×/jour                                     ║
║     └─ 07:00 CH - Briefing matinal (news overnight)           ║
║                                                                ║
║  💼 PORTFOLIO ANALYSIS - 2×/jour                               ║
║     ├─ 07:30 CH - Vue matinale (avant Europe)                 ║
║     └─ 22:00 CH - Post-marché US (après clôture 16h ET)       ║
║                                                                ║
║  📊 TICKERS ANALYSIS - 1×/jour                                 ║
║     └─ 14:30 CH - Pré-ouverture US (08:30 ET)                 ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  💰 COÛT ESTIMÉ: ~$3.50/mois                                   ║
║  ⏱️  TIMEZONE: Europe/Zurich (CH)                              ║
║  📅 JOURS: Lundi-Vendredi (marchés ouverts)                   ║
╚════════════════════════════════════════════════════════════════╝
""")

    def log_task(task_name):
        """Log l'exécution d'une tâche"""
        now = datetime.now(TZ_SWISS)
        print(f"\n{'='*70}")
        print(f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S')} CH - {task_name}")
        print(f"{'='*70}\n")

    def run_news_job():
        """📰 NEWS - 07:00"""
        log_task("📰 NEWS SUMMARY - Briefing matinal")
        if NEWS_AVAILABLE:
            update_news_summaries(force=True)
            print("✅ News summary complété\n")
        else:
            print("⚠️ News module non disponible\n")

    def run_tickers_job():
        """📊 TICKERS - 14:30"""
        log_task("📊 TICKERS ANALYSIS - Pré-ouverture US")
        today = datetime.now().strftime('%Y-%m-%d')
        set_last_batch_analysis_date(today)
        run_analysis()
        print("✅ Tickers analysis complété\n")

    def run_portfolio_morning_job():
        """💼 PORTFOLIO - 07:30"""
        log_task("💼 PORTFOLIO ANALYSIS - Vue matinale")
        run_portfolio_analysis(force=True)
        print("✅ Portfolio analysis (matin) complété\n")

    def run_portfolio_evening_job():
        """💼 PORTFOLIO - 22:00"""
        log_task("💼 PORTFOLIO ANALYSIS - Post-marché US")
        run_portfolio_analysis(force=True)
        print("✅ Portfolio analysis (soir) complété\n")

    # Tâches programmées (Lundi-Vendredi uniquement)
    
    # 07:00 - News Summary
    schedule.every().monday.at("07:00").do(run_news_job)
    schedule.every().tuesday.at("07:00").do(run_news_job)
    schedule.every().wednesday.at("07:00").do(run_news_job)
    schedule.every().thursday.at("07:00").do(run_news_job)
    schedule.every().friday.at("07:00").do(run_news_job)
    
    # 07:30 - Portfolio Morning
    schedule.every().monday.at("07:30").do(run_portfolio_morning_job)
    schedule.every().tuesday.at("07:30").do(run_portfolio_morning_job)
    schedule.every().wednesday.at("07:30").do(run_portfolio_morning_job)
    schedule.every().thursday.at("07:30").do(run_portfolio_morning_job)
    schedule.every().friday.at("07:30").do(run_portfolio_morning_job)
    
    # 14:30 - Tickers Analysis (pré-ouverture US)
    schedule.every().monday.at("14:30").do(run_tickers_job)
    schedule.every().tuesday.at("14:30").do(run_tickers_job)
    schedule.every().wednesday.at("14:30").do(run_tickers_job)
    schedule.every().thursday.at("14:30").do(run_tickers_job)
    schedule.every().friday.at("14:30").do(run_tickers_job)
    
    # 22:00 - Portfolio Evening (post-marché US)
    schedule.every().monday.at("22:00").do(run_portfolio_evening_job)
    schedule.every().tuesday.at("22:00").do(run_portfolio_evening_job)
    schedule.every().wednesday.at("22:00").do(run_portfolio_evening_job)
    schedule.every().thursday.at("22:00").do(run_portfolio_evening_job)
    schedule.every().friday.at("22:00").do(run_portfolio_evening_job)

    now = datetime.now(TZ_SWISS)
    print(f"⏰ Démarré à: {now.strftime('%Y-%m-%d %H:%M:%S')} CH")
    print(f"📅 Jour: {now.strftime('%A')}\n")
    
    # Afficher les prochaines tâches
    jobs = schedule.get_jobs()
    if jobs:
        print("📋 Prochaines tâches programmées:\n")
        sorted_jobs = sorted(jobs, key=lambda j: j.next_run)
        for job in sorted_jobs[:10]:
            task_name = job.job_func.__name__.replace('run_', '').replace('_job', '').replace('_', ' ').title()
            next_run = job.next_run.strftime('%a %d/%m %H:%M')
            print(f"   ⏰ {next_run} - {task_name}")
    
    print("\n" + "="*70)
    print("🔄 Scheduler actif - En attente des prochains jobs...")
    print("⌨️  Ctrl+C pour arrêter")
    print("="*70 + "\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("⏹️  SCHEDULER ARRÊTÉ")
        print("="*70 + "\n")
