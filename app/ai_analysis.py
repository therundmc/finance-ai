"""Module d'analyse IA - Version Claude API (remplace Ollama)"""
import time
import json
import requests
import os
from datetime import datetime

# Configuration API Claude
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_claude_api(prompt, model, max_tokens=256, temperature=0.2, system_prompt=None):
    """
    Appelle l'API Claude (remplace ollama.chat)
    
    Returns:
        tuple: (response_text, elapsed_time)
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("❌ ANTHROPIC_API_KEY manquante dans l'environnement (.env)")
    
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
        "messages": [
            {"role": "user", "content": prompt}
        ]
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
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API Claude: {e}")
        return "", 0


# JSON Schema pour la réponse structurée (gardé identique)
ANALYSIS_JSON_SCHEMA = {
    "signal": "ACHETER | VENDRE | CONSERVER",
    "conviction": "Forte | Moyenne | Faible",
    "resume": "Une phrase de synthèse",
    "analyse_technique": {
        "tendance": "Haussière | Baissière | Neutre",
        "rsi_interpretation": "description",
        "macd_interpretation": "description",
        "volatilite": "description"
    },
    "analyse_fondamentale": {
        "valorisation": "description",
        "points_forts": ["liste"],
        "points_faibles": ["liste"]
    },
    "catalyseurs": [{"type": "positif|négatif", "description": "texte"}],
    "risques": ["liste des risques"],
    "niveaux": {
        "achat_recommande": 0.0,
        "stop_loss": 0.0,
        "objectif_1": 0.0,
        "objectif_2": 0.0
    },
    "conclusion": "Synthèse finale"
}


def build_analysis_prompt(ticker, hist_1mo, info, indicators, advanced=False, 
                          news=None, calendar=None, recommendations=None):
    """
    Construit un prompt structuré pour l'analyse (IDENTIQUE à l'original)
    """
    
    # === DONNÉES DE BASE ===
    current_price = hist_1mo['Close'].iloc[-1] if not hist_1mo.empty else 0
    open_price = hist_1mo['Open'].iloc[-1] if not hist_1mo.empty else 0
    high_price = hist_1mo['High'].iloc[-1] if not hist_1mo.empty else 0
    low_price = hist_1mo['Low'].iloc[-1] if not hist_1mo.empty else 0
    volume = hist_1mo['Volume'].iloc[-1] if not hist_1mo.empty else 0
    
    # Variation sur le mois
    if len(hist_1mo) >= 2:
        monthly_change = ((current_price - hist_1mo['Close'].iloc[0]) / 
                          hist_1mo['Close'].iloc[0] * 100)
    else:
        monthly_change = 0
    
    # === INFORMATIONS ENTREPRISE ===
    company_name = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 'N/A')
    forward_pe = info.get('forwardPE', 'N/A')
    peg_ratio = info.get('pegRatio', 'N/A')
    dividend_yield = info.get('dividendYield', 0)
    beta = info.get('beta', 'N/A')
    target_price = info.get('targetMeanPrice', 'N/A')
    recommendation = info.get('recommendationKey', 'N/A')
    
    # Formatage market cap
    if market_cap and market_cap > 0:
        if market_cap >= 1e12:
            market_cap_str = f"{market_cap/1e12:.2f}T$"
        elif market_cap >= 1e9:
            market_cap_str = f"{market_cap/1e9:.2f}B$"
        else:
            market_cap_str = f"{market_cap/1e6:.2f}M$"
    else:
        market_cap_str = "N/A"
    
    # === CONSTRUCTION DU PROMPT ===
    prompt = f"""# ANALYSE FINANCIÈRE PROFESSIONNELLE - {ticker}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## INSTRUCTIONS
Tu es un analyste financier senior. Analyse les données suivantes et fournis une recommandation claire et actionnable.

**FORMAT DE RÉPONSE OBLIGATOIRE:**
1. Commence TOUJOURS par une ligne: `SIGNAL: [ACHETER/VENDRE/CONSERVER]`
2. Puis une ligne: `CONVICTION: [Forte/Moyenne/Faible]`
3. Puis une ligne: `RÉSUMÉ: [Une phrase de synthèse]`
4. Ensuite ton analyse détaillée

---

## 1. PROFIL DE L'ENTREPRISE
- **Nom:** {company_name}
- **Secteur:** {sector}
- **Industrie:** {industry}
- **Capitalisation:** {market_cap_str}
- **Beta:** {beta}

## 2. DONNÉES DE PRIX (Dernière séance)
- **Prix actuel:** {current_price:.2f}$
- **Ouverture:** {open_price:.2f}$
- **Plus haut:** {high_price:.2f}$
- **Plus bas:** {low_price:.2f}$
- **Volume:** {volume:,.0f}
- **Variation mensuelle:** {monthly_change:+.2f}%

