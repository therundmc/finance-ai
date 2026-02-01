"""Module d'analyse IA - Approche Hybride Claude (Haiku → Sonnet)"""
import time
import json
import requests
import os
from datetime import datetime

# Configuration API Claude
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_claude_api(prompt, model, max_tokens=256, temperature=0.2, system_prompt=None, timeout=60):
    """
    Appelle l'API Claude avec retry sur rate limit (429) et fallback vers Ollama local.

    Args:
        timeout: Timeout en secondes (défaut 60, augmenter pour portfolio)

    Returns:
        tuple: (response_text, elapsed_time)
    """
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY manquante - Fallback vers Ollama")
        return _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt)

    if not ANTHROPIC_API_KEY.startswith('sk-ant-'):
        print(f"⚠️ ANTHROPIC_API_KEY invalide - Fallback vers Ollama")
        return _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt)

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

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=timeout)

            # Handle rate limit (429) with retry
            if response.status_code == 429:
                retry_after = response.headers.get('retry-after', '')
                try:
                    wait_time = int(retry_after)
                except (ValueError, TypeError):
                    wait_time = 30 + (attempt * 15)

                print(f"⏳ Rate limit atteint (429) - attente {wait_time}s avant retry ({attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            result = response.json()
            elapsed_time = time.time() - start_time
            text = result["content"][0]["text"] if "content" in result else ""
            return text, elapsed_time

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            print(f"❌ Erreur API Claude ({response.status_code}): {error_detail}")
            print(f"🔄 Tentative fallback vers Ollama local...")
            return _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur API Claude: {e}")
            print(f"🔄 Tentative fallback vers Ollama local...")
            return _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt)

    # All retries exhausted
    print(f"❌ Rate limit: {max_retries} retries epuises - Fallback vers Ollama")
    return _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt)


def _fallback_ollama(prompt, model, max_tokens, temperature, system_prompt=None):
    """
    Fallback vers Ollama local si Claude API échoue
    """
    try:
        import ollama
        
        # Récupérer le modèle local depuis config
        from config import load_config
        config = load_config()
        local_model = config.get('model', 'mistral-nemo')
        num_threads = config.get('num_threads', 12)
        
        print(f"   🤖 Ollama local: {local_model}")
        
        start_time = time.time()
        
        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        response = ollama.chat(
            model=local_model,
            messages=messages,
            options={
                'temperature': temperature,
                'num_predict': max_tokens,
                'num_thread': num_threads
            }
        )
        
        elapsed_time = time.time() - start_time
        text = response['message']['content'] if 'message' in response else ""
        
        print(f"   ✅ Ollama OK ({elapsed_time:.1f}s)")
        return text, elapsed_time
        
    except ImportError:
        print(f"   ❌ Module ollama non installé (pip install ollama)")
        return "", 0
    except Exception as e:
        print(f"   ❌ Erreur Ollama: {e}")
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
    Construit prompt COMPLET pour analyse Approfondie
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
        for i, article in enumerate(news[:10], 1):  # Augmenté de 3 à 10
            title = article.get('title', 'N/A')
            summary = article.get('summary', '')[:150] if article.get('summary') else ''
            prompt += f"{i}. **{title}**\n"
            if summary:
                prompt += f"   {summary}\n"
    
    # Préparer les valeurs pour le JSON template
    rsi_value = indicators.get('rsi') if indicators else None
    rsi_str = f"{rsi_value:.1f}" if isinstance(rsi_value, (int, float)) and rsi_value is not None else "N/A"
    
    prompt += f"""
---

## FORMAT DE RÉPONSE - JSON STRUCTURÉ OBLIGATOIRE

Réponds UNIQUEMENT avec un objet JSON valide (sans balises markdown ```json).

{{
  "signal": "ACHETER | VENDRE | CONSERVER",
  "conviction": "Forte | Moyenne | Faible",
  "resume": "Résumé de 2-3 phrases expliquant ta recommandation et les raisons principales",
  "analyse_technique": {{
    "tendance": "Haussière | Baissière | Neutre",
    "rsi_interpretation": "RSI {rsi_str}: analyse et interprétation",
    "macd_interpretation": "MACD: analyse et signal",
    "volatilite": "Volatilité et niveaux clés"
  }},
  "analyse_fondamentale": {{
    "valorisation": "Sous-évaluée | Correcte | Sur-évaluée avec justification",
    "points_forts": ["Point fort 1 détaillé", "Point fort 2"],
    "points_faibles": ["Point faible 1 détaillé", "Point faible 2"]
  }},
  "catalyseurs": [
    {{"type": "positif", "description": "Catalyseur haussier identifié"}},
    {{"type": "négatif", "description": "Risque baissier identifié"}}
  ],
  "risques": ["Risque principal 1", "Risque 2"],
  "niveaux": {{
    "achat_recommande": {current_price * 0.98:.2f},
    "stop_loss": {current_price * 0.92:.2f},
    "objectif_1": {current_price * 1.08:.2f},
    "objectif_2": {current_price * 1.15:.2f}
  }},
  "conclusion": "Synthèse finale de 2-3 phrases avec perspective"
}}

IMPORTANT:
- Fournis des analyses DÉTAILLÉES et COMPLÈTES
- Le résumé doit faire 2-3 phrases
- Remplis TOUS les champs avec du contenu substantiel
- Les niveaux doivent être basés sur le prix actuel ({current_price:.2f}$)
- Sois précis, chiffré et actionnable
- Assure-toi que le JSON est COMPLET et VALIDE (pas coupé)
- Pas de balises markdown, juste le JSON pur
"""
    
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
    
    system_prompt = """Tu es un analyste financier senior avec 15 ans d'expérience.

Tu analyses les actions de manière approfondie en considérant:
- L'analyse technique (tendances, indicateurs, niveaux clés)
- L'analyse fondamentale (valorisation, santé financière)
- Les actualités et catalyseurs
- Les risques identifiables

Tu réponds UNIQUEMENT en JSON structuré, sans texte avant ou après, sans balises markdown.
Fournis des analyses détaillées et substantielles pour chaque champ."""
    
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

