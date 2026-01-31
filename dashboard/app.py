from flask import Flask, render_template, jsonify, request, Response, stream_with_context
import os
import json
from datetime import datetime
import requests
import time
from threading import Thread, Event

# Portfolio service URL for live prices
PORTFOLIO_SERVICE_URL = os.environ.get('PORTFOLIO_SERVICE_URL', 'http://portfolio:5555')

# Import database module - chemin partagé via volume Docker
import sys
sys.path.insert(0, '/app')

from database import (
    get_analyses, get_latest_by_ticker, get_stats, get_ticker_history, init_db,
    get_favorites, add_favorite, remove_favorite,
    create_position, get_positions, get_position, update_position, close_position, partial_close_position, delete_position, get_positions_summary,
    get_news_articles, save_news_articles, get_latest_news_summaries,
    get_portfolio_history, get_portfolio_performance, get_latest_snapshot,
    get_latest_portfolio_analysis, get_portfolio_analyses_history
)

# Import news fetcher (pour les endpoints raw)
try:
    from news_fetcher import get_news_fetcher, NEWS_CATEGORIES
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    NEWS_CATEGORIES = ['general']

app = Flask(__name__)

# Initialiser la base de données
init_db()


# ============================================
# ERROR HANDLERS - Return JSON instead of HTML
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response"""
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'message': str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"❌ Internal Server Error: {error}")
    print(error_trace)
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error),
        'trace': error_trace
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions with JSON response"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"❌ Unhandled Exception: {error}")
    print(error_trace)

    # Return JSON for API routes, HTML for others
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': type(error).__name__,
            'message': str(error),
            'trace': error_trace
        }), 500
    else:
        # Re-raise for non-API routes to use default HTML error page
        raise


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/components-demo')
def components_demo():
    """Demo page for Lit components"""
    return render_template('components-demo.html')


@app.route('/new')
def index_new():
    """New dashboard page with Lit components"""
    return render_template('index-new.html')


@app.route('/api/analyses')
def api_analyses():
    """API : Liste des analyses"""
    ticker = request.args.get('ticker', None)
    days = int(request.args.get('days', 7))
    
    analyses = get_analyses(ticker=ticker, days=days)
    
    return jsonify({
        'success': True,
        'count': len(analyses),
        'analyses': analyses
    })


@app.route('/api/latest')
def api_latest():
    """API : Dernières analyses (une par ticker)"""
    latest = get_latest_by_ticker(hours=24)
    favorites = get_favorites()
    
    return jsonify({
        'success': True,
        'latest': latest,
        'favorites': favorites
    })


@app.route('/api/stats')
def api_stats():
    """API : Statistiques"""
    stats = get_stats()
    stats['favorites'] = get_favorites()
    return jsonify(stats)


@app.route('/health')
def health():
    """Health check endpoint pour Docker"""
    return jsonify({
        'status': 'healthy',
        'service': 'finance-dashboard',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/ticker/<ticker>')
def api_ticker_history(ticker):
    """API : Historique d'un ticker"""
    days = int(request.args.get('days', 30))
    result = get_ticker_history(ticker=ticker, days=days)
    
    return jsonify({
        'success': True,
        **result
    })


# ============================================
# API FAVORIS
# ============================================

@app.route('/api/favorites', methods=['GET'])
def api_get_favorites():
    """Liste des favoris"""
    return jsonify({
        'success': True,
        'favorites': get_favorites()
    })


@app.route('/api/favorites/<ticker>', methods=['POST'])
def api_add_favorite(ticker):
    """Ajouter aux favoris"""
    success = add_favorite(ticker.upper())
    return jsonify({'success': success})


@app.route('/api/favorites/<ticker>', methods=['DELETE'])
def api_remove_favorite(ticker):
    """Retirer des favoris"""
    success = remove_favorite(ticker.upper())
    return jsonify({'success': success})


# ============================================
# API POSITIONS
# ============================================

