"""Calcul des indicateurs techniques"""
import numpy as np

def get_technical_indicators(hist):
    """Calcule tous les indicateurs techniques"""
    try:
        close_prices = hist['Close']
        high_prices = hist['High']
        low_prices = hist['Low']
        volumes = hist['Volume']
        
        indicators = {}
        
        # === RSI (Relative Strength Index) ===
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = safe_float(rsi.iloc[-1])
        
        # === Moyennes Mobiles ===
        indicators['ma_20'] = safe_float(close_prices.rolling(window=20).mean().iloc[-1])
        indicators['ma_50'] = safe_float(close_prices.rolling(window=50).mean().iloc[-1])
        indicators['ma_200'] = safe_float(close_prices.rolling(window=200).mean().iloc[-1]) if len(close_prices) >= 200 else None
        
        # === MACD (Moving Average Convergence Divergence) ===
        exp1 = close_prices.ewm(span=12, adjust=False).mean()
        exp2 = close_prices.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        indicators['macd'] = safe_float(macd_line.iloc[-1])
        indicators['macd_signal'] = safe_float(signal_line.iloc[-1])
        indicators['macd_histogram'] = safe_float(macd_histogram.iloc[-1])
        
        # === Bollinger Bands ===
        sma_20 = close_prices.rolling(window=20).mean()
        std_20 = close_prices.rolling(window=20).std()
        
        indicators['bb_upper'] = safe_float((sma_20 + (std_20 * 2)).iloc[-1])
        indicators['bb_middle'] = safe_float(sma_20.iloc[-1])
        indicators['bb_lower'] = safe_float((sma_20 - (std_20 * 2)).iloc[-1])
        
        # Position du prix dans les bandes (%)
        current_price = close_prices.iloc[-1]
        if indicators['bb_upper'] and indicators['bb_lower']:
            bb_range = indicators['bb_upper'] - indicators['bb_lower']
            if bb_range > 0:
                indicators['bb_position'] = ((current_price - indicators['bb_lower']) / bb_range) * 100
            else:
                indicators['bb_position'] = 50.0
        
        # === Volume ===
        avg_volume_20 = volumes.rolling(window=20).mean()
        indicators['volume_avg'] = safe_float(avg_volume_20.iloc[-1])
        indicators['volume_current'] = safe_float(volumes.iloc[-1])
        
        # Ratio volume actuel vs moyenne
        if indicators['volume_avg'] and indicators['volume_avg'] > 0:
            indicators['volume_ratio'] = (indicators['volume_current'] / indicators['volume_avg'])
        else:
            indicators['volume_ratio'] = 1.0
        
        # === ATR (Average True Range) - Volatilité ===
        high_low = high_prices - low_prices
        high_close = np.abs(high_prices - close_prices.shift())
        low_close = np.abs(low_prices - close_prices.shift())
        
        ranges = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = ranges.rolling(window=14).mean()
        indicators['atr'] = safe_float(atr.iloc[-1])
        
        # ATR en % du prix
        if current_price > 0:
            indicators['atr_percent'] = (indicators['atr'] / current_price) * 100 if indicators['atr'] else None
        
        # === Stochastic Oscillator ===
        low_14 = low_prices.rolling(window=14).min()
        high_14 = high_prices.rolling(window=14).max()
        
        stoch_k = 100 * ((close_prices - low_14) / (high_14 - low_14))
        stoch_d = stoch_k.rolling(window=3).mean()
        
        indicators['stoch_k'] = safe_float(stoch_k.iloc[-1])
        indicators['stoch_d'] = safe_float(stoch_d.iloc[-1])
        
        # === Support et Résistance (simples) ===
        recent_high = high_prices.tail(20).max()
        recent_low = low_prices.tail(20).min()
        
        indicators['resistance'] = safe_float(recent_high)
        indicators['support'] = safe_float(recent_low)
        
        return indicators
        
    except Exception as e:
        print(f"⚠️ Erreur calcul indicateurs: {e}")
        return {
            'rsi': None, 'ma_20': None, 'ma_50': None, 'ma_200': None,
            'macd': None, 'macd_signal': None, 'macd_histogram': None,
            'bb_upper': None, 'bb_middle': None, 'bb_lower': None, 'bb_position': None,
            'volume_avg': None, 'volume_current': None, 'volume_ratio': None,
            'atr': None, 'atr_percent': None,
            'stoch_k': None, 'stoch_d': None,
            'resistance': None, 'support': None
        }


def safe_float(value):
    """Convertit une valeur en float ou retourne None si NaN"""
    try:
        if value is None or (isinstance(value, float) and (value != value)):  # Check NaN
            return None
        return float(value)
    except:
        return None


def interpret_indicators(indicators, current_price):
    """Interprète les indicateurs et génère des insights"""
    insights = []
    
    # RSI
    rsi = indicators.get('rsi')
    if rsi:
        if rsi < 30:
            insights.append(f"🟢 RSI survendu ({rsi:.1f}) - Signal d'achat potentiel")
        elif rsi > 70:
            insights.append(f"🔴 RSI suracheté ({rsi:.1f}) - Risque de correction")
        else:
            insights.append(f"🟡 RSI neutre ({rsi:.1f})")
    
    # Moyennes mobiles
    ma20 = indicators.get('ma_20')
    ma50 = indicators.get('ma_50')
    
    if ma20 and ma50:
        if current_price > ma20 > ma50:
            insights.append("🚀 Prix > MA20 > MA50 - Tendance haussière forte")
        elif current_price < ma20 < ma50:
            insights.append("📉 Prix < MA20 < MA50 - Tendance baissière")
        elif current_price > ma20 and current_price < ma50:
            insights.append("🟡 Prix entre MA20 et MA50 - Consolidation")
    
    # MACD
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    
    if macd and macd_signal:
        if macd > macd_signal and macd > 0:
            insights.append("🟢 MACD positif et au-dessus du signal - Momentum haussier")
        elif macd < macd_signal and macd < 0:
            insights.append("🔴 MACD négatif et sous le signal - Momentum baissier")
    
    # Bollinger Bands
    bb_position = indicators.get('bb_position')
    if bb_position:
        if bb_position > 80:
            insights.append(f"🔴 Prix proche bande supérieure ({bb_position:.0f}%) - Suracheté")
        elif bb_position < 20:
            insights.append(f"🟢 Prix proche bande inférieure ({bb_position:.0f}%) - Survendu")
    
    # Volume
    volume_ratio = indicators.get('volume_ratio')
    if volume_ratio:
        if volume_ratio > 1.5:
            insights.append(f"📊 Volume élevé ({volume_ratio:.1f}x moyenne) - Fort intérêt")
        elif volume_ratio < 0.7:
            insights.append(f"📊 Volume faible ({volume_ratio:.1f}x moyenne) - Faible conviction")
    
    # Stochastic
    stoch_k = indicators.get('stoch_k')
    if stoch_k:
        if stoch_k < 20:
            insights.append(f"🟢 Stochastique survendu ({stoch_k:.1f}) - Rebond possible")
        elif stoch_k > 80:
            insights.append(f"🔴 Stochastique suracheté ({stoch_k:.1f}) - Correction possible")
    
    return insights