def build_portfolio_analysis_prompt(positions, all_analyses, news_summaries=None, config=None):
    """
    Construit le prompt pour l'analyse globale du portefeuille.
    Inclut toutes les actions surveillées, les news et le profil investisseur.

    Args:
        positions: Liste des positions ouvertes avec leurs données
        all_analyses: Dict des dernières analyses par ticker (tous les tickers surveillés)
        news_summaries: Dict des résumés de news par catégorie
        config: Configuration avec budget, risk_level, investment_objective

    Returns:
        str: Prompt formaté pour l'analyse IA du portefeuille
    """
    from datetime import datetime
    import statistics

    config = config or {}
    news_summaries = news_summaries or {}

    # Budget et profil
    budget = config.get('budget', 10000)
    budget_currency = config.get('budget_currency', 'CHF')
    risk_level = config.get('risk_level', 'modere')
    objective = config.get('investment_objective', 'croissance long terme')
    trading = config.get('trading', {})

    # Support both percentage and fixed commissions
    buy_commission_pct = trading.get('buy_commission_pct')
    sell_commission_pct = trading.get('sell_commission_pct')
    buy_commission_fixed = trading.get('buy_commission', 10)
    sell_commission_fixed = trading.get('sell_commission', 12)
    commission_currency = trading.get('commission_currency', 'CHF')

    # Use percentage if available, otherwise use fixed
    if buy_commission_pct is not None:
        commission_text = f"achat {buy_commission_pct}%, vente {sell_commission_pct}%"
        total_roundtrip_pct = (buy_commission_pct + sell_commission_pct) if buy_commission_pct else 0
    else:
        commission_text = f"achat {buy_commission_fixed} {commission_currency}, vente {sell_commission_fixed} {commission_currency}"
        total_roundtrip_pct = 0

    # Portfolio totals
    total_invested = sum(p.get('entry_price', 0) * p.get('quantity', 1) for p in positions) if positions else 0
    total_value = sum(p.get('current_price', p.get('entry_price', 0)) * p.get('quantity', 1) for p in positions) if positions else 0
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Owned tickers
    owned_tickers = set(p.get('ticker', '') for p in positions) if positions else set()

    # AMELIORATION #1: Récupérer l'historique des recommandations
    from database import get_latest_portfolio_analysis
    previous_analysis = get_latest_portfolio_analysis()

    # AMELIORATION #2: Calculer le contexte macro
    def calculate_macro_context(analyses):
        """Calcule le contexte macro à partir des analyses disponibles"""
        if not analyses:
            return None

        # Changements 1 jour
        changes_1d = [a.get('change_1d', 0) for a in analyses.values() if a.get('change_1d') is not None]

        if not changes_1d or len(changes_1d) < 2:
            return None

        avg_change = sum(changes_1d) / len(changes_1d)
        volatility = statistics.stdev(changes_1d)

        # Sentiment général
        signals = [a.get('signal', '') for a in analyses.values()]
        bullish = sum(1 for s in signals if 'ACHETER' in str(s).upper())
        bearish = sum(1 for s in signals if 'VENDRE' in str(s).upper())
        total_signals = len(signals)

        bullish_pct = (bullish / total_signals * 100) if total_signals > 0 else 0
        bearish_pct = (bearish / total_signals * 100) if total_signals > 0 else 0

        # Déterminer le mood
        if bullish > bearish * 1.5:
            mood = 'BULL'
        elif bearish > bullish * 1.5:
            mood = 'BEAR'
        else:
            mood = 'NEUTRE'

        # Niveau de volatilité
        if volatility > 2.5:
            vol_level = 'HAUTE'
        elif volatility > 1.5:
            vol_level = 'MODEREE'
        else:
            vol_level = 'FAIBLE'

        return {
            'avg_change_1d': avg_change,
            'volatility': volatility,
            'vol_level': vol_level,
            'mood': mood,
            'bullish_pct': bullish_pct,
            'bearish_pct': bearish_pct,
            'total_analyzed': total_signals
        }

    macro_context = calculate_macro_context(all_analyses)

    # NOUVEAU: Calculer la répartition sectorielle + MOMENTUM
    sector_allocation = {}
    for pos in positions:
        ticker = pos.get('ticker', '')
        analysis = all_analyses.get(ticker, {})
        sector = analysis.get('sector', 'Unknown')
        position_value = pos.get('current_price', pos.get('entry_price', 0)) * pos.get('quantity', 1)

        if sector not in sector_allocation:
            sector_allocation[sector] = {
                'value': 0,
                'tickers': [],
                'changes_1mo': [],
                'signals': []
            }
        sector_allocation[sector]['value'] += position_value
        sector_allocation[sector]['tickers'].append(ticker)
        sector_allocation[sector]['changes_1mo'].append(analysis.get('change_1mo', 0) or 0)
        sector_allocation[sector]['signals'].append(analysis.get('signal', ''))

    # Calculer les pourcentages et momentum
    for sector in sector_allocation:
        pct = (sector_allocation[sector]['value'] / total_value * 100) if total_value > 0 else 0
        sector_allocation[sector]['pct'] = pct

        # Momentum sectoriel
        changes = sector_allocation[sector]['changes_1mo']
        avg_change = sum(changes) / len(changes) if changes else 0
        sector_allocation[sector]['momentum_1mo'] = avg_change

        # Signaux positifs
        signals = sector_allocation[sector]['signals']
        bullish = sum(1 for s in signals if 'ACHETER' in str(s).upper())
        sector_allocation[sector]['bullish_count'] = bullish
        sector_allocation[sector]['bullish_pct'] = (bullish / len(signals) * 100) if signals else 0

    prompt = f"""# CONSEILLER FINANCIER PERSONNEL - ANALYSE QUOTIDIENNE
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## TON ROLE
Tu es mon conseiller financier personnel. Je suivrai tes recommandations directement.
Dis-moi clairement quoi ACHETER, VENDRE, et CONSERVER aujourd'hui.
Maximise la probabilite de rendement positif. Recommande uniquement des achats a haute conviction.

## PROFIL INVESTISSEUR
- **Budget disponible:** {budget:,.0f} {budget_currency}
- **Niveau de risque:** {risk_level}
- **Objectif:** {objective}
- **Commissions:** {commission_text}

## PORTEFEUILLE ACTUEL ({len(positions)} positions)
- **Capital investi:** {total_invested:,.2f}$
- **Valeur actuelle:** {total_value:,.2f}$
- **P&L Total:** {total_pnl:+,.2f}$ ({total_pnl_percent:+.2f}%)

### ALLOCATION SECTORIELLE (CRITIQUE pour diversification)
"""

    # Ajouter allocation sectorielle + MOMENTUM au prompt
    if sector_allocation:
        sectors_sorted = sorted(sector_allocation.items(), key=lambda x: x[1]['pct'], reverse=True)
        for sector, data in sectors_sorted:
            tickers_str = ', '.join(data['tickers'])
            momentum = data['momentum_1mo']
            bullish_pct = data['bullish_pct']

            # Emoji momentum
            momentum_emoji = '🔥' if momentum > 10 else '📈' if momentum > 5 else '📊' if momentum > 0 else '📉' if momentum > -5 else '❄️'

            prompt += f"- **{sector}**: {data['pct']:.1f}% ({tickers_str})\n"
            prompt += f"  Momentum 1mo: {momentum:+.1f}% | Signaux bullish: {data['bullish_count']}/{len(data['tickers'])} {momentum_emoji}\n"

        prompt += "\n### ANALYSE RISQUE/OPPORTUNITE PAR SECTEUR\n"
        for sector, data in sectors_sorted:
            pct = data['pct']
            momentum = data['momentum_1mo']
            bullish_pct = data['bullish_pct']

            # Déterminer le statut
            if pct > 60:
                if momentum > 10 and bullish_pct > 50:
                    status = f"⚠️ TRES CONCENTRE ({pct:.0f}%) MAIS momentum fort → Conserver, ne pas renforcer"
                else:
                    status = f"🚨 SURCONCENTRATION CRITIQUE ({pct:.0f}%) → PRIORITE: Diversifier"
            elif pct > 40:
                if momentum > 8 and bullish_pct > 50:
                    status = f"✅ Concentration élevée ({pct:.0f}%) avec momentum fort → OK pour petits renforts"
                else:
                    status = f"⚠️ Concentration notable ({pct:.0f}%) → Prudence sur nouveaux achats"
            elif pct < 15:
                if momentum > 5 or bullish_pct > 50:
                    status = f"🎯 OPPORTUNITE ({pct:.0f}%) sous-représenté avec potentiel → Considérer renforcement"
                else:
                    status = f"📊 Sous-représenté ({pct:.0f}%) → Evaluer opportunités"
            else:
                status = f"✅ Allocation équilibrée ({pct:.0f}%)"

            prompt += f"- **{sector}**: {status}\n"

    prompt += "\n"

    # AMELIORATION #3: Calculer la matrice de corrélation et risque caché
    def calculate_correlation_risk(positions, analyses):
        """
        Calcule les corrélations entre positions et détecte les risques cachés.
        Utilise secteur + momentum pour estimer corrélation.
        """
        if not positions or len(positions) < 2:
            return None

        # Grouper par secteur
        by_sector = {}
        for pos in positions:
            ticker = pos.get('ticker', '')
            analysis = analyses.get(ticker, {})
            sector = analysis.get('sector', 'Unknown')

            if sector not in by_sector:
                by_sector[sector] = []
            by_sector[sector].append({
                'ticker': ticker,
                'value': pos.get('current_price', pos.get('entry_price', 0)) * pos.get('quantity', 1),
                'change_1mo': analysis.get('change_1mo', 0) or 0
            })

        # Identifier groupes fortement corrélés (même secteur)
        high_correlation_groups = []
        total_value = sum(p.get('current_price', p.get('entry_price', 0)) * p.get('quantity', 1) for p in positions)

        for sector, tickers_data in by_sector.items():
            if len(tickers_data) >= 2:  # Au moins 2 positions dans le secteur
                sector_value = sum(t['value'] for t in tickers_data)
                sector_pct = (sector_value / total_value * 100) if total_value > 0 else 0

                # Estimer corrélation (même secteur = corrélation élevée ~0.7-0.9)
                correlation_estimate = 0.75 + (len(tickers_data) * 0.05)  # Plus de tickers = plus corrélés
                correlation_estimate = min(0.95, correlation_estimate)

                # Calculer momentum moyen du groupe
                avg_momentum = sum(t['change_1mo'] for t in tickers_data) / len(tickers_data)

                high_correlation_groups.append({
                    'sector': sector,
                    'tickers': [t['ticker'] for t in tickers_data],
                    'count': len(tickers_data),
                    'allocation_pct': sector_pct,
                    'correlation': correlation_estimate,
                    'avg_momentum': avg_momentum,
                    'value': sector_value
                })

        # Calculer score de diversification (0-100)
        # Score élevé = bien diversifié, score bas = trop concentré/corrélé
        diversification_score = 100

        # Pénalité pour surconcentration sectorielle
        for group in high_correlation_groups:
            if group['allocation_pct'] > 40:
                diversification_score -= 20
            elif group['allocation_pct'] > 30:
                diversification_score -= 10

        # Pénalité pour trop peu de secteurs
        num_sectors = len(by_sector)
        if num_sectors == 1:
            diversification_score -= 30
        elif num_sectors == 2:
            diversification_score -= 15

        diversification_score = max(0, min(100, diversification_score))

        # Calculer risque estimé en cas de crash sectoriel
        worst_case_impact = {}
        for group in high_correlation_groups:
            # Si secteur chute de -20%, impact sur portfolio
            sector_impact = group['allocation_pct'] * 0.20  # 20% de la valeur du secteur
            worst_case_impact[group['sector']] = sector_impact

        return {
            'high_correlation_groups': high_correlation_groups,
            'diversification_score': diversification_score,
            'num_sectors': num_sectors,
            'worst_case_impacts': worst_case_impact
        }

    correlation_risk = calculate_correlation_risk(positions, all_analyses)

    # AMELIORATION #3: Afficher le risque de corrélation
    if correlation_risk:
        score = correlation_risk['diversification_score']
        num_sectors = correlation_risk['num_sectors']

        # Déterminer le niveau de risque
        if score >= 70:
            risk_level = "✅ BON"
            risk_emoji = "🟢"
        elif score >= 50:
            risk_level = "⚠️ MOYEN"
            risk_emoji = "🟡"
        else:
            risk_level = "🚨 ELEVÉ"
            risk_emoji = "🔴"

        prompt += f"""
### RISQUE DE CORRELATION (CRITIQUE pour diversification réelle)
- **Score de diversification**: {score}/100 {risk_emoji} ({risk_level})
- **Nombre de secteurs**: {num_sectors}

"""

        # Afficher les groupes fortement corrélés
        high_corr = correlation_risk['high_correlation_groups']
        if high_corr:
            prompt += "**GROUPES FORTEMENT CORRELES** (positions du même secteur = corrélation ~75-95%):\n"
            for group in high_corr:
                if group['count'] >= 2:
                    tickers_str = ', '.join(group['tickers'])
                    impact = correlation_risk['worst_case_impacts'].get(group['sector'], 0)

                    # Emoji selon allocation
                    if group['allocation_pct'] > 50:
                        alloc_emoji = "🚨"
                    elif group['allocation_pct'] > 35:
                        alloc_emoji = "⚠️"
                    else:
                        alloc_emoji = "📊"

                    prompt += f"""
{alloc_emoji} **{group['sector']}**: {group['count']} positions ({tickers_str})
   - Allocation: {group['allocation_pct']:.1f}% du portfolio
   - Corrélation estimée: {group['correlation']:.2f}
   - Momentum moyen: {group['avg_momentum']:+.1f}%
   - ⚠️ Impact si crash secteur -20%: -{impact:.1f}% du portfolio total
"""

        # Recommandations basées sur le score
        prompt += "\n**IMPLICATIONS POUR DIVERSIFICATION**:\n"
        if score < 50:
            prompt += "🚨 DIVERSIFICATION INSUFFISANTE: Portfolio très exposé aux risques sectoriels concentrés\n"
            prompt += "   → PRIORITE ABSOLUE: Acheter dans secteurs NON représentés ou sous-représentés (<15%)\n"
            prompt += "   → Éviter tout renforcement dans secteurs >40%\n"
        elif score < 70:
            prompt += "⚠️ DIVERSIFICATION LIMITEE: Amélioration recommandée\n"
            prompt += "   → Privilégier achats dans secteurs <20% allocation\n"
            prompt += "   → Prudence sur renforcement secteurs >35%\n"
        else:
            prompt += "✅ DIVERSIFICATION CORRECTE: Maintenir l'équilibre sectoriel\n"
            prompt += "   → OK pour renforcer secteurs performants si <40% allocation\n"

        prompt += "\n"

    # AMELIORATION #2: Ajouter le contexte macro
    if macro_context:
        prompt += f"""
### CONTEXTE MARCHE GLOBAL (CRITIQUE pour strategie)
- **Tendance moyenne 1j**: {macro_context['avg_change_1d']:+.2f}% (sur {macro_context['total_analyzed']} tickers)
- **Volatilité**: {macro_context['volatility']:.2f}% ({macro_context['vol_level']})
- **Sentiment marché**: {macro_context['mood']}
  - Signaux bullish: {macro_context['bullish_pct']:.0f}%
  - Signaux bearish: {macro_context['bearish_pct']:.0f}%

STRATEGIE ADAPTEE AU CONTEXTE:
"""
        # Stratégie selon contexte
        if macro_context['mood'] == 'BULL' and macro_context['vol_level'] == 'FAIBLE':
            prompt += "✅ **ENVIRONNEMENT FAVORABLE** (Bull + faible volatilité)\n"
            prompt += "   → Stratégie AGGRESSIVE: Renforcer positions gagnantes, OK pour concentration modérée\n"
            prompt += "   → Stop-loss: Standards (6-8%)\n"
        elif macro_context['mood'] == 'BULL' and macro_context['vol_level'] in ['MODEREE', 'HAUTE']:
            prompt += "⚠️ **BULL MARKET VOLATIL** (Haussier mais instable)\n"
            prompt += "   → Stratégie EQUILIBREE: Profiter momentum MAIS prudence sur tailles positions\n"
            prompt += "   → Stop-loss: Légèrement serrés (5-7%)\n"
        elif macro_context['mood'] == 'BEAR':
            prompt += "🚨 **ENVIRONNEMENT DEFENSIF** (Bear market)\n"
            prompt += "   → Stratégie CONSERVATIVE: Préserver capital, diversification stricte\n"
            prompt += "   → Stop-loss: Très serrés (4-6%)\n"
            prompt += "   → Privilégier qualité et secteurs défensifs\n"
        else:  # NEUTRE
            prompt += "📊 **MARCHE MIXTE** (Sentiment neutre)\n"
            prompt += "   → Stratégie SELECTIVE: Suivre momentum sectoriel, éviter paris hasardeux\n"
            prompt += "   → Stop-loss: Standards (6-8%)\n"

        prompt += "\n"

    # AMELIORATION #1: Ajouter l'historique des recommandations
    if previous_analysis:
        prev_date = previous_analysis.get('created_at', previous_analysis.get('date', ''))
        if isinstance(prev_date, str):
            prev_date_str = prev_date[:10] if len(prev_date) >= 10 else prev_date
        else:
            prev_date_str = str(prev_date)[:10]

        prev_achats = previous_analysis.get('achats_recommandes', [])
        prev_ventes = previous_analysis.get('ventes_recommandees', [])

        if prev_achats or prev_ventes:
            prompt += f"""
### RECOMMANDATIONS PRECEDENTES ({prev_date_str}) - COHERENCE TEMPORELLE OBLIGATOIRE

"""
            if prev_achats:
                achats_tickers = [a.get('ticker', 'N/A') for a in prev_achats if isinstance(a, dict)]
                prompt += f"**Achats suggérés précédemment**: {', '.join(achats_tickers)}\n"

            if prev_ventes:
                ventes_tickers = [v.get('ticker', 'N/A') for v in prev_ventes if isinstance(v, dict)]
                prompt += f"**Ventes suggérées précédemment**: {', '.join(ventes_tickers)}\n"

            prompt += f"""
⚠️ REGLES DE COHERENCE TEMPORELLE (CRITIQUES):
1. Si tu as recommandé d'ACHETER un ticker il y a <7 jours, ne recommande PAS de le VENDRE maintenant
   SAUF si changement MAJEUR (cassure SL, news très négatives, momentum inversé)
2. Si conditions fondamentales N'ONT PAS CHANGE, MAINTIENS tes recommandations
3. Pour tout CHANGEMENT de position vs analyse précédente, EXPLIQUE CLAIREMENT pourquoi:
   - Exemple: "Précédemment suggéré d'acheter NVDA, mais momentum a faibli (-5% cette semaine) → Passer à CONSERVER"
4. FAVORISE la COHERENCE: Si tu as dit "acheter" et le ticker n'a pas bougé, ne change pas d'avis sans raison
5. Évite les FLIP-FLOPS (acheter puis vendre puis acheter): Montre de la CONVICTION

"""

    if positions:
        prompt += "\n### Positions detaillees\n"
        for i, pos in enumerate(positions, 1):
            ticker = pos.get('ticker', 'N/A')
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', entry_price)
            quantity = pos.get('quantity', 1)
            pnl_value = pos.get('pnl_value', 0)
            pnl_percent = pos.get('pnl_percent', 0)
            stop_loss = pos.get('stop_loss')
            take_profit_1 = pos.get('take_profit_1')
            entry_date = pos.get('entry_date', '')

            analysis = all_analyses.get(ticker, {})
            signal = analysis.get('signal', 'N/A')
            confidence = analysis.get('confidence', 'N/A')
            summary = (analysis.get('summary', '') or '')[:150]
            indicators = analysis.get('indicators', {})
            rsi = indicators.get('rsi', 'N/A')
            macd_hist = indicators.get('macd_histogram', 'N/A')

            prompt += f"""
{i}. **{ticker}** | Entree: {entry_price:.2f}$ ({entry_date[:10] if entry_date else '?'}) | Actuel: {current_price:.2f}$ | Qte: {quantity}
   P&L: {pnl_value:+.2f}$ ({pnl_percent:+.2f}%) | SL: {f'{stop_loss:.2f}$' if stop_loss else '-'} | TP: {f'{take_profit_1:.2f}$' if take_profit_1 else '-'}
   Signal: {signal} ({confidence}) | RSI: {rsi} | MACD: {macd_hist}
   {summary}
"""
    else:
        prompt += "\nAucune position ouverte - recommande des achats initiaux.\n"

    # Non-owned tickers
    non_owned = {t: a for t, a in all_analyses.items() if t not in owned_tickers}
    if non_owned:
        prompt += f"\n## ACTIONS SURVEILLEES NON DETENUES ({len(non_owned)} tickers)\n"
        for ticker, analysis in sorted(non_owned.items()):
            signal = analysis.get('signal', 'N/A')
            confidence = analysis.get('confidence', 'N/A')
            price = analysis.get('price', 0) or 0
            change_1d = analysis.get('change_1d', 0) or 0
            sector = analysis.get('sector', 'N/A')
            indicators = analysis.get('indicators', {})
            rsi = indicators.get('rsi', 'N/A')
            summary = (analysis.get('summary', '') or '')[:100]
            prompt += f"- **{ticker}** [{sector}]: {signal} ({confidence}) | {price:.2f}$ | 1j: {change_1d:+.2f}% | RSI: {rsi} | {summary}\n"

    # News summaries
    if news_summaries:
        prompt += "\n## ACTUALITES DU JOUR\n"
        for category, data in news_summaries.items():
            if category == 'market_daily_summary':
                continue
            summary_text = data.get('summary', '') if isinstance(data, dict) else str(data)
            if summary_text:
                prompt += f"### {category}\n{summary_text[:400]}\n\n"

    prompt += f"""
---

## FORMAT DE REPONSE - JSON OBLIGATOIRE

Reponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou apres, sans balises markdown.

{{
  "date": "{datetime.now().strftime('%Y-%m-%d')}",
  "resume_global": {{
    "etat_portfolio": "Sain | Attention | Critique",
    "tendance": "Haussiere | Baissiere | Mixte",
    "score_sante": 75,
    "resume": "2-3 phrases courtes sur l'etat actuel du portefeuille, performance globale, et orientation strategique recommandee."
  }},
  "plan_action": [
    {{
      "action": "VENDRE",
      "tickers": ["GCTS"],
      "stop_loss": 0.95,
      "take_profit": null,
      "nombre_actions": null,
      "raison": "Stop-loss proche, liberer du capital"
    }},
    {{
      "action": "ACHETER",
      "tickers": ["NOC"],
      "stop_loss": 645.00,
      "take_profit": 780.00,
      "nombre_actions": 5,
      "raison": "Defense premium, momentum haussier"
    }},
    {{
      "action": "CONSERVER",
      "tickers": ["LMT", "NVDA", "GOOG"],
      "stop_loss": null,
      "take_profit": null,
      "nombre_actions": null,
      "raison": "Momentum intact, positions solides"
    }}
  ],
  "achats_recommandes": [
    {{
      "ticker": "NVDA",
      "raison": "1 phrase: pourquoi acheter maintenant",
      "nombre_actions": 15,
      "prix_entree": 130.50,
      "stop_loss": 122.00,
      "objectif": 145.00,
      "conviction": "Forte | Moyenne"
    }}
  ],
  "ventes_recommandees": [
    {{
      "ticker": "GCTS",
      "raison": "1 phrase: pourquoi vendre",
      "prix_actuel": 1.16,
      "stop_loss": 0.95,
      "urgence": "Immediate | Cette semaine | Surveiller"
    }}
  ],
  "conseils_positions": [
    {{
      "ticker": "AAPL",
      "action": "CONSERVER | RENFORCER | ALLEGER | VENDRE | SURVEILLER",
      "urgence": "Haute | Moyenne | Faible",
      "conseil": "Conseil actionnable court",
      "niveau_cle": "Prix important",
      "raison": "Justification technique courte"
    }}
  ],
  "projections": {{
    "expected_pnl_1w": 2.5,
    "expected_pnl_1m": 8.0,
    "expected_pnl_1y": 25.0,
    "confidence_level": "Moyenne",
    "commentary": "Base des projections en 1-2 phrases"
  }},
  "risques_portfolio": {{
    "risque_principal": "Risque majeur identifie en 1 phrase"
  }}
}}

REGLES CRITIQUES:
- Retourne UNIQUEMENT le JSON valide et COMPLET
- resume_global.resume: 2-3 phrases courtes sur l'etat du portefeuille, performance globale, et orientation strategique. OBLIGATOIRE.
- plan_action: 3-7 etapes CONCRETES en objets structures, dans l'ORDRE DE PRIORITE. C'est la PARTIE LA PLUS IMPORTANTE - l'investisseur suivra ces etapes dans l'ordre.
  * Chaque objet doit contenir:
    - action: "VENDRE" | "ACHETER" | "ALLEGER" | "SURVEILLER" | "CONSERVER" | "RENFORCER"
    - tickers: array de tickers concernes (ex: ["AAPL"] ou ["NVDA", "GOOG"])
    - stop_loss: prix du stop-loss (ou null si non applicable)
    - take_profit: prix de l'objectif (ou null si non applicable)
    - nombre_actions: nombre d'actions pour ACHETER/VENDRE (ou null si non applicable)
    - raison: phrase courte expliquant pourquoi (max 15 mots)
- achats_recommandes: SEULEMENT des achats haute conviction, budget total <= {budget} {budget_currency}. Pour chaque achat, calculer le NOMBRE D'ACTIONS recommande (nombre_actions) base sur le budget disponible et le prix d'entree.
- ventes_recommandees: positions a liquider ou alleger avec urgence et raison
- Chaque achat DOIT avoir un stop_loss (proteger le capital)
- Considere les commissions ({commission_text}) dans la rentabilite{f" - Round-trip total: {total_roundtrip_pct:.2f}%. Objectif minimum: +{total_roundtrip_pct*2:.1f}% pour etre profitable" if total_roundtrip_pct > 0 else ""}
- Ne recommande PAS d'acheter un ticker deja en portefeuille (utilise RENFORCER dans conseils_positions)
- projections: % attendus si on suit tes recommandations (1 semaine, 1 mois, 1 an)
- Priorise le momentum recent et les catalyseurs news
- Sois DIRECT et CONCIS - pas de disclaimers, pas de langage vague

REGLES DE DIVERSIFICATION INTELLIGENTES (basées sur PERFORMANCE + MOMENTUM):

PHILOSOPHIE: Momentum + Performance > Allocation brute
- Secteur performant avec momentum fort = OK pour concentration moderee
- Secteur faible meme sous-represente = Ne pas renforcer par principe

NIVEAUX DE RISQUE:

🟢 NIVEAU 1 - Secteur <40%:
- AUTORISE: Renforcer si momentum >+8% (1mo) ET signaux bullish >50%
- Exemple: Tech 35% avec +15% momentum → ✅ OK pour acheter
- Limite: Ne pas depasser 50% meme si momentum excellent

🟡 NIVEAU 2 - Secteur 40-60%:
- PRUDENCE: Renforcer SEULEMENT si momentum TRES fort (>+12%) ET tous signaux bullish
- RECOMMANDE: Prises de profits partielles sur positions tres gagnantes
- ALTERNATIVE: Proposer des secteurs sous-représentés avec bon momentum

🔴 NIVEAU 3 - Secteur >60%:
- ALERTE: Recommander diversification SAUF si bull run exceptionnel (>+20% momentum)
- DANS TOUS LES CAS: Stop-loss serres + ne pas renforcer
- Si momentum faiblit (<+5%): VENDRE ou ALLEGER prioritaire

OPPORTUNITES:
- Secteurs <15% avec momentum >+5% = CIBLES PRIORITAIRES pour diversifier
- Chercher des secteurs sous-representes avec signaux ACHETER

COHERENCE OBLIGATOIRE:
- Si tu recommandes "diversifier" → achats dans secteurs DIFFERENTS (<30% allocation)
- Si secteur >50% → TOUJOURS mentionner le risque de concentration
- Justifie CHAQUE achat par le momentum sectoriel, pas juste par le ticker
"""

    return prompt


