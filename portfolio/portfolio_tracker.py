"""
Portfolio Tracker Service
Dedicated service for portfolio performance tracking and snapshots.
Runs independently from the analyzer.

Currency handling:
- Each position is stored and displayed in its native currency
- For aggregated portfolio totals, all values are converted to USD
- Exchange rates are fetched from Yahoo Finance

Also provides a REST API for live price fetching.
"""

import os
import sys
import time
import logging
import schedule
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import yfinance as yf
import pytz

# Import database module
sys.path.insert(0, '/app')
from database import (
    init_db, get_positions, save_portfolio_snapshot, 
    get_latest_snapshot, get_portfolio_history, get_portfolio_performance
)

# Flask app for API
app = Flask(__name__)

# Disable Flask/Werkzeug request logging (too verbose)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Timezone
ZURICH_TZ = pytz.timezone('Europe/Zurich')
NY_TZ = pytz.timezone('America/New_York')

# Currency to USD exchange rates (updated at runtime)
EXCHANGE_RATES = {
    'USD': 1.0,
    'CHF': 1.13,  # CHF to USD (1 CHF = ~1.13 USD)
    'EUR': 1.08,  # EUR to USD
    'GBP': 1.27   # GBP to USD
}

# Market schedules (in Zurich time)
MARKET_SCHEDULES = {
    'US': {
        'name': 'NYSE/NASDAQ',
        'open_time': '09:30',  # ET
        'close_time': '16:00',  # ET
        'timezone': 'America/New_York',
        'suffixes': ['', '.US'],
        'currency': 'USD'
    },
    'CH': {
        'name': 'SIX Swiss Exchange',
        'open_time': '09:00',  # CET
        'close_time': '17:30',  # CET
        'timezone': 'Europe/Zurich', 
        'suffixes': ['.SW', '.VX'],
        'currency': 'CHF'
    },
    'EU': {
        'name': 'Euronext',
        'open_time': '09:00',  # CET
        'close_time': '17:30',  # CET
        'timezone': 'Europe/Paris',
        'suffixes': ['.PA', '.DE', '.AS'],
        'currency': 'EUR'
    }
}


def get_ticker_market(ticker: str) -> str:
    """Determine market from ticker suffix"""
    ticker_upper = ticker.upper()
    
    for market, config in MARKET_SCHEDULES.items():
        for suffix in config['suffixes']:
            if suffix and ticker_upper.endswith(suffix.upper()):
                return market
    
    return 'US'  # Default to US


def get_ticker_currency(ticker: str) -> str:
    """Get the native currency for a ticker"""
    market = get_ticker_market(ticker)
    return MARKET_SCHEDULES.get(market, {}).get('currency', 'USD')


def is_market_open(market: str) -> dict:
    """
    Check if a specific market is currently open.
    Returns dict with is_open, is_extended, next_open, next_close info.
    """
    config = MARKET_SCHEDULES.get(market, MARKET_SCHEDULES['US'])
    tz = pytz.timezone(config['timezone'])
    now = datetime.now(tz)
    current_time = now.time()
    
    # Parse market hours
    open_time = datetime.strptime(config['open_time'], '%H:%M').time()
    close_time = datetime.strptime(config['close_time'], '%H:%M').time()
    
    # Check if it's a weekday
    is_weekday = now.weekday() < 5
    
    # Check if market is open
    is_open = is_weekday and open_time <= current_time <= close_time
    
    # Extended hours (1h before open, 1h after close) - only for US market
    is_extended = False
    if market == 'US' and is_weekday:
        pre_market = (datetime.combine(now.date(), open_time) - timedelta(hours=1)).time()
        post_market = (datetime.combine(now.date(), close_time) + timedelta(hours=1)).time()
        is_extended = (pre_market <= current_time < open_time) or (close_time < current_time <= post_market)
    
    return {
        'market': market,
        'name': config['name'],
        'is_open': is_open,
        'is_extended': is_extended,
        'is_weekday': is_weekday,
        'current_time': current_time.strftime('%H:%M'),
        'open_time': config['open_time'],
        'close_time': config['close_time'],
        'timezone': config['timezone']
    }