@app.route('/api/positions', methods=['GET'])
def api_get_positions():
    """Liste des positions"""
    status = request.args.get('status', None)
    ticker = request.args.get('ticker', None)
    positions = get_positions(status=status, ticker=ticker)
    summary = get_positions_summary()
    
    return jsonify({
        'success': True,
        'positions': positions,
        'summary': summary
    })


@app.route('/api/positions', methods=['POST'])
def api_create_position():
    """Créer une position"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        required = ['ticker', 'entry_price']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        position = create_position(data)
        if position:
            return jsonify({
                'success': True,
                'position': position.to_dict()
            })
        return jsonify({'success': False, 'error': 'Failed to create position'}), 500
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error creating position: {e}")
        print(error_trace)
        return jsonify({'success': False, 'error': str(e), 'trace': error_trace}), 500


@app.route('/api/positions/<int:position_id>', methods=['GET'])
def api_get_position(position_id):
    """Détail d'une position"""
    position = get_position(position_id)
    if position:
        return jsonify({'success': True, 'position': position})
    return jsonify({'success': False, 'error': 'Position not found'}), 404


@app.route('/api/positions/<int:position_id>', methods=['PUT'])
def api_update_position(position_id):
    """Modifier une position"""
    data = request.get_json()
    success = update_position(position_id, data)
    return jsonify({'success': success})


@app.route('/api/positions/<int:position_id>/close', methods=['POST'])
def api_close_position(position_id):
    """Clôturer une position"""
    data = request.get_json()
    exit_price = data.get('exit_price')
    status = data.get('status', 'closed')
    
    if not exit_price:
        return jsonify({'success': False, 'error': 'exit_price required'}), 400
    
    success = close_position(position_id, exit_price, status)
    return jsonify({'success': success})


@app.route('/api/positions/<int:position_id>/partial-close', methods=['POST'])
def api_partial_close_position(position_id):
    """Clôturer partiellement une position (vendre un %)"""
    data = request.get_json()
    exit_price = data.get('exit_price')
    sell_percent = data.get('sell_percent')
    status = data.get('status', 'closed')
    
    if not exit_price:
        return jsonify({'success': False, 'error': 'exit_price required'}), 400
    if not sell_percent or sell_percent <= 0 or sell_percent >= 100:
        return jsonify({'success': False, 'error': 'sell_percent must be between 1 and 99'}), 400
    
    result = partial_close_position(position_id, exit_price, sell_percent, status)
    if result:
        return jsonify({'success': True, **result})
    return jsonify({'success': False, 'error': 'Failed to partially close position'}), 400


@app.route('/api/positions/<int:position_id>', methods=['DELETE'])
def api_delete_position(position_id):
    """Supprimer une position"""
    success = delete_position(position_id)
    return jsonify({'success': success})


# ============================================
# API LIVE PRICES (proxied to portfolio service)
# ============================================

