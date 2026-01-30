"""Module d'analyse IA - Approche Hybride Claude (Haiku → Sonnet)"""
import time
import json
import requests
import os
from datetime import datetime

# Configuration API Claude
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_claude_api(prompt, model, max_tokens=256, temperature=0.2, system_prompt=None):
    """Appelle l'API Claude - Fonction de base"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("❌ ANTHROPIC_API_KEY manquante dans .env")
    
    if not ANTHROPIC_API_KEY.startswith('sk-ant-'):
        raise ValueError(f"❌ ANTHROPIC_API_KEY invalide (doit commencer par 'sk-ant-'). Actuellement: {ANTHROPIC_API_KEY[:10]}...")
    
    start_time = time.time()
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    if system_prompt:
        data["system"] = system_prompt
    
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        elapsed_time = time.time() - start_time
        text = result["content"][0]["text"] if "content" in result else ""
        return text, elapsed_time
    except requests.exceptions.HTTPError as e:
        # Erreur HTTP détaillée
        error_detail = ""
        try:
            error_detail = response.json()
        except:
            error_detail = response.text
        print(f"❌ Erreur API Claude ({response.status_code}): {error_detail}")
        return "", 0
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API Claude: {e}")
        return "", 0


# ============================================================================
# PHASE 1: SCREENING RAPIDE (HAIKU)
# ============================================================================

def build_screening_prompt(ticker, analysis_data, current_price, monthly_change):
    """Construit prompt CONCIS pour screening Haiku"""
    info = analysis_data.get('info', {})
    news = analysis_data.get('news', [])
    
    company = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    pe = info.get('trailingPE', 'N/A')
    recommendation = info.get('recommendationKey', 'N/A')
    
    prompt = f"""Screening rapide: {ticker} ({company})

DONNÉES:
• Secteur: {sector}
• Prix: {current_price:.2f}$
• Var 1 mois: {monthly_change:+.2f}%
• P/E: {pe}
• Consensus: {recommendation}
• News: {len(news)} articles récents

INSTRUCTIONS:
Fournis un screening en 3 lignes MAX:
1. SCORE: X/100
2. FLAG: À APPROFONDIR (si ≥60) OU RAS (si <60)
3. RAISON: 1 phrase justifiant

Sois objectif et concis."""
    
    return prompt


def screen_with_haiku(ticker, analysis_data, current_price, monthly_change):
    """
    Phase 1: Screening rapide avec Haiku
    
    Returns:
        dict: {
            'score': int,
            'flag': str,
            'reason': str,
            'should_analyze': bool
        }
    """
    from config import CLAUDE_CONFIG
    
    print(f"  🔍 Screening Haiku...", end=" ")
    
    prompt = build_screening_prompt(ticker, analysis_data, current_price, monthly_change)
    
    haiku_config = CLAUDE_CONFIG['screening']
    system_prompt = """Tu es un analyste quantitatif.
Fournis un screening objectif en 3 lignes: SCORE, FLAG, RAISON."""
    
    response, elapsed = call_claude_api(
        prompt=prompt,
        model=haiku_config['model'],
        max_tokens=haiku_config['max_tokens'],
        temperature=haiku_config['temperature'],
        system_prompt=system_prompt
    )
    
    # Parser réponse
    score = 50
    flag = 'RAS'
    reason = response
    
    lines = response.strip().split('\n')
    for line in lines:
        line_upper = line.upper()
        if 'SCORE' in line_upper or '/100' in line:
            import re
            match = re.search(r'(\d+)(?:/100)?', line)
            if match:
                score = int(match.group(1))
        elif 'FLAG' in line_upper:
            if 'APPROFONDIR' in line_upper:
                flag = 'À APPROFONDIR'
        elif 'RAISON' in line_upper:
            reason = line.split(':', 1)[-1].strip()
    
    should_analyze = (score >= 60 and flag == 'À APPROFONDIR')
    
    print(f"Score: {score}/100 - {flag} ({elapsed:.1f}s)")
    
    return {
        'score': score,
        'flag': flag,
        'reason': reason,
        'should_analyze': should_analyze,
        'screening_time': elapsed
    }


# ============================================================================
# PHASE 2: ANALYSE APPROFONDIE (SONNET) - PROMPTS
# ============================================================================

def build_analysis_prompt(ticker, hist_1mo, info, indicators, advanced=False, 
                          news=None, calendar=None, recommendations=None,
                          alpha_vantage=None, fred_macro=None):
    """
    Construit prompt COMPLET pour analyse Sonnet
    Ajoute alpha_vantage et fred_macro aux paramètres existants
    """
    
    current_price = hist_1mo['Close'].iloc[-1] if not hist_1mo.empty else 0
    open_price = hist_1mo['Open'].iloc[-1] if not hist_1mo.empty else 0
    volume = hist_1mo['Volume'].iloc[-1] if not hist_1mo.empty else 0
    
    if len(hist_1mo) >= 2:
        monthly_change = ((current_price - hist_1mo['Close'].iloc[0]) / hist_1mo['Close'].iloc[0] * 100)
    else:
        monthly_change = 0
    
    company_name = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 'N/A')
    dividend_yield = info.get('dividendYield', 0)
    target_price = info.get('targetMeanPrice', 'N/A')
    recommendation = info.get('recommendationKey', 'N/A')
    
    if market_cap and market_cap > 0:
        if market_cap >= 1e12:
            market_cap_str = f"{market_cap/1e12:.2f}T$"
        elif market_cap >= 1e9:
            market_cap_str = f"{market_cap/1e9:.2f}B$"
        else:
            market_cap_str = f"{market_cap/1e6:.2f}M$"
    else:
        market_cap_str = "N/A"
    
    prompt = f"""# ANALYSE FINANCIÈRE - {ticker}