def get_ticker_market_status(ticker: str) -> dict:
    """Get market status for a specific ticker"""
    market = get_ticker_market(ticker)
    status = is_market_open(market)
    status['ticker'] = ticker
    return status


def update_exchange_rates():
    """Fetch current exchange rates from Yahoo Finance"""
    global EXCHANGE_RATES
    
    pairs = {
        'CHFUSD=X': 'CHF',
        'EURUSD=X': 'EUR', 
        'GBPUSD=X': 'GBP'
    }
    
    print("💱 Updating exchange rates...")
    
    for symbol, currency in pairs.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                rate = float(hist['Close'].iloc[-1])
                EXCHANGE_RATES[currency] = rate
                print(f"   {currency}/USD: {rate:.4f}")
        except Exception as e:
            print(f"   ⚠️ Could not fetch {currency} rate: {e}")
    
    print(f"   USD/USD: 1.0000 (reference)")


def convert_to_usd(value: float, currency: str) -> float:
    """Convert a value to USD using current exchange rates"""
    if currency == 'USD':
        return value
    rate = EXCHANGE_RATES.get(currency, 1.0)
    return value * rate


def is_market_day() -> bool:
    """Check if today is a trading day (Mon-Fri)"""
    return datetime.now(ZURICH_TZ).weekday() < 5


