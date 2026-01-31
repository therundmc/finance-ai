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

    config = config or {}
    news_summaries = news_summaries or {}

    # Budget et profil
    budget = config.get('budget', 10000)
    budget_currency = config.get('budget_currency', 'CHF')
    risk_level = config.get('risk_level', 'modere')
    objective = config.get('investment_objective', 'croissance long terme')
    trading = config.get('trading', {})
    buy_commission = trading.get('buy_commission', 10)
    sell_commission = trading.get('sell_commission', 12)
    commission_currency = trading.get('commission_currency', 'CHF')

    # Portfolio totals
    total_invested = sum(p.get('entry_price', 0) * p.get('quantity', 1) for p in positions) if positions else 0
    total_value = sum(p.get('current_price', p.get('entry_price', 0)) * p.get('quantity', 1) for p in positions) if positions else 0
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Owned tickers
    owned_tickers = set(p.get('ticker', '') for p in positions) if positions else set()

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
- **Commissions:** achat {buy_commission} {commission_currency}, vente {sell_commission} {commission_currency}

## PORTEFEUILLE ACTUEL ({len(positions)} positions)
- **Capital investi:** {total_invested:,.2f}$
- **Valeur actuelle:** {total_value:,.2f}$
- **P&L Total:** {total_pnl:+,.2f}$ ({total_pnl_percent:+.2f}%)
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
    "Vendre GCTS immediatement a 1.16$ - stop-loss proche, liberer 580$",
    "Alleger MU de 50% a 101$ - prendre profits +1.15%, liberer 415$",
    "Acheter NOC 5 actions a 692$ avec SL 645$ objectif 780$ - defense premium",
    "Acheter ENOV 100 actions a 22$ avec SL 19.5$ objectif 48.50$ - rebond healthcare",
    "Acheter MA 4 actions a 538$ avec SL 505$ objectif 620$ - paiements survendu",
    "Surveiller TTWO - couper si cassure 210$, sinon conserver pour rebond >225$",
    "Conserver LMT, NVDA, GOOG - momentum intact, ne pas renforcer"
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
- plan_action: 3-7 etapes CONCRETES et dans l'ORDRE DE PRIORITE. Chaque etape commence par un verbe d'action (Vendre, Acheter, Alleger, Surveiller, Conserver). Pour les achats, TOUJOURS indiquer le NOMBRE D'ACTIONS (ex: "Acheter NOC 5 actions a 692$"). Inclure ticker, prix et raison courte. C'est la PARTIE LA PLUS IMPORTANT - l'investisseur suivra ces etapes dans l'ordre.
- achats_recommandes: SEULEMENT des achats haute conviction, budget total <= {budget} {budget_currency}. Pour chaque achat, calculer le NOMBRE D'ACTIONS recommande (nombre_actions) base sur le budget disponible et le prix d'entree.
- ventes_recommandees: positions a liquider ou alleger avec urgence et raison
- Chaque achat DOIT avoir un stop_loss (proteger le capital)
- Considere les commissions ({buy_commission}+{sell_commission} {commission_currency}) dans la rentabilite
- Ne recommande PAS d'acheter un ticker deja en portefeuille (utilise RENFORCER dans conseils_positions)
- projections: % attendus si on suit tes recommandations (1 semaine, 1 mois, 1 an)
- Priorise le momentum recent et les catalyseurs news
- Sois DIRECT et CONCIS - pas de disclaimers, pas de langage vague
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

L'investisseur suivra tes recommandations directement. Ta priorite absolue: maximiser la probabilite de rendement positif.

Tu utilises:
- Analyse technique (RSI, MACD, supports/resistances, volumes, Bollinger Bands)
- Signaux fondamentaux (valorisation, croissance, momentum sectoriel)
- Sentiment des news et catalyseurs recents
- Gestion du risque (stop-loss obligatoire, diversification sectorielle)

Tu reponds UNIQUEMENT en JSON valide, sans texte avant ou apres, sans balises markdown.
Tu recommandes uniquement des achats a haute conviction avec un ratio risque/rendement favorable.
Tu es direct et actionnable. Pas de disclaimers ou de langage vague."""

    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config['max_tokens'],
            temperature=portfolio_config.get('temperature', 0.3),
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
    Build prompt for daily market summary from completed analyses.

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

    prompt = f"""# RESUME QUOTIDIEN DU MARCHE - {datetime.now().strftime('%Y-%m-%d')}

## INSTRUCTIONS
Tu es un stratege de marche senior. A partir des analyses ci-dessous, genere un resume quotidien synthetique:
1. Quelles actions sont les plus attractives a acheter aujourd'hui et pourquoi
2. Quelles actions devraient etre vendues et pourquoi
3. Quels secteurs performent le mieux / le moins bien
4. Vue d'ensemble du marche

## ANALYSES DU JOUR ({len(analyses_results)} actions)
"""

    for sector, analyses in by_sector.items():
        prompt += f"\n### Secteur: {sector}\n"
        for a in analyses:
            signal = a.get('signal', 'N/A')
            confidence = a.get('confidence', 'N/A')
            change_1d = a.get('change_1d', 0) or 0
            price = a.get('price', 0) or 0
            summary = (a.get('summary', '') or '')[:150]
            prompt += f"- **{a['ticker']}**: {signal} ({confidence}) | Prix: {price:.2f} | Var 1j: {change_1d:+.2f}% | {summary}\n"

    prompt += """
---

## FORMAT DE REPONSE - JSON OBLIGATOIRE

Reponds UNIQUEMENT avec un objet JSON valide:

{
  "date": "YYYY-MM-DD",
  "market_mood": "Haussier | Baissier | Mixte | Neutre",
  "summary": "3-4 phrases resumant la journee de marche",
  "top_picks": [
    {"ticker": "AAPL", "action": "ACHETER", "raison": "Pourquoi cette action est attractive"}
  ],
  "sells": [
    {"ticker": "XYZ", "action": "VENDRE", "raison": "Pourquoi vendre"}
  ],
  "sector_performance": [
    {"sector": "Technology", "trend": "Haussier", "comment": "Bref commentaire"}
  ],
  "key_levels": "Niveaux importants a surveiller"
}
"""
    return prompt


def generate_market_summary(analyses_results):
    """
    Generate daily market summary using Claude.

    Args:
        analyses_results: List of successful analysis result dicts

    Returns:
        tuple: (summary_dict, elapsed_time) or (None, 0)
    """
    from config import CLAUDE_CONFIG

    if not analyses_results:
        return None, 0

    print(f"📋 Generation du resume marche ({len(analyses_results)} analyses)...")

    prompt = build_market_summary_prompt(analyses_results)

    portfolio_config = CLAUDE_CONFIG.get('portfolio', CLAUDE_CONFIG.get('deep_analysis'))

    system_prompt = """Tu es un stratege de marche senior.
Tu resumes les analyses du jour et identifies les meilleures opportunites.
Tu reponds UNIQUEMENT en JSON valide, sans texte avant ou apres, sans balises markdown."""

    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config.get('max_tokens', 2048),
            temperature=0.3,
            system_prompt=system_prompt,
            timeout=90
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
            print(f"✅ Resume marche genere ({elapsed:.1f}s)")
            return summary_json, elapsed
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur JSON resume marche: {e}")
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed
    except Exception as e:
        print(f"❌ Erreur generation resume marche: {e}")
        return None, 0