def generate_portfolio_analysis(positions, all_analyses, news_summaries=None, config=None, model=None, num_threads=12):
    """
    Genere l'analyse du portefeuille via Claude API.

    Args:
        positions: Liste des positions ouvertes
        all_analyses: Dict des dernières analyses par ticker (tous les tickers)
        news_summaries: Dict des résumés de news
        config: Configuration avec budget, risk, objective
        model: Modèle (ignoré, utilise config Claude)
        num_threads: Ignoré (compatibilité)

    Returns:
        tuple: (analyse_json, temps_écoulé) ou (None, 0) en cas d'erreur
    """
    from config import CLAUDE_CONFIG

    n_positions = len(positions) if positions else 0
    n_analyses = len(all_analyses) if all_analyses else 0

    print(f"🤖 Analyse portfolio Sonnet ({n_positions} positions, {n_analyses} tickers surveilles)...")

    prompt = build_portfolio_analysis_prompt(positions, all_analyses, news_summaries, config)
    portfolio_config = CLAUDE_CONFIG['portfolio']

    system_prompt = """Tu es un conseiller financier expert avec 20 ans d'experience en gestion de portefeuille.

L'investisseur suivra tes recommandations directement. Ta priorite: MAXIMISER LE RENDEMENT tout en gerant le risque.

METHODOLOGIE D'ANALYSE (dans cet ordre):
1. Analyser l'allocation sectorielle + MOMENTUM de chaque secteur
2. Identifier les secteurs FORTS (momentum >+8%, signaux bullish) vs FAIBLES
3. Evaluer risque de concentration vs opportunite de momentum
4. Prioriser: Secteurs performants sous-representes (<30%) = MEILLEURE OPPORTUNITE
5. COHERENCE: Si tu dis "diversifier", achete dans secteurs DIFFERENTS et performants

PHILOSOPHIE GAGNANTE:
- Momentum + Performance > Diversification aveugle
- OK pour concentration jusqu'a 50% dans secteur TRES fort (momentum >+12%)
- Mais si secteur >60% → TOUJOURS recommander prudence meme si forte performance
- Secteurs faibles: ALLEGER meme si <30% allocation

Tu utilises (par priorité):
1. Momentum sectoriel (variation 1 mois, signaux bullish)
2. Analyse technique (RSI, MACD, supports/resistances, volumes)
3. Catalyseurs news et fondamentaux
4. Gestion du risque adaptative (stop-loss serres si concentration >50%)

REGLES ABSOLUES:
- Temperature mentale = 0 (decisions reproductibles basees sur donnees)
- COHERENCE totale: allocation + momentum → recommendations alignees
- Justifie CHAQUE achat par momentum sectoriel + signal ticker
- Si secteur >60%: TOUJOURS mentionner risque concentration
- Stop-loss OBLIGATOIRE sur tous achats

Tu reponds UNIQUEMENT en JSON valide, sans texte avant ou apres, sans balises markdown.
Tu es OPPORTUNISTE (profiter momentum fort) mais PRUDENT (limiter risque concentration).
Direct, methodique, base sur donnees. Pas de disclaimers vagues."""

    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config['max_tokens'],
            temperature=0.1,  # Très bas pour cohérence et répétabilité
            system_prompt=system_prompt,
            timeout=120
        )

        # Clean markdown
        clean = response.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean = '\n'.join(lines)

        # Parse JSON
        try:
            analysis_json = json.loads(clean)
            print(f"✅ Portfolio analyse ({elapsed:.1f}s)")
            return analysis_json, elapsed
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur JSON: {e}")
            print(f"   Reponse: {clean[:200]}...")
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, 0