def get_current_price(ticker: str) -> float:
    """Fetch current price for a ticker via yfinance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        
        # Fallback: try 5d if 1d is empty
        hist = stock.history(period="5d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
            
        return None
    except Exception as e:
        print(f"   ⚠️ Error fetching {ticker}: {e}")
        return None


def calculate_position_pnl(position: dict, current_price: float) -> dict:
    """
    Calculate P&L for a single position.
    Returns values in both native currency and USD.
    """
    ticker = position.get('ticker', '')
    currency = get_ticker_currency(ticker)
    
    entry_price = position.get('entry_price', 0)
    quantity = position.get('quantity', 1)
    buy_commission = position.get('buy_commission', 0)
    sell_commission = position.get('sell_commission', 0)
    # Note: Commissions are stored in CHF by default (Swiss broker)
    commission_currency = 'CHF'
    total_commission = buy_commission + sell_commission
    
    # Calculate in native currency
    invested = entry_price * quantity
    current_value = current_price * quantity
    pnl_gross = current_value - invested
    
    # Convert commission to native currency for P&L calculation
    commission_in_native = total_commission
    if commission_currency != currency:
        # Convert CHF commission to native currency
        commission_usd = convert_to_usd(total_commission, commission_currency)
        if currency != 'USD':
            commission_in_native = commission_usd / EXCHANGE_RATES.get(currency, 1.0)
        else:
            commission_in_native = commission_usd
    
    pnl_net = pnl_gross - commission_in_native
    pnl_percent = (pnl_net / invested * 100) if invested > 0 else 0
    
    # Convert to USD for aggregation
    invested_usd = convert_to_usd(invested, currency)
    current_value_usd = convert_to_usd(current_value, currency)
    pnl_gross_usd = convert_to_usd(pnl_gross, currency)
    commission_usd = convert_to_usd(total_commission, commission_currency)
    pnl_net_usd = pnl_gross_usd - commission_usd
    
    return {
        # Native currency values
        'currency': currency,
        'invested': invested,
        'current_value': current_value,
        'pnl_gross': pnl_gross,
        'pnl_net': pnl_net,
        'pnl_percent': pnl_percent,
        'commission': total_commission,
        'commission_native': commission_in_native,  # Commission converted to stock's market currency
        # USD converted values (for aggregation)
        'invested_usd': invested_usd,
        'current_value_usd': current_value_usd,
        'pnl_gross_usd': pnl_gross_usd,
        'pnl_net_usd': pnl_net_usd,
        'commission_usd': commission_usd
    }


def generate_portfolio_snapshot():
    """
    Generate a single daily portfolio snapshot with all open positions.
    Includes all markets, but only processes markets with actual positions.
    """
    now = datetime.now(ZURICH_TZ)
    
    print(f"\n{'='*60}")
    print(f"📊 PORTFOLIO SNAPSHOT - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Market: All (consolidated at NASDAQ close)")
    print(f"{'='*60}")
    
    if not is_market_day():
        print("📅 Weekend - skipping snapshot")
        return
    
    try:
        # Get open positions
        positions = get_positions(status='open')
        
        if not positions:
            print("ℹ️ No open positions - skipping snapshot")
            return
        
        # Update exchange rates before calculating
        update_exchange_rates()
        
        print(f"📈 Processing {len(positions)} position(s)...")
        
        # Track totals in USD (reference currency for aggregation)
        total_invested_usd = 0
        total_value_usd = 0
        total_commission_usd = 0
        
        # Track currencies found
        currencies_found = set()
        
        for pos in positions:
            ticker = pos['ticker']
            quantity = pos.get('quantity', 1)
            entry_price = pos.get('entry_price', 0)
            currency = get_ticker_currency(ticker)
            currencies_found.add(currency)
            
            # Fetch current price
            current_price = get_current_price(ticker)
            
            if current_price is None:
                # Fallback to entry price
                print(f"   ⚠️ {ticker}: No price data, using entry price")
                current_price = entry_price
            
            # Calculate P&L (returns both native and USD values)
            pnl_data = calculate_position_pnl(pos, current_price)
            
            # Aggregate in USD
            total_invested_usd += pnl_data['invested_usd']
            total_value_usd += pnl_data['current_value_usd']
            total_commission_usd += pnl_data['commission_usd']
            
            # Log position in native currency
            pnl_sign = '+' if pnl_data['pnl_net'] >= 0 else ''
            symbol = 'CHF ' if currency == 'CHF' else ('€' if currency == 'EUR' else '$')
            print(f"   ✅ {ticker}: {symbol}{current_price:.2f} × {quantity} = {symbol}{pnl_data['current_value']:.2f} "
                  f"(P&L: {pnl_sign}{symbol}{pnl_data['pnl_net']:.2f}) [→ ${pnl_data['current_value_usd']:.2f}]")
        
        # Calculate totals in USD
        total_pnl_usd = total_value_usd - total_invested_usd - total_commission_usd
        total_pnl_percent = (total_pnl_usd / total_invested_usd * 100) if total_invested_usd > 0 else 0
        
        # Get previous snapshot for daily change
        previous = get_latest_snapshot()
        daily_change = 0
        daily_change_percent = 0
        
        if previous:
            prev_value = previous.get('total_value', 0)
            if prev_value > 0:
                daily_change = total_value_usd - prev_value
                daily_change_percent = (daily_change / prev_value) * 100
        
        # Count positions closed today and calculate realized P&L from ALL closed positions
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        closed_positions = get_positions(status='closed')
        stopped_positions = get_positions(status='stopped')
        all_closed = closed_positions + stopped_positions
        
        closed_today = sum(
            1 for p in all_closed 
            if p.get('exit_date') and datetime.fromisoformat(p['exit_date']).replace(tzinfo=ZURICH_TZ) >= today_start
        )
        
        # Calculate realized P&L from all closed positions (in USD)
        realized_pnl_usd = 0
        total_closed_invested_usd = 0
        for p in all_closed:
            ticker = p.get('ticker', '')
            currency = get_ticker_currency(ticker)
            entry_price = p.get('entry_price', 0)
            exit_price = p.get('exit_price', entry_price)
            quantity = p.get('quantity', 1)
            buy_commission = p.get('buy_commission', 0)
            sell_commission = p.get('sell_commission', 0)
            total_commission = buy_commission + sell_commission
            
            # P&L in native currency
            pnl_native = (exit_price - entry_price) * quantity
            invested_native = entry_price * quantity
            
            # Convert to USD
            pnl_usd = convert_to_usd(pnl_native, currency)
            invested_usd = convert_to_usd(invested_native, currency)
            commission_usd = convert_to_usd(total_commission, 'CHF')  # Commissions are in CHF
            
            realized_pnl_usd += pnl_usd - commission_usd
            total_closed_invested_usd += invested_usd
        
        # Global P&L = Unrealized (open) + Realized (closed)
        global_pnl_usd = total_pnl_usd + realized_pnl_usd
        global_invested_usd = total_invested_usd + total_closed_invested_usd
        global_pnl_percent = (global_pnl_usd / global_invested_usd * 100) if global_invested_usd > 0 else 0
        
        # Save snapshot (values are in USD) - include hour:minute for intraday tracking
        snapshot_data = {
            'date': now.strftime('%Y-%m-%d %H:%M'),
            'total_value': total_value_usd,
            'total_invested': total_invested_usd,
            'total_pnl': total_pnl_usd,
            'total_pnl_percent': total_pnl_percent,
            'realized_pnl': realized_pnl_usd,
            'global_pnl': global_pnl_usd,
            'global_pnl_percent': global_pnl_percent,
            'open_positions_count': len(positions),
            'closed_positions_count': closed_today,
            'total_closed_count': len(all_closed),
            'daily_change': daily_change,
            'daily_change_percent': daily_change_percent
        }
        
        saved = save_portfolio_snapshot(snapshot_data)
        
        currencies_str = ', '.join(sorted(currencies_found))
        
        if saved:
            print(f"\n✅ Snapshot saved (converted to USD):")
            print(f"   💱 Currencies: {currencies_str}")
            print(f"   💰 Total Value: ${total_value_usd:.2f}")
            print(f"   💵 Invested: ${total_invested_usd:.2f}")
            print(f"   📈 P&L (Open): {'+' if total_pnl_usd >= 0 else ''}${total_pnl_usd:.2f} ({'+' if total_pnl_percent >= 0 else ''}{total_pnl_percent:.2f}%)")
            print(f"   💸 P&L (Réalisé): {'+' if realized_pnl_usd >= 0 else ''}${realized_pnl_usd:.2f} ({len(all_closed)} positions clôturées)")
            print(f"   🎯 P&L GLOBAL: {'+' if global_pnl_usd >= 0 else ''}${global_pnl_usd:.2f} ({'+' if global_pnl_percent >= 0 else ''}{global_pnl_percent:.2f}%)")
            print(f"   📊 Daily Change: {'+' if daily_change >= 0 else ''}${daily_change:.2f} ({'+' if daily_change_percent >= 0 else ''}{daily_change_percent:.2f}%)")
        else:
            print("❌ Failed to save snapshot")
            
    except Exception as e:
        print(f"❌ Error generating snapshot: {e}")
        import traceback
        traceback.print_exc()


# ============================================
# FLASK API ENDPOINTS
# ============================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'portfolio-tracker',
        'timestamp': datetime.now().isoformat()
    }), 200


def get_intraday_change(ticker: str) -> dict:
    """
    Get accurate intraday change from Yahoo Finance.
    Uses regular_market_previous_close for accurate day change.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        
        # Get current price and CORRECT previous close
        # Note: 'previous_close' in fast_info can be stale/wrong
        # Use 'regular_market_previous_close' which is the actual previous trading day close
        current_price = getattr(info, 'last_price', None)
        previous_close = getattr(info, 'regular_market_previous_close', None)
        
        # Fallback to stock.info if fast_info doesn't have it
        if not previous_close:
            try:
                full_info = stock.info
                previous_close = full_info.get('previousClose') or full_info.get('regularMarketPreviousClose')
            except:
                pass
        
        if current_price and previous_close:
            day_change = current_price - previous_close
            day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else 0
            return {
                'price': current_price,
                'previous_close': previous_close,
                'day_change': day_change,
                'day_change_percent': day_change_percent
            }
        
        # Fallback to history if fast_info not available
        return None
    except Exception as e:
        print(f"⚠️ Error getting intraday change for {ticker}: {e}")
        return None