## PROFIL
- **{company_name}**
- Secteur: {sector}
- Cap: {market_cap_str}

## PRIX
- Actuel: {current_price:.2f}$
- Var 1M: {monthly_change:+.2f}%
- Volume: {volume:,.0f}

## VALORISATION
- P/E: {pe_ratio}
- Dividende: {f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A"}
- Target: {f"{target_price:.2f}$" if isinstance(target_price, (int, float)) else target_price}
- Consensus: {recommendation}

## INDICATEURS TECHNIQUES
"""
    
    if indicators:
        rsi = indicators.get('rsi')
        if rsi:
            prompt += f"- RSI: {rsi:.1f}\n"
        ma_20 = indicators.get('ma_20')
        if ma_20:
            prompt += f"- MA20: {ma_20:.2f}$ (Prix: {current_price:.2f}$)\n"
        macd = indicators.get('macd')
        if macd:
            prompt += f"- MACD: {macd:.3f}\n"
    
    # NOUVEAU: Alpha Vantage
    if alpha_vantage:
        prompt += f"\n## FONDAMENTAUX DÉTAILLÉS\n"
        if alpha_vantage.get('profit_margin'):
            prompt += f"- Marge: {alpha_vantage['profit_margin']}\n"
        if alpha_vantage.get('roe'):
            prompt += f"- ROE: {alpha_vantage['roe']}\n"
    
    # NOUVEAU: FRED
    if fred_macro:
        prompt += f"\n## CONTEXTE MACRO\n"
        if fred_macro.get('fed_funds_rate'):
            prompt += f"- Taux FED: {fred_macro['fed_funds_rate']['value']}%\n"
        if fred_macro.get('unemployment'):
            prompt += f"- Chômage: {fred_macro['unemployment']['value']}%\n"
    
    if news:
        prompt += f"\n## NEWS ({len(news)} articles)\n"
        for i, article in enumerate(news[:3], 1):
            prompt += f"{i}. {article.get('title', 'N/A')}\n"
    
    prompt += """
---

FOURNIS:
SIGNAL: [ACHETER/VENDRE/CONSERVER]
CONVICTION: [Forte/Moyenne/Faible]
RÉSUMÉ: [Une phrase]

Puis analyse détaillée."""
    
    return prompt


def generate_analysis(ticker, model, context, num_threads=12):
    """
    FONCTION PRINCIPALE - Compatible analyzer.py
    
    Returns:
        tuple: (analysis_text, elapsed_time)
    """
    from config import CLAUDE_CONFIG
    
    print(f"  🤖 Analyse Sonnet...", end=" ")
    
    sonnet_config = CLAUDE_CONFIG['deep_analysis']
    
    system_prompt = """Tu es un analyste financier senior.

COMMENCE PAR:
SIGNAL: [ACHETER/VENDRE/CONSERVER]
CONVICTION: [Forte/Moyenne/Faible]
RÉSUMÉ: [Une phrase]

Puis analyse détaillée."""
    
    try:
        analysis_text, elapsed_time = call_claude_api(
            prompt=context,
            model=sonnet_config['model'],
            max_tokens=sonnet_config['max_tokens'],
            temperature=sonnet_config['temperature'],
            system_prompt=system_prompt
        )
        
        if analysis_text:
            print(f"OK ({elapsed_time:.1f}s)")
            return analysis_text, elapsed_time
        else:
            print(f"ÉCHEC")
            return None, 0
            
    except Exception as e:
        print(f"ERREUR: {e}")
        return None, 0


# ============================================================================
# PORTFOLIO
# ============================================================================

def build_portfolio_analysis_prompt(positions, latest_analyses):
    """Construit prompt portfolio"""
    total_invested = sum(p.get('entry_price', 0) * p.get('quantity', 1) for p in positions)
    total_value = sum(p.get('current_price', p.get('entry_price', 0)) * p.get('quantity', 1) for p in positions)
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    prompt = f"""# ANALYSE PORTEFEUILLE

Capital: {total_invested:,.2f}$ | Actuel: {total_value:,.2f}$ | P&L: {total_pnl:+.2f}$ ({total_pnl_percent:+.2f}%)
Positions: {len(positions)}

"""

    for i, pos in enumerate(positions, 1):
        ticker = pos.get('ticker', 'N/A')
        entry = pos.get('entry_price', 0)
        current = pos.get('current_price', entry)
        pnl_pct = pos.get('pnl_percent', 0)
        
        analysis = latest_analyses.get(ticker, {})
        signal = analysis.get('signal', 'N/A')
        
        prompt += f"{i}. {ticker}: {entry:.2f}$→{current:.2f}$ ({pnl_pct:+.2f}%) | Signal: {signal}\n"

    prompt += """
RÉPONDS JSON:
{"resume_global": {"etat_portfolio": "...", "score_sante": 75}, "conseils_positions": [...]}
"""
    
    return prompt


def generate_portfolio_analysis(positions, latest_analyses, model, num_threads=12):
    """Analyse portfolio"""
    from config import CLAUDE_CONFIG
    
    if not positions:
        return None, 0
    
    print(f"🤖 Portfolio Sonnet ({len(positions)} pos)...")
    
    prompt = build_portfolio_analysis_prompt(positions, latest_analyses)
    portfolio_config = CLAUDE_CONFIG['portfolio']
    
    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config['max_tokens'],
            temperature=portfolio_config['temperature'],
            system_prompt="Gestionnaire portfolio. JSON uniquement."
        )
        
        clean = response.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean = '\n'.join(lines)
        
        try:
            analysis_json = json.loads(clean)
            print(f"✅ OK ({elapsed:.1f}s)")
            return analysis_json, elapsed
        except json.JSONDecodeError:
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, 0