def build_market_summary_prompt(analyses_results):
    """
    Build simplified prompt for sector trends summary.

    Args:
        analyses_results: List of analysis result dicts from analyze_stock()

    Returns:
        str: Prompt for Claude
    """
    # Group by sector
    by_sector = {}
    for a in analyses_results:
        sector = a.get('sector', 'N/A')
        if sector not in by_sector:
            by_sector[sector] = []
        by_sector[sector].append(a)

    prompt = f"""# TENDANCES SECTORIELLES - {datetime.now().strftime('%Y-%m-%d')}

## INSTRUCTIONS
Analyse les tendances par secteur. Pour chaque secteur, determine simplement la tendance globale.

## ANALYSES PAR SECTEUR
"""

    for sector, analyses in by_sector.items():
        prompt += f"\n### {sector}\n"
        for a in analyses:
            signal = a.get('signal', 'N/A')
            change_1d = a.get('change_1d', 0) or 0
            prompt += f"- {a['ticker']}: {signal} | Var 1j: {change_1d:+.2f}%\n"

    prompt += """
---

## FORMAT DE REPONSE - JSON OBLIGATOIRE

Reponds UNIQUEMENT avec un objet JSON valide:

{
  "date": "YYYY-MM-DD",
  "sector_trends": [
    {"sector": "Technology", "trend": "Haussier | Baissier | Neutre"}
  ]
}

REGLES:
- trend doit etre exactement "Haussier", "Baissier" ou "Neutre"
- Base ta decision sur les signaux et variations des actions du secteur
- Pas de texte supplementaire, juste le JSON
"""
    return prompt