@app.route('/api/live/prices', methods=['POST'])
def api_get_live_prices():
    """
    Fetch live prices for multiple tickers with pre-calculated P&L.
    Body: { "tickers": ["AAPL", "NVDA", ...], "positions": [...] }
    
    If positions are provided, returns enriched data with P&L calculations.
    Also includes market status for each ticker.
    """
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        positions = data.get('positions', [])  # Optional: positions for P&L calculation
        
        if not tickers:
            return jsonify({'success': True, 'prices': {}})
        
        # Build position lookup by ticker
        position_by_ticker = {}
        for pos in positions:
            t = pos.get('ticker')
            if t:
                position_by_ticker[t] = pos
        
        # Get market status for all markets
        market_status = {
            market: is_market_open(market) 
            for market in MARKET_SCHEDULES.keys()
        }
        
        prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                
                # Get market status for this ticker
                ticker_market = get_ticker_market(ticker)
                ticker_market_status = market_status[ticker_market]
                
                # Get accurate intraday change from fast_info
                intraday = get_intraday_change(ticker)
                
                # Get intraday chart data
                hist = stock.history(period="1d", interval="5m")
                
                if not hist.empty or intraday:
                    if intraday:
                        current_price = intraday['price']
                        previous_close = intraday['previous_close']
                        day_change = intraday['day_change']
                        day_change_percent = intraday['day_change_percent']
                    else:
                        current_price = float(hist['Close'].iloc[-1])
                        # Use previous close for accurate day change
                        try:
                            info = stock.fast_info
                            previous_close = getattr(info, 'previous_close', None)
                            if previous_close:
                                day_change = current_price - previous_close
                                day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else 0
                            else:
                                open_price = float(hist['Open'].iloc[0])
                                day_change = current_price - open_price
                                day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
                        except:
                            open_price = float(hist['Open'].iloc[0])
                            day_change = current_price - open_price
                            day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
                    
                    # Get day high/low from history
                    if not hist.empty:
                        day_high = float(hist['High'].max())
                        day_low = float(hist['Low'].min())
                        chart_data = hist['Close'].tolist()[-78:]  # Last ~6.5 hours at 5min intervals
                    else:
                        day_high = current_price
                        day_low = current_price
                        chart_data = []
                    
                    # Base price data
                    price_data = {
                        'price': current_price,
                        'previous_close': previous_close if intraday else None,
                        'high': day_high,
                        'low': day_low,
                        'change': day_change,
                        'change_percent': day_change_percent,
                        'chart': chart_data,
                        'currency': get_ticker_currency(ticker),
                        'updated': datetime.now().isoformat(),
                        'market': {
                            'code': ticker_market,
                            'name': ticker_market_status['name'],
                            'is_open': ticker_market_status['is_open'],
                            'is_extended': ticker_market_status['is_extended']
                        }
                    }
                    
                    # Calculate P&L if position data provided
                    if ticker in position_by_ticker:
                        pos = position_by_ticker[ticker]
                        pnl_data = calculate_position_pnl(pos, current_price)
                        price_data['pnl'] = {
                            'invested': pnl_data['invested'],
                            'current_value': pnl_data['current_value'],
                            'pnl_gross': pnl_data['pnl_gross'],
                            'pnl_net': pnl_data['pnl_net'],
                            'pnl_percent': pnl_data['pnl_percent'],
                            'commission': pnl_data['commission'],
                            'commission_native': pnl_data['commission_native'],  # Fees in stock's market currency
                            'commission_usd': pnl_data['commission_usd'],
                            'currency': pnl_data['currency'],
                            # USD values for portfolio totals
                            'invested_usd': pnl_data['invested_usd'],
                            'current_value_usd': pnl_data['current_value_usd'],
                            'pnl_net_usd': pnl_data['pnl_net_usd']
                        }
                    
                    prices[ticker] = price_data
                else:
                    # Fallback to 5d if 1d is empty (weekend/after hours)
                    hist_5d = stock.history(period="5d", interval="1h")
                    if not hist_5d.empty:
                        current_price = float(hist_5d['Close'].iloc[-1])
                        price_data = {
                            'price': current_price,
                            'high': float(hist_5d['High'].iloc[-1]),
                            'low': float(hist_5d['Low'].iloc[-1]),
                            'change': 0,
                            'change_percent': 0,
                            'chart': hist_5d['Close'].tolist()[-24:],
                            'currency': get_ticker_currency(ticker),
                            'updated': datetime.now().isoformat(),
                            'market': {
                                'code': ticker_market,
                                'name': ticker_market_status['name'],
                                'is_open': ticker_market_status['is_open'],
                                'is_extended': ticker_market_status['is_extended']
                            }
                        }
                        
                        # Calculate P&L even for closed market
                        if ticker in position_by_ticker:
                            pos = position_by_ticker[ticker]
                            pnl_data = calculate_position_pnl(pos, current_price)
                            price_data['pnl'] = {
                                'invested': pnl_data['invested'],
                                'current_value': pnl_data['current_value'],
                                'pnl_gross': pnl_data['pnl_gross'],
                                'pnl_net': pnl_data['pnl_net'],
                                'pnl_percent': pnl_data['pnl_percent'],
                                'commission': pnl_data['commission'],
                                'currency': pnl_data['currency'],
                                'invested_usd': pnl_data['invested_usd'],
                                'current_value_usd': pnl_data['current_value_usd'],
                                'pnl_net_usd': pnl_data['pnl_net_usd']
                            }
                        
                        prices[ticker] = price_data
            except Exception as e:
                print(f"⚠️ Error fetching price for {ticker}: {e}")
                prices[ticker] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'prices': prices,
            'exchange_rates': EXCHANGE_RATES,
            'markets': {market: is_market_open(market) for market in MARKET_SCHEDULES.keys()},
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/markets/status')
def api_markets_status():
    """
    Get status of all markets (open/closed/extended hours).
    Returns status for US, CH, EU markets.
    """
    try:
        markets = {}
        for market in MARKET_SCHEDULES.keys():
            markets[market] = is_market_open(market)
        
        return jsonify({
            'success': True,
            'markets': markets,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/live/price/<ticker>')
def api_get_live_price(ticker):
    """
    Fetch live price for a single ticker with accurate day change.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get accurate intraday change
        intraday = get_intraday_change(ticker)
        
        # Get chart data
        hist = stock.history(period="1d", interval="5m")
        
        if intraday or not hist.empty:
            if intraday:
                current_price = intraday['price']
                previous_close = intraday['previous_close']
                day_change = intraday['day_change']
                day_change_percent = intraday['day_change_percent']
            else:
                current_price = float(hist['Close'].iloc[-1])
                try:
                    info = stock.fast_info
                    previous_close = getattr(info, 'previous_close', None)
                    if previous_close:
                        day_change = current_price - previous_close
                        day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else 0
                    else:
                        open_price = float(hist['Open'].iloc[0])
                        day_change = current_price - open_price
                        day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
                except:
                    open_price = float(hist['Open'].iloc[0])
                    day_change = current_price - open_price
                    day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
            
            if not hist.empty:
                day_high = float(hist['High'].max())
                day_low = float(hist['Low'].min())
                chart_data = hist['Close'].tolist()[-78:]
            else:
                day_high = current_price
                day_low = current_price
                chart_data = []
            
            return jsonify({
                'success': True,
                'ticker': ticker,
                'price': current_price,
                'previous_close': intraday.get('previous_close') if intraday else None,
                'high': day_high,
                'low': day_low,
                'change': day_change,
                'change_percent': day_change_percent,
                'chart': chart_data,
                'currency': get_ticker_currency(ticker),
                'updated': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_flask():
    """Run Flask API server in a separate thread"""
    app.run(host='0.0.0.0', port=5555, debug=False, use_reloader=False)


def is_nasdaq_hours() -> tuple:
    """
    Check NASDAQ market status.
    Returns (is_open, is_extended) where:
    - is_open: True if market is open (9:30-16:00 ET = 15:30-22:00 CET)
    - is_extended: True if in extended hours (1h before open or 1h after close)
    """
    now = datetime.now(NY_TZ)
    current_time = now.time()
    
    # NASDAQ hours in ET
    market_open = datetime.strptime('09:30', '%H:%M').time()
    market_close = datetime.strptime('16:00', '%H:%M').time()
    pre_market = datetime.strptime('08:30', '%H:%M').time()  # 1h before open
    post_market = datetime.strptime('17:00', '%H:%M').time()  # 1h after close
    
    is_open = market_open <= current_time <= market_close
    is_extended = (pre_market <= current_time < market_open) or (market_close < current_time <= post_market)
    
    return is_open, is_extended


def should_take_snapshot() -> bool:
    """
    Determine if a snapshot should be taken based on current time.
    - Every 15 min when NASDAQ is open
    - Every hour during extended hours (1h before/after)
    - No snapshots outside these hours
    """
    if not is_market_day():
        return False
    
    is_open, is_extended = is_nasdaq_hours()
    now = datetime.now(ZURICH_TZ)
    minute = now.minute
    
    if is_open:
        # Every 15 minutes during market hours
        return minute in [0, 15, 30, 45]
    elif is_extended:
        # Every hour during extended hours
        return minute == 0
    else:
        return False


def run_scheduler():
    """Main scheduler loop"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   📊 PORTFOLIO TRACKER SERVICE                            ║
║   Dedicated portfolio performance tracking                ║
║   - Every 15 min when NASDAQ is open (15:30-22:00 CET)    ║
║   - Every hour during extended hours (±1h)                ║
║   + Live Prices API on port 5555                          ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Initialize database
    init_db()
    
    # Start Flask API in a separate thread
    api_thread = threading.Thread(target=run_flask, daemon=True)
    api_thread.start()
    print("🌐 Live Prices API started on port 5555")
    
    # Schedule check every minute to see if snapshot needed
    print("⏰ Snapshot schedule (Zurich time):")
    print("   14:30-15:30 → Hourly (pre-market)")
    print("   15:30-22:00 → Every 15 minutes (market open)")
    print("   22:00-23:00 → Hourly (post-market)")
    print()
    
    # Generate initial snapshot at startup if during market hours
    print("🚀 Checking if snapshot needed...")
    if should_take_snapshot() or True:  # Always take one at startup
        generate_portfolio_snapshot()
    else:
        print("   ⏸️ Outside market hours - waiting for next window")
    
    print("\n✅ Portfolio Tracker running. Checking every minute...")
    print("   Press Ctrl+C to stop.\n")
    
    # Main loop - check every minute
    last_snapshot_minute = -1
    while True:
        now = datetime.now(ZURICH_TZ)
        current_minute = now.minute
        
        # Only check once per minute
        if current_minute != last_snapshot_minute:
            if should_take_snapshot():
                generate_portfolio_snapshot()
            last_snapshot_minute = current_minute
        
        time.sleep(30)  # Check twice per minute for precision


if __name__ == "__main__":
    run_scheduler()