## 3. VALORISATION
- **P/E (TTM):** {pe_ratio}
- **P/E Forward:** {forward_pe}
- **PEG Ratio:** {peg_ratio}
- **Rendement dividende:** {f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A"}
- **Objectif analystes:** {f"{target_price:.2f}$" if isinstance(target_price, (int, float)) else target_price}
- **Consensus:** {recommendation}

## 4. INDICATEURS TECHNIQUES
"""
    
    # === INDICATEURS TECHNIQUES ===
    if indicators:
        rsi = indicators.get('rsi')
        if rsi is not None:
            rsi_signal = "SURACHETÉ ⚠️" if rsi > 70 else "SURVENDU ⚠️" if rsi < 30 else "Neutre"
            prompt += f"- **RSI (14):** {rsi:.1f} → {rsi_signal}\n"
        
        ma_20 = indicators.get('ma_20')
        ma_50 = indicators.get('ma_50')
        ma_200 = indicators.get('ma_200')
        
        if ma_20:
            ma20_pos = "AU-DESSUS ✅" if current_price > ma_20 else "EN-DESSOUS ❌"
            prompt += f"- **MA20:** {ma_20:.2f}$ (Prix {ma20_pos})\n"
        if ma_50:
            ma50_pos = "AU-DESSUS ✅" if current_price > ma_50 else "EN-DESSOUS ❌"
            prompt += f"- **MA50:** {ma_50:.2f}$ (Prix {ma50_pos})\n"
        if ma_200:
            ma200_pos = "AU-DESSUS ✅" if current_price > ma_200 else "EN-DESSOUS ❌"
            prompt += f"- **MA200:** {ma_200:.2f}$ (Prix {ma200_pos})\n"
        
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd is not None and macd_signal is not None:
            macd_trend = "HAUSSIER ✅" if macd > macd_signal else "BAISSIER ❌"
            prompt += f"- **MACD:** {macd:.3f} | Signal: {macd_signal:.3f} → {macd_trend}\n"
        
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        bb_position = indicators.get('bb_position')
        if bb_upper and bb_lower:
            prompt += f"- **Bollinger:** [{bb_lower:.2f}$ - {bb_upper:.2f}$]\n"
            if bb_position is not None:
                bb_zone = "HAUT (Surachat)" if bb_position > 80 else "BAS (Survente)" if bb_position < 20 else "Médian"
                prompt += f"- **Position Bollinger:** {bb_position:.1f}% → {bb_zone}\n"
        
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        if stoch_k is not None:
            stoch_signal = "SURVENDU ⚠️" if stoch_k < 20 else "SURACHETÉ ⚠️" if stoch_k > 80 else "Neutre"
            prompt += f"- **Stochastique K:** {stoch_k:.1f} → {stoch_signal}\n"
        
        atr = indicators.get('atr')
        atr_pct = indicators.get('atr_percent')
        if atr and atr_pct:
            prompt += f"- **ATR:** {atr:.2f} ({atr_pct:.2f}% du prix) - Volatilité\n"
    
    # === DONNÉES ENRICHIES (si mode avancé) ===
    if advanced and news:
        prompt += f"\n## 5. ACTUALITÉS RÉCENTES\n"
        for i, article in enumerate(news[:3], 1):
            title = article.get('title', 'N/A')
            pub_date = article.get('providerPublishTime', '')
            prompt += f"{i}. **{title}**\n"
    
    if advanced and calendar:
        prompt += f"\n## 6. CALENDRIER FINANCIER\n"
        earnings = calendar.get('Earnings Date') if isinstance(calendar, dict) else None
        if earnings:
            prompt += f"- **Prochains résultats:** {earnings}\n"
    
    if advanced and recommendations is not None and not recommendations.empty:
        prompt += f"\n## 7. RECOMMANDATIONS ANALYSTES\n"
        recent_recos = recommendations.tail(3)
        for _, reco in recent_recos.iterrows():
            firm = reco.get('Firm', 'N/A')
            action = reco.get('To Grade', reco.get('Action', 'N/A'))
            prompt += f"- **{firm}:** {action}\n"
    
    prompt += """
---

## INSTRUCTIONS FINALES
Fournis une analyse COMPLÈTE et STRUCTURÉE avec:
1. Signal clair (ACHETER/VENDRE/CONSERVER)
2. Conviction (Forte/Moyenne/Faible)
3. Résumé en 1 phrase
4. Analyse technique détaillée
5. Analyse fondamentale
6. Catalyseurs et risques
7. Niveaux d'action recommandés
8. Conclusion synthétique

Sois précis, factuel et actionnable.
"""
    
    return prompt


def generate_analysis(ticker, model, context, num_threads=12):
    """
    Génère l'analyse IA (INTERFACE IDENTIQUE - remplace Ollama par Claude)
    
    Args:
        ticker: Symbole de l'action
        model: Modèle à utiliser (ignoré si Claude, utilise config)
        context: Prompt de contexte
        num_threads: Ignoré (compatibilité Ollama)
    
    Returns:
        tuple: (analysis_text, elapsed_time)
    """
    from config import CLAUDE_CONFIG
    
    print(f"🤖 Claude Sonnet - Analyse de {ticker}...")
    
    # Configuration Sonnet pour analyse complète
    sonnet_config = CLAUDE_CONFIG['deep_analysis']
    
    system_prompt = """Tu es un analyste financier senior avec 15 ans d'expérience.
Tu analyses les actions de manière approfondie en considérant:
- L'analyse technique (tendances, niveaux clés)
- L'analyse fondamentale (valorisation, santé financière)
- Les actualités et catalyseurs
- Les risques identifiables

Commence TOUJOURS ta réponse par:
SIGNAL: [ACHETER/VENDRE/CONSERVER]
CONVICTION: [Forte/Moyenne/Faible]
RÉSUMÉ: [Une phrase claire]

Puis fournis ton analyse détaillée."""
    
    try:
        analysis_text, elapsed_time = call_claude_api(
            prompt=context,
            model=sonnet_config['model'],
            max_tokens=sonnet_config['max_tokens'],
            temperature=sonnet_config['temperature'],
            system_prompt=system_prompt
        )
        
        if analysis_text:
            print(f"✅ Analyse générée en {elapsed_time:.1f}s")
            return analysis_text, elapsed_time
        else:
            print(f"❌ Échec génération analyse")
            return None, 0
            
    except Exception as e:
        print(f"❌ Erreur Claude API: {e}")
        return None, 0


def build_portfolio_analysis_prompt(positions, latest_analyses):
    """
    Construit le prompt pour l'analyse globale du portefeuille (IDENTIQUE)
    """
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
        
        analysis = latest_analyses.get(ticker, {})
        signal = analysis.get('signal', 'N/A')
        confidence = analysis.get('confidence', 'N/A')
        
        prompt += f"""
### {i}. {ticker}
- **Entrée:** {entry_price:.2f}$
- **Prix actuel:** {current_price:.2f}$
- **Quantité:** {quantity}
- **P&L:** {pnl_value:+.2f}$ ({pnl_percent:+.2f}%)
- **Signal AI récent:** {signal} (Conviction: {confidence})
"""

    prompt += """
---

## FORMAT DE RÉPONSE - JSON OBLIGATOIRE

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.

```json
{
  "date": "YYYY-MM-DD",
  "resume_global": {
    "etat_portfolio": "Sain | Attention | Critique",
    "tendance": "Haussière | Baissière | Mixte",
    "synthese": "Description état global",
    "score_sante": 75
  },
  "actions_du_jour": {
    "priorite_haute": ["Action 1", "Action 2"],
    "a_surveiller": ["Point 1", "Point 2"]
  },
  "conseils_positions": [
    {
      "ticker": "XXX",
      "action": "CONSERVER | RENFORCER | ALLEGER | VENDRE",
      "urgence": "Haute | Moyenne | Faible",
      "conseil": "Conseil actionnable",
      "raison": "Justification"
    }
  ],
  "conclusion": "Synthèse finale"
}
```
"""
    
    return prompt


def generate_portfolio_analysis(positions, latest_analyses, model, num_threads=12):
    """
    Génère l'analyse du portefeuille (INTERFACE IDENTIQUE - Claude au lieu d'Ollama)
    
    Returns:
        tuple: (analyse_json, temps_écoulé)
    """
    from config import CLAUDE_CONFIG
    
    if not positions:
        print("⚠️ Aucune position ouverte à analyser")
        return None, 0
    
    print(f"🤖 Claude Sonnet - Analyse du portefeuille ({len(positions)} positions)...")
    
    prompt = build_portfolio_analysis_prompt(positions, latest_analyses)
    
    portfolio_config = CLAUDE_CONFIG['portfolio']
    
    system_prompt = """Tu es un gestionnaire de portefeuille expérimenté.
Tu analyses les positions d'un investisseur et fournis des conseils actionnables.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""
    
    try:
        response, elapsed_time = call_claude_api(
            prompt=prompt,
            model=portfolio_config['model'],
            max_tokens=portfolio_config['max_tokens'],
            temperature=portfolio_config['temperature'],
            system_prompt=system_prompt
        )
        
        # Nettoyer les backticks markdown
        clean_response = response.strip()
        if clean_response.startswith('```'):
            lines = clean_response.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean_response = '\n'.join(lines)
        
        # Parser JSON
        try:
            analysis_json = json.loads(clean_response)
            print(f"✅ Analyse portefeuille générée en {elapsed_time:.1f}s")
            return analysis_json, elapsed_time
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur parsing JSON: {e}")
            return {'raw_response': response, 'error': 'JSON parse failed'}, elapsed_time
            
    except Exception as e:
        print(f"❌ Erreur analyse portefeuille: {e}")
        return None, 0
