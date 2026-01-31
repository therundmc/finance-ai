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
    Appelle l'API Claude avec fallback vers Ollama local
    
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
    
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        elapsed_time = time.time() - start_time
        text = result["content"][0]["text"] if "content" in result else ""
        return text, elapsed_time
    except requests.exceptions.HTTPError as e:
        # Erreur HTTP - tenter fallback Ollama
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

def build_portfolio_analysis_prompt(positions, latest_analyses):
    """
    Construit le prompt pour l'analyse globale du portefeuille.
    
    Args:
        positions: Liste des positions ouvertes avec leurs données
        latest_analyses: Dict des dernières analyses par ticker
    
    Returns:
        str: Prompt formaté pour l'analyse IA du portefeuille
    """
    from datetime import datetime
    
    total_invested = sum(p.get('entry_price', 0) * p.get('quantity', 1) for p in positions)
    total_value = sum(p.get('current_price', p.get('entry_price', 0)) * p.get('quantity', 1) for p in positions)
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    prompt = f"""# ANALYSE DE PORTEFEUILLE - CONSEILS DU JOUR
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## INSTRUCTIONS
Tu es un gestionnaire de portefeuille senior. Analyse mon portefeuille actuel et fournis:
1. Un résumé global de la situation
2. Des conseils actionnables pour aujourd'hui
3. Un avis position par position

## APERÇU DU PORTEFEUILLE
- **Capital investi:** {total_invested:,.2f}$
- **Valeur actuelle:** {total_value:,.2f}$
- **P&L Total:** {total_pnl:+,.2f}$ ({total_pnl_percent:+.2f}%)
- **Nombre de positions:** {len(positions)}

## MES POSITIONS ACTUELLES
"""

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
        
        # Récupérer l'analyse récente si disponible
        analysis = latest_analyses.get(ticker, {})
        signal = analysis.get('signal', 'N/A')
        confidence = analysis.get('confidence', 'N/A')
        summary = analysis.get('summary', '')[:200] if analysis.get('summary') else ''
        
        # Indicateurs
        indicators = analysis.get('indicators', {})
        rsi = indicators.get('rsi', 'N/A')
        macd_hist = indicators.get('macd_histogram', 'N/A')
        
        prompt += f"""
### {i}. {ticker}
- **Entrée:** {entry_price:.2f}$ le {entry_date[:10] if entry_date else 'N/A'}
- **Prix actuel:** {current_price:.2f}$
- **Quantité:** {quantity}
- **P&L:** {pnl_value:+.2f}$ ({pnl_percent:+.2f}%)
- **Stop-Loss:** {f'{stop_loss:.2f}$' if stop_loss else 'Non défini'}
- **Take-Profit:** {f'{take_profit_1:.2f}$' if take_profit_1 else 'Non défini'}
- **Signal AI récent:** {signal} (Conviction: {confidence})
- **RSI:** {rsi} | **MACD Hist:** {macd_hist}
- **Analyse récente:** {summary}...
"""

    prompt += f"""
---

## FORMAT DE RÉPONSE - JSON OBLIGATOIRE

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises markdown.
Respecte EXACTEMENT ce schéma:

{{
  "date": "{datetime.now().strftime('%Y-%m-%d')}",
  "resume_global": {{
    "etat_portfolio": "Sain | Attention | Critique",
    "tendance": "Haussière | Baissière | Mixte",
    "synthese": "3-4 phrases décrivant l'état global du portefeuille, les points d'attention majeurs et la direction générale",
    "score_sante": 75
  }},
  "actions_du_jour": {{
    "priorite_haute": ["Action urgente 1", "Action urgente 2"],
    "a_surveiller": ["Point de surveillance 1", "Point de surveillance 2"],
    "opportunites": ["Opportunité détectée si applicable"]
  }},
  "conseils_positions": [
    {{
      "ticker": "AAPL",
      "action": "CONSERVER | RENFORCER | ALLEGER | VENDRE | SURVEILLER",
      "urgence": "Haute | Moyenne | Faible",
      "conseil": "Conseil spécifique et actionnable pour cette position",
      "niveau_cle": "Prix important à surveiller",
      "raison": "Justification basée sur l'analyse technique et fondamentale"
    }}
  ],
  "allocation": {{
    "commentaire": "Commentaire sur la diversification et l'équilibre du portefeuille",
    "suggestion": "Suggestion d'ajustement si nécessaire"
  }},
  "risques_portfolio": {{
    "risque_principal": "Le risque majeur identifié sur l'ensemble du portefeuille",
    "exposition": "Commentaire sur l'exposition sectorielle ou géographique",
    "correlation": "Niveau de corrélation entre les positions"
  }},
  "conclusion": "Synthèse finale: que faire aujourd'hui, quoi surveiller cette semaine"
}}

IMPORTANT:
- Retourne UNIQUEMENT le JSON, pas de texte explicatif
- Un conseil par position dans conseils_positions
- Les conseils doivent être actionnables et précis
- Priorise les actions selon l'urgence
- Assure-toi que le JSON est COMPLET et VALIDE
"""
    
    return prompt


def generate_portfolio_analysis(positions, latest_analyses, model, num_threads=12):
    """
    Génère l'analyse du portefeuille via Claude API (avec fallback Ollama).
    
    Args:
        positions: Liste des positions ouvertes
        latest_analyses: Dict des dernières analyses par ticker
        model: Modèle (ignoré, utilise config Claude)
        num_threads: Ignoré (compatibilité)
    
    Returns:
        tuple: (analyse_json, temps_écoulé) ou (None, 0) en cas d'erreur
    """
    from config import CLAUDE_CONFIG
    
    if not positions:
        print("⚠️ Aucune position ouverte à analyser")
        return None, 0
    
    print(f"🤖 Analyse portfolio Sonnet ({len(positions)} positions)...")
    
    prompt = build_portfolio_analysis_prompt(positions, latest_analyses)
    portfolio_config = CLAUDE_CONFIG['portfolio']
    
    system_prompt = """Tu es un gestionnaire de portefeuille expérimenté avec 20 ans d'expérience.

Tu analyses les positions d'un investisseur et fournis des conseils actionnables.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après, sans balises markdown.
Tu priorises:
- La gestion du risque et préservation du capital
- Des conseils précis et justifiés pour chaque position
- L'identification d'opportunités d'optimisation
- L'analyse de la diversification et corrélation

Tu fournis des analyses DÉTAILLÉES et SUBSTANTIELLES."""
    
    try:
        response, elapsed = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config['max_tokens'],
            temperature=portfolio_config['temperature'],
            system_prompt=system_prompt,
            timeout=120  # Portfolio plus long, 120s au lieu de 60s
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
            print(f"✅ Portfolio analysé ({elapsed:.1f}s)")
            return analysis_json, elapsed
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur JSON: {e}")
            print(f"   Réponse: {clean[:200]}...")
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, 0