@app.route('/api/live/prices', methods=['POST'])
def api_get_live_prices():
    """
    Récupère les prix en temps réel pour une liste de tickers.
    Proxied to portfolio service.
    Body: { "tickers": ["AAPL", "NVDA", ...] }
    """
    try:
        data = request.get_json()
        
        # Forward request to portfolio service
        response = requests.post(
            f'{PORTFOLIO_SERVICE_URL}/api/live/prices',
            json=data,
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error connecting to portfolio service: {e}")
        return jsonify({
            'success': False,
            'error': f'Portfolio service unavailable: {str(e)}'
        }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/live/price/<ticker>')
def api_get_live_price(ticker):
    """
    Récupère le prix en temps réel pour un seul ticker.
    Proxied to portfolio service.
    """
    try:
        # Forward request to portfolio service
        response = requests.get(
            f'{PORTFOLIO_SERVICE_URL}/api/live/price/{ticker}',
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error connecting to portfolio service: {e}")
        return jsonify({
            'success': False,
            'error': f'Portfolio service unavailable: {str(e)}'
        }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# API PORTFOLIO PERFORMANCE
# ============================================

@app.route('/api/portfolio/history')
def api_portfolio_history():
    """
    Récupère l'historique des snapshots du portfolio.
    Query params:
        - days: nombre de jours (défaut: 30, 0 = tout)
    """
    days = int(request.args.get('days', 30))
    
    try:
        history = get_portfolio_history(days=days)
        
        return jsonify({
            'success': True,
            'days': days,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'history': []
        }), 500


@app.route('/api/portfolio/performance')
def api_portfolio_performance():
    """
    Récupère les métriques de performance du portfolio.
    """
    try:
        performance = get_portfolio_performance()
        latest = get_latest_snapshot()
        
        return jsonify({
            'success': True,
            'performance': performance,
            'latest_snapshot': latest
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/chart-data')
def api_portfolio_chart_data():
    """
    Endpoint optimisé pour les graphiques.
    Retourne les données formatées pour Chart.js.
    Query params:
        - days: 7, 30, 90, 365, 0 (tout)
    """
    days = int(request.args.get('days', 30))
    
    try:
        history = get_portfolio_history(days=days)
        
        if not history:
            return jsonify({
                'success': True,
                'labels': [],
                'datasets': {
                    'value': [],
                    'invested': [],
                    'pnl': [],
                    'pnl_percent': []
                }
            })
        
        # Formater pour Chart.js
        labels = [h['date'] for h in history]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': {
                'value': [h['total_value'] for h in history],
                'invested': [h['total_invested'] for h in history],
                'pnl': [h['total_pnl'] for h in history],
                'pnl_percent': [h['total_pnl_percent'] for h in history],
                'daily_change': [h['daily_change_percent'] for h in history],
                'global_pnl': [h.get('global_pnl', h['total_pnl']) for h in history],
                'global_pnl_percent': [h.get('global_pnl_percent', h['total_pnl_percent']) for h in history],
                'realized_pnl': [h.get('realized_pnl', 0) for h in history]
            },
            'summary': {
                'current_value': history[-1]['total_value'] if history else 0,
                'total_invested': history[-1]['total_invested'] if history else 0,
                'total_pnl': history[-1]['total_pnl'] if history else 0,
                'total_pnl_percent': history[-1]['total_pnl_percent'] if history else 0,
                'global_pnl': history[-1].get('global_pnl', history[-1]['total_pnl']) if history else 0,
                'global_pnl_percent': history[-1].get('global_pnl_percent', history[-1]['total_pnl_percent']) if history else 0,
                'realized_pnl': history[-1].get('realized_pnl', 0) if history else 0,
                'days_tracked': len(history)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# API PORTFOLIO AI ANALYSIS
# ============================================

@app.route('/api/portfolio/analysis')
def api_portfolio_analysis():
    """
    Récupère la dernière analyse IA du portfolio.
    """
    try:
        analysis = get_latest_portfolio_analysis()
        
        if not analysis:
            return jsonify({
                'success': True,
                'analysis': None,
                'message': 'Aucune analyse de portfolio disponible'
            })
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/analysis/history')
def api_portfolio_analysis_history():
    """
    Récupère l'historique des analyses IA du portfolio.
    Query params:
        - limit: nombre d'analyses (défaut: 10)
    """
    limit = int(request.args.get('limit', 10))
    
    try:
        history = get_portfolio_analyses_history(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/settings/commissions', methods=['GET'])
def api_get_commissions():
    """Get trading commission settings"""
    import json
    config_path = '/app/config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        trading = config.get('trading', {
            'buy_commission': 10.0,
            'sell_commission': 12.0,
            'commission_currency': 'CHF'
        })
        return jsonify({'success': True, 'trading': trading})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/commissions', methods=['PUT'])
def api_set_commissions():
    """Update trading commission settings"""
    import json
    config_path = '/app/config.json'
    data = request.get_json()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'trading' not in config:
            config['trading'] = {}
        
        if 'buy_commission' in data:
            config['trading']['buy_commission'] = float(data['buy_commission'])
        if 'sell_commission' in data:
            config['trading']['sell_commission'] = float(data['sell_commission'])
        if 'commission_currency' in data:
            config['trading']['commission_currency'] = data['commission_currency']
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({'success': True, 'trading': config['trading']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# API TICKERS CONFIGURATION (Analyzer Settings)
# ============================================

@app.route('/api/settings/tickers', methods=['GET'])
def api_get_tickers():
    """Get list of tracked tickers for analysis"""
    config_path = '/app/config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        tickers = config.get('tickers', [])
        return jsonify({
            'success': True, 
            'tickers': tickers,
            'model': config.get('model', 'mistral-nemo'),
            'advanced_analysis': config.get('advanced_analysis', False),
            'parallel_analysis': config.get('parallel_analysis', False)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/tickers', methods=['PUT'])
def api_set_tickers():
    """Update list of tracked tickers for analysis"""
    config_path = '/app/config.json'
    data = request.get_json()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'tickers' in data:
            # Ensure uppercase and unique
            tickers = list(set([t.upper().strip() for t in data['tickers'] if t.strip()]))
            config['tickers'] = sorted(tickers)
        
        if 'model' in data:
            config['model'] = data['model']
        
        if 'advanced_analysis' in data:
            config['advanced_analysis'] = bool(data['advanced_analysis'])
        
        if 'parallel_analysis' in data:
            config['parallel_analysis'] = bool(data['parallel_analysis'])
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True, 
            'tickers': config['tickers'],
            'model': config.get('model'),
            'advanced_analysis': config.get('advanced_analysis'),
            'parallel_analysis': config.get('parallel_analysis')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/tickers/<ticker>', methods=['POST'])
def api_add_ticker(ticker):
    """Add a ticker to tracked list"""
    config_path = '/app/config.json'
    ticker = ticker.upper().strip()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tickers = config.get('tickers', [])
        if ticker not in tickers:
            tickers.append(ticker)
            config['tickers'] = sorted(tickers)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return jsonify({'success': True, 'tickers': config['tickers']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/tickers/<ticker>', methods=['DELETE'])
def api_remove_ticker(ticker):
    """Remove a ticker from tracked list"""
    config_path = '/app/config.json'
    ticker = ticker.upper().strip()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tickers = config.get('tickers', [])
        if ticker in tickers:
            tickers.remove(ticker)
            config['tickers'] = sorted(tickers)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return jsonify({'success': True, 'tickers': config['tickers']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# API ON-DEMAND ANALYSIS
# ============================================

# Track running analyses
_running_analyses = {}
_force_analysis_status = {'running': False}

@app.route('/api/analyze/force', methods=['POST'])
def api_force_all_analysis():
    """Force analysis of all configured tickers"""
    
    # Check if force analysis is already running
    if _force_analysis_status.get('running'):
        return jsonify({
            'success': False,
            'error': 'Force analysis already running',
            'status': 'running',
            'started': _force_analysis_status.get('started')
        }), 409
    
    try:
        def run_force_analysis():
            try:
                _force_analysis_status['running'] = True
                _force_analysis_status['started'] = datetime.now().isoformat()
                _force_analysis_status['completed'] = None
                _force_analysis_status['success'] = None
                
                import subprocess
                result = subprocess.run(
                    ['python', '/app/analyzer.py', '--force'],
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout for all tickers
                )
                
                _force_analysis_status['running'] = False
                _force_analysis_status['completed'] = datetime.now().isoformat()
                _force_analysis_status['success'] = result.returncode == 0
                _force_analysis_status['output'] = result.stdout[-2000:] if result.stdout else ''
                _force_analysis_status['error'] = result.stderr[-1000:] if result.stderr else ''
                
            except Exception as e:
                _force_analysis_status['running'] = False
                _force_analysis_status['completed'] = datetime.now().isoformat()
                _force_analysis_status['success'] = False
                _force_analysis_status['error'] = str(e)
        
        thread = Thread(target=run_force_analysis)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Force analysis started for all tickers',
            'status': 'started'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/force/status', methods=['GET'])
def api_force_analysis_status():
    """Check status of force analysis"""
    return jsonify({
        'success': True,
        **_force_analysis_status
    })


@app.route('/api/analyze/check', methods=['GET'])
def api_check_analysis_needed():
    """Check which tickers need analysis based on last analysis time"""
    try:
        import subprocess
        result = subprocess.run(
            ['python', '/app/analyzer.py', '--check'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return jsonify({
            'success': True,
            'output': result.stdout,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/<ticker>', methods=['POST'])
def api_run_analysis(ticker):
    """Request an on-demand analysis for a ticker"""
    ticker = ticker.upper().strip()
    
    # Check if analysis is already running
    if ticker in _running_analyses and _running_analyses[ticker].get('running'):
        return jsonify({
            'success': False, 
            'error': f'Analysis already running for {ticker}',
            'status': 'running'
        }), 409
    
    try:
        # Start analysis in background thread
        def run_analysis_task():
            try:
                _running_analyses[ticker] = {'running': True, 'started': datetime.now().isoformat()}
                
                # Import analyzer module
                import subprocess
                result = subprocess.run(
                    ['python', '/app/analyzer.py', '--single', ticker],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 min timeout
                )
                
                _running_analyses[ticker] = {
                    'running': False, 
                    'completed': datetime.now().isoformat(),
                    'success': result.returncode == 0,
                    'output': result.stdout[-1000:] if result.stdout else '',
                    'error': result.stderr[-500:] if result.stderr else ''
                }
            except Exception as e:
                _running_analyses[ticker] = {
                    'running': False,
                    'completed': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }
        
        thread = Thread(target=run_analysis_task)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Analysis started for {ticker}',
            'status': 'started'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/<ticker>/status', methods=['GET'])
def api_analysis_status(ticker):
    """Check status of an on-demand analysis"""
    ticker = ticker.upper().strip()
    
    if ticker in _running_analyses:
        return jsonify({
            'success': True,
            'ticker': ticker,
            **_running_analyses[ticker]
        })
    
    return jsonify({
        'success': True,
        'ticker': ticker,
        'running': False,
        'status': 'idle'
    })


# ============================================
# API NEWS
# ============================================

@app.route('/api/news')
def api_get_news():
    """
    Récupère les actualités agrégées.
    Query params:
        - category: 'my_stocks', 'market', 'tech' (défaut: all)
        - refresh: 'true' pour forcer le refresh depuis l'API
    """
    category = request.args.get('category', None)
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if not NEWS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'News service not available',
            'news': {'my_stocks': [], 'market': [], 'tech': []}
        })
    
    try:
        fetcher = get_news_fetcher()
        
        if not fetcher.is_available():
            # Retourner les news depuis la DB si pas d'API
            return jsonify({
                'success': True,
                'source': 'database',
                'news': {
                    'my_stocks': get_news_articles(category='company', days=3, limit=15),
                    'market': get_news_articles(category='general', days=3, limit=10),
                    'tech': get_news_articles(category='sector_technology', days=3, limit=10)
                }
            })
        
        # Récupérer les tickers depuis la config
        config_path = '/app/config.json'
        tickers = []
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                tickers = config.get('tickers', [])
        except:
            pass
        
        # Collecter les news par catégorie
        news = {
            'my_stocks': [],
            'market': fetcher.get_market_news(),
            'tech': fetcher.get_tech_news()
        }
        
        # News des actions suivies
        for ticker in tickers:
            for article in fetcher.get_company_news(ticker)[:5]:
                news['my_stocks'].append(article)
        news['my_stocks'] = sorted(news['my_stocks'], key=lambda x: x.get('datetime', ''), reverse=True)[:15]
        
        # Sauvegarder en DB pour cache persistant
        for category_name, articles in news.items():
            for article in articles:
                article['category'] = category_name
            save_news_articles(articles)
        
        # Filtrer par catégorie si demandé
        if category and category in news:
            return jsonify({
                'success': True,
                'source': 'api',
                'category': category,
                'articles': news[category]
            })
        
        return jsonify({
            'success': True,
            'source': 'api',
            'news': news
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Error fetching news: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'news': {'my_stocks': [], 'market': [], 'tech': []}
        }), 500


@app.route('/api/news/ticker/<ticker>')
def api_get_ticker_news(ticker):
    """Récupère les actualités pour un ticker spécifique"""
    days = int(request.args.get('days', 7))
    
    if not NEWS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'News service not available',
            'articles': []
        })
    
    try:
        fetcher = get_news_fetcher()
        
        if fetcher.is_available():
            articles = fetcher.get_company_news(ticker.upper(), days=days)
            
            # Sauvegarder en DB
            for a in articles:
                a['category'] = 'company'
            save_news_articles(articles)
            
            return jsonify({
                'success': True,
                'ticker': ticker.upper(),
                'source': 'api',
                'count': len(articles),
                'articles': articles
            })
        else:
            # Fallback DB
            articles = get_news_articles(ticker=ticker.upper(), days=days)
            return jsonify({
                'success': True,
                'ticker': ticker.upper(),
                'source': 'database',
                'count': len(articles),
                'articles': articles
            })
            
    except Exception as e:
        print(f"❌ Error fetching ticker news: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'articles': []
        }), 500


@app.route('/api/news/category/<category>')
def api_get_category_news(category):
    """Récupère les actualités par catégorie Finnhub"""
    if category not in NEWS_CATEGORIES:
        return jsonify({
            'success': False,
            'error': f'Invalid category. Valid: {NEWS_CATEGORIES}'
        }), 400
    
    if not NEWS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'News service not available',
            'articles': []
        })
    
    try:
        fetcher = get_news_fetcher()
        
        if fetcher.is_available():
            articles = fetcher.get_market_news(limit=20)
            
            return jsonify({
                'success': True,
                'category': category,
                'count': len(articles),
                'articles': articles
            })
        else:
            return jsonify({
                'success': True,
                'category': category,
                'articles': get_news_articles(category=category, days=3)
            })
            
    except Exception as e:
        print(f"❌ Error fetching category news: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'articles': []
        }), 500


@app.route('/api/news/status')
def api_news_status():
    """Vérifie le statut du service de news"""
    status = {
        'available': NEWS_AVAILABLE,
        'api_configured': False,
        'categories': NEWS_CATEGORIES
    }
    
    if NEWS_AVAILABLE:
        fetcher = get_news_fetcher()
        status['api_configured'] = fetcher.is_available()
    
    return jsonify(status)


@app.route('/api/news/summary')
def api_news_summary():
    """
    Récupère les résumés d'actualités pré-générés depuis la DB.
    Les résumés sont générés par l'analyzer tous les matins à 7h00.
    
    Query params:
        - max_age: âge maximum en minutes (défaut: 1440 = 24h)
    """
    max_age = request.args.get('max_age', 1440, type=int)  # 24h par défaut
    
    try:
        # Récupérer les résumés depuis la DB
        result = get_latest_news_summaries(max_age_minutes=max_age)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'No summaries available. They are generated every 30 minutes by the analyzer.'),
                'summaries': {}
            })
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"❌ Error fetching news summaries: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'summaries': {}
        }), 500


# ============================================
# API MARKET DAILY SUMMARY
# ============================================

@app.route('/api/market/summary')
def api_market_summary():
    """
    Retrieve the latest daily market summary.
    Generated after all ticker analyses complete.
    """
    try:
        result = get_latest_news_summaries(max_age_minutes=1440)

        if result.get('success') and result.get('summaries'):
            market_summary = result['summaries'].get('market_daily_summary')
            if market_summary:
                try:
                    parsed = json.loads(market_summary.get('summary', '{}'))
                    return jsonify({
                        'success': True,
                        'summary': parsed,
                        'generated_at': market_summary.get('generated_at'),
                        'tickers_analyzed': market_summary.get('article_count', 0)
                    })
                except json.JSONDecodeError:
                    return jsonify({
                        'success': True,
                        'summary': {'raw': market_summary.get('summary', '')},
                        'generated_at': market_summary.get('generated_at')
                    })

        return jsonify({
            'success': False,
            'error': 'No market summary available yet',
            'summary': None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# SSE ENDPOINTS (Server-Sent Events)
# ============================================

@app.route('/api/stream/prices')
def stream_prices():
    """SSE stream for live price updates - default 5s interval"""
    # Get update interval from env or default to 5 seconds
    update_interval = int(os.environ.get('SSE_PRICE_INTERVAL', '5'))
    
    def generate():
        while True:
            try:
                # Get all open positions to determine which tickers to track
                positions = get_positions(status='open')
                if positions:
                    tickers = list(set([p['ticker'] for p in positions]))
                    positions_for_calc = [{
                        'ticker': p['ticker'],
                        'entry_price': p['entry_price'],
                        'quantity': p.get('quantity', 1),
                        'buy_commission': p.get('buy_commission', 0),
                        'sell_commission': p.get('sell_commission', 0)
                    } for p in positions]
                    
                    # Fetch live prices from portfolio service
                    try:
                        response = requests.post(
                            f'{PORTFOLIO_SERVICE_URL}/api/live/prices',
                            json={'tickers': tickers, 'positions': positions_for_calc},
                            timeout=5
                        )
                        if response.ok:
                            result = response.json()
                            if result.get('success') and result.get('prices'):
                                # Send update as SSE event
                                yield f"data: {json.dumps(result)}\n\n"
                    except Exception as e:
                        print(f"❌ Error fetching live prices for SSE: {e}")
                
                # Wait before next update
                time.sleep(update_interval)
            except GeneratorExit:
                break
            except Exception as e:
                print(f"❌ SSE stream error: {e}")
                time.sleep(update_interval)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/stream/news')
def stream_news():
    """SSE stream for news summary updates - default 2min interval"""
    update_interval = int(os.environ.get('SSE_NEWS_INTERVAL', '120'))
    
    def generate():
        last_summaries = {}
        while True:
            try:
                # Fetch latest news summaries
                result = get_latest_news_summaries(max_age_minutes=60)
                
                if result.get('success') and result.get('summaries'):
                    current_summaries = result['summaries']
                    
                    # Only send if summaries have changed
                    if current_summaries != last_summaries:
                        yield f"data: {json.dumps(result)}\n\n"
                        last_summaries = current_summaries
                
                # Wait before checking again
                time.sleep(update_interval)
            except GeneratorExit:
                break
            except Exception as e:
                print(f"❌ SSE news stream error: {e}")
                time.sleep(update_interval)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/stream/analyses')
def stream_analyses():
    """SSE stream for new AI analyses - default 1min interval"""
    update_interval = int(os.environ.get('SSE_ANALYSES_INTERVAL', '60'))
    
    def generate():
        last_count = 0
        while True:
            try:
                # Check for new analyses
                latest = get_latest_by_ticker(hours=24)
                current_count = len(latest)
                
                # Send update if new analyses detected
                if current_count != last_count:
                    favorites = get_favorites()
                    yield f"data: {json.dumps({'success': True, 'latest': latest, 'favorites': favorites})}\n\n"
                    last_count = current_count
                
                # Wait before checking again
                time.sleep(update_interval)
            except GeneratorExit:
                break
            except Exception as e:
                print(f"❌ SSE analyses stream error: {e}")
                time.sleep(update_interval)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