def generate_market_summary(analyses_results):
    """
    Generate simplified sector trends summary using Claude.

    Args:
        analyses_results: List of successful analysis result dicts

    Returns:
        tuple: (summary_dict, elapsed_time) or (None, 0)
    """
    from config import CLAUDE_CONFIG

    if not analyses_results:
        return None, 0

    print(f"📋 Generation des tendances sectorielles ({len(analyses_results)} analyses)...")

    prompt = build_market_summary_prompt(analyses_results)

    portfolio_config = CLAUDE_CONFIG.get('portfolio', CLAUDE_CONFIG.get('deep_analysis'))

    system_prompt = """Tu es un analyste de marche.
Tu determines les tendances sectorielles (Haussier/Baissier/Neutre) basees sur les signaux.
Tu reponds UNIQUEMENT en JSON valide, sans texte avant ou apres, sans balises markdown."""

    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=512,  # Reduced since we only need sector trends
            temperature=0.2,
            system_prompt=system_prompt,
            timeout=60
        )

        # Clean markdown wrappers
        clean = response.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean = '\n'.join(lines)

        try:
            summary_json = json.loads(clean)
            print(f"✅ Tendances sectorielles generees ({elapsed:.1f}s)")
            return summary_json, elapsed
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur JSON tendances sectorielles: {e}")
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed
    except Exception as e:
        print(f"❌ Erreur generation tendances sectorielles: {e}")
        return None, 0
