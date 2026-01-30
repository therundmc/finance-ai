"""Module d'analyse IA amélioré pour l'analyse financière"""
import time
import json
import ollama
from datetime import datetime


# JSON Schema pour la réponse structurée
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
    Construit un prompt structuré et optimisé pour l'analyse financière
    
    Args:
        ticker: Symbole de l'action
        hist_1mo: DataFrame historique 1 mois
        info: Dictionnaire d'informations sur l'action
        indicators: Dictionnaire des indicateurs techniques
        advanced: Mode avancé avec news/calendar
        news: Liste des actualités récentes
        calendar: Calendrier financier
        recommendations: Recommandations des analystes
    
    Returns:
        str: Prompt formaté pour l'IA
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
        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            rsi_signal = "SURACHETÉ ⚠️" if rsi > 70 else "SURVENDU ⚠️" if rsi < 30 else "Neutre"
            prompt += f"- **RSI (14):** {rsi:.1f} → {rsi_signal}\n"
        
        # Moyennes mobiles
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
            prompt += f"- **MA200:** {ma200:.2f}$ (Prix {ma200_pos})\n"
        
        # MACD
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_hist = indicators.get('macd_histogram')
        if macd is not None and macd_signal is not None:
            macd_trend = "HAUSSIER ✅" if macd > macd_signal else "BAISSIER ❌"
            prompt += f"- **MACD:** {macd:.3f} | Signal: {macd_signal:.3f} → {macd_trend}\n"
            if macd_hist is not None:
                prompt += f"- **Histogramme MACD:** {macd_hist:.3f}\n"
        
        # Bandes de Bollinger
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        bb_position = indicators.get('bb_position')
        if bb_upper and bb_lower:
            prompt += f"- **Bollinger:** [{bb_lower:.2f}$ - {bb_upper:.2f}$]\n"
            if bb_position is not None:
                bb_zone = "HAUT (Surachat)" if bb_position > 80 else "BAS (Survente)" if bb_position < 20 else "Médian"
                prompt += f"- **Position Bollinger:** {bb_position:.1f}% → {bb_zone}\n"
        
        # Stochastique
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        if stoch_k is not None and stoch_d is not None:
            stoch_signal = "SURACHETÉ" if stoch_k > 80 else "SURVENDU" if stoch_k < 20 else "Neutre"
            prompt += f"- **Stochastique:** K={stoch_k:.1f} D={stoch_d:.1f} → {stoch_signal}\n"
        
        # Volume
        vol_ratio = indicators.get('volume_ratio')
        if vol_ratio is not None:
            vol_signal = "ÉLEVÉ 📈" if vol_ratio > 1.5 else "FAIBLE 📉" if vol_ratio < 0.5 else "Normal"
            prompt += f"- **Ratio Volume:** {vol_ratio:.2f}x → {vol_signal}\n"
        
        # ATR
        atr = indicators.get('atr')
        atr_pct = indicators.get('atr_percent')
        if atr is not None and atr_pct is not None:
            volatility = "HAUTE" if atr_pct > 3 else "FAIBLE" if atr_pct < 1 else "Modérée"
            prompt += f"- **ATR:** {atr:.2f}$ ({atr_pct:.2f}%) → Volatilité {volatility}\n"
        
        # Support/Résistance
        support = indicators.get('support')
        resistance = indicators.get('resistance')
        if support and resistance:
            prompt += f"- **Support:** {support:.2f}$ | **Résistance:** {resistance:.2f}$\n"
            # Distance aux niveaux
            dist_support = ((current_price - support) / current_price) * 100
            dist_resistance = ((resistance - current_price) / current_price) * 100
            prompt += f"- **Distance Support:** {dist_support:.1f}% | **Distance Résistance:** {dist_resistance:.1f}%\n"
    
    # === MODE AVANCÉ ===
    if advanced:
        # Actualités
        if news and len(news) > 0:
            prompt += "\n## 5. ACTUALITÉS RÉCENTES\n"
            prompt += "Voici les dernières actualités concernant cette action:\n\n"
            for i, article in enumerate(news[:5], 1):
                title = article.get('title', article.get('headline', 'Sans titre'))
                source = article.get('source', article.get('publisher', 'Source inconnue'))
                summary = article.get('summary', '')[:200]
                date = article.get('date', '')
                
                prompt += f"**{i}. {title}**\n"
                prompt += f"   - Source: {source}"
                if date:
                    prompt += f" | Date: {date}"
                prompt += "\n"
                if summary:
                    prompt += f"   - Résumé: {summary}...\n"
                prompt += "\n"
            
            prompt += """→ **Analyse l'impact des news:**
   - Sentiment global (Positif/Négatif/Neutre)
   - Catalyseurs potentiels identifiés
   - Risques médiatiques ou réputationnels
"""
        
        # Calendrier financier
        if calendar is not None:
            prompt += "\n## 6. CALENDRIER FINANCIER\n"
            try:
                if hasattr(calendar, 'items'):
                    for key, value in calendar.items():
                        prompt += f"- {key}: {value}\n"
                elif hasattr(calendar, 'to_dict'):
                    cal_dict = calendar.to_dict()
                    for key, value in cal_dict.items():
                        prompt += f"- {key}: {value}\n"
            except Exception:
                prompt += "- Données calendrier non disponibles\n"
        
        # Recommandations analystes
        if recommendations is not None:
            prompt += "\n## 7. RECOMMANDATIONS ANALYSTES (5 dernières)\n"
            try:
                if hasattr(recommendations, 'to_string'):
                    prompt += recommendations.to_string() + "\n"
                else:
                    prompt += str(recommendations) + "\n"
            except Exception:
                prompt += "- Données recommandations non disponibles\n"
    
    # === INSTRUCTIONS FINALES - FORMAT JSON ===
    prompt += f"""
---

## CONSIGNES D'ANALYSE

1. **Analyse technique:** Interprète les indicateurs de manière cohérente, identifie les divergences, les croisements de moyennes mobiles, et les patterns chartistes
2. **Analyse fondamentale:** Évalue la valorisation par rapport au secteur et aux moyennes historiques. Compare les multiples (P/E, PEG) aux pairs
3. **Catalyseurs:** Identifie les événements pouvant impacter le cours (earnings, annonces, M&A, macro)
4. **Risques:** Liste les principaux risques à surveiller (sectoriels, macro, spécifiques à l'entreprise)
5. **Niveaux clés:** Définis des points d'entrée/sortie précis basés sur support/résistance et ATR
6. **Horizon temporel:** Distingue court terme (1-5 jours), moyen terme (1-3 mois), long terme (6+ mois)

## FORMAT DE RÉPONSE - JSON OBLIGATOIRE

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.
Respecte EXACTEMENT ce schéma:

```json
{{
  "signal": "ACHETER" | "VENDRE" | "CONSERVER",
  "conviction": "Forte" | "Moyenne" | "Faible",
  "resume": "Synthèse détaillée de 3-4 phrases: situation actuelle, facteurs clés, et recommandation avec horizon temporel",
  "analyse_technique": {{
    "tendance": "Haussière" | "Baissière" | "Neutre",
    "tendance_details": "Description détaillée de la tendance avec les niveaux clés et la force du mouvement",
    "rsi_interpretation": "Analyse complète du RSI: niveau actuel, zones de surachat/survente, divergences éventuelles",
    "macd_interpretation": "Analyse du MACD: position par rapport au signal, momentum, croisements récents ou à venir",
    "moyennes_mobiles": "Position du prix par rapport aux MA20/50/200, golden/death cross potentiels",
    "volatilite": "Niveau ATR, implications pour le sizing de position et les stops",
    "volumes": "Analyse des volumes: confirmation de tendance, divergences, accumulation/distribution",
    "pattern": "Patterns chartistes identifiés (si présents): support, résistance, figures"
  }},
  "analyse_fondamentale": {{
    "valorisation": "Évaluation détaillée: P/E vs historique et secteur, PEG ratio, valeur relative",
    "qualite_entreprise": "Points sur la qualité du business: marges, croissance, avantages compétitifs",
    "points_forts": ["Force 1 avec explication", "Force 2 avec explication", "Force 3"],
    "points_faibles": ["Faiblesse 1 avec explication", "Faiblesse 2 avec explication"]
  }},
  "sentiment_marche": {{
    "consensus_analystes": "Synthèse des recommandations analystes et objectifs de cours",
    "news_impact": "Impact des actualités récentes sur le titre",
    "flux_institutionnels": "Tendance des flux si disponible"
  }},
  "catalyseurs": [
    {{"type": "positif", "horizon": "court/moyen/long terme", "description": "Description détaillée du catalyseur et son impact potentiel"}},
    {{"type": "negatif", "horizon": "court/moyen/long terme", "description": "Description du risque et probabilité"}}
  ],
  "risques": {{
    "risque_principal": "Le risque majeur à surveiller avec son déclencheur potentiel",
    "risques_secondaires": ["Risque 2 avec contexte", "Risque 3 avec contexte"],
    "stop_loss_justification": "Pourquoi ce niveau de stop est approprié"
  }},
  "niveaux": {{
    "achat_recommande": {current_price:.2f},
    "stop_loss": {current_price * 0.95:.2f},
    "objectif_1": {current_price * 1.10:.2f},
    "objectif_2": {current_price * 1.20:.2f},
    "ratio_risk_reward": "Calcul du ratio risque/rendement",
    "invalidation": "Niveau qui invaliderait le scénario"
  }},
  "plan_trading": {{
    "entree": "Conditions idéales pour entrer en position",
    "gestion": "Comment gérer la position (trailing stop, prise de profits partielle)",
    "sortie": "Conditions de sortie autres que TP/SL"
  }},
  "conclusion": "Synthèse finale de 4-5 phrases: contexte actuel, opportunité ou risque principal, niveaux clés à surveiller, et recommandation claire avec conviction et horizon"
}}
```

IMPORTANT:
- Retourne UNIQUEMENT le JSON, pas de texte explicatif
- Utilise des nombres pour les prix (pas de $)
- Les niveaux doivent être réalistes par rapport au support/résistance
- Chaque liste doit contenir au moins un élément
"""
    
    return prompt


def generate_analysis(ticker, model, context, num_threads=12):
    """
    Génère l'analyse via l'instance locale Ollama avec paramètres optimisés
    
    Args:
        ticker: Symbole de l'action
        model: Modèle Ollama à utiliser
        context: Prompt complet
        num_threads: Nombre de threads CPU
    
    Returns:
        tuple: (texte_analyse, temps_écoulé) ou (None, 0) en cas d'erreur
    """
    print(f"🤖 IA ({model}) en cours d'analyse pour {ticker}...")
    start_time = time.time()
    
    try:
        # Configuration optimisée pour l'analyse financière avec sortie JSON
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': """Tu es un analyste financier senior avec 20 ans d'expérience dans les marchés actions.
Tu fournis des analyses approfondies, précises, factuelles et actionnables.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après.
Tu ne fais jamais de prédictions garanties mais donnes des probabilités et scénarios.
Tu utilises un langage professionnel mais accessible en français.
Tu justifies toujours tes recommandations avec des données chiffrées.
Tu identifies les risques autant que les opportunités.
Tu donnes des niveaux de prix précis pour l'entrée, le stop-loss et les objectifs."""
                },
                {
                    'role': 'user', 
                    'content': context
                }
            ],
            format='json',  # Force la sortie JSON
            options={
                'temperature': 0.3,      # Factuel et cohérent
                'top_p': 0.9,            # Nucleus sampling
                'top_k': 40,             # Limite le vocabulaire
                'num_thread': num_threads,
                'num_predict': 5000,     # Augmenté pour analyses détaillées
                'repeat_penalty': 1.1,   # Évite les répétitions
            }
        )
        
        elapsed_time = time.time() - start_time
        analysis_text = response['message']['content']
        
        # Validation basique de la réponse
        if not analysis_text or len(analysis_text) < 100:
            print(f"⚠️ Réponse trop courte de l'IA pour {ticker}")
            return None, 0
        
        # Vérification du format attendu
        if 'SIGNAL:' not in analysis_text.upper():
            print(f"⚠️ Format de réponse non conforme pour {ticker}, tentative de correction...")
            # On garde quand même la réponse mais on log le problème
        
        return analysis_text, elapsed_time
        
    except ollama.ResponseError as e:
        print(f"❌ Erreur Ollama (ResponseError): {e}")
        return None, 0
    except ConnectionError:
        print(f"❌ Erreur: Impossible de se connecter à Ollama. Vérifiez que le service est démarré.")
        return None, 0
    except Exception as e:
        print(f"❌ Erreur inattendue Ollama: {type(e).__name__}: {e}")
        return None, 0


def generate_quick_analysis(ticker, model, current_price, indicators, num_threads=12):
    """
    Génère une analyse rapide basée uniquement sur les indicateurs techniques
    Utile pour un screening rapide de plusieurs actions
    
    Args:
        ticker: Symbole de l'action
        model: Modèle Ollama
        current_price: Prix actuel
        indicators: Dictionnaire des indicateurs
        num_threads: Nombre de threads
    
    Returns:
        tuple: (signal, conviction, résumé)
    """
    
    prompt = f"""Analyse rapide de {ticker} à {current_price:.2f}$

Indicateurs:
- RSI: {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')} vs Signal: {indicators.get('macd_signal', 'N/A')}
- Position Bollinger: {indicators.get('bb_position', 'N/A')}%
- Stochastique K: {indicators.get('stoch_k', 'N/A')}

Réponds UNIQUEMENT avec ce format (3 lignes):
SIGNAL: [ACHETER/VENDRE/CONSERVER]
CONVICTION: [Forte/Moyenne/Faible]
RÉSUMÉ: [10 mots maximum]"""

    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': 0.1,
                'num_thread': num_threads,
                'num_predict': 100
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"❌ Erreur analyse rapide: {e}")
        return "SIGNAL: CONSERVER\nCONVICTION: Faible\nRÉSUMÉ: Erreur d'analyse"


def compare_stocks(tickers_data, model, num_threads=12):
    """
    Compare plusieurs actions et génère un classement
    
    Args:
        tickers_data: Liste de dict avec {ticker, price, indicators, info}
        model: Modèle Ollama
        num_threads: Nombre de threads
    
    Returns:
        str: Analyse comparative
    """
    
    prompt = "# COMPARAISON D'ACTIONS\n\nCompare ces actions et classe-les par attractivité:\n\n"
    
    for data in tickers_data:
        ticker = data.get('ticker', 'N/A')
        price = data.get('price', 0)
        indicators = data.get('indicators', {})
        info = data.get('info', {})
        
        prompt += f"""## {ticker} - {price:.2f}$
- Secteur: {info.get('sector', 'N/A')}
- P/E: {info.get('trailingPE', 'N/A')}
- RSI: {indicators.get('rsi', 'N/A')}
- Tendance MACD: {"Haussière" if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else "Baissière"}

"""
    
    prompt += """
Fournis:
1. Classement des actions (meilleure à pire)
2. Justification pour chaque position
3. Action recommandée pour un portefeuille équilibré
"""
    
    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': 0.3,
                'num_thread': num_threads,
                'num_predict': 1500
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"❌ Erreur comparaison: {e}")
        return None


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

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.
Respecte EXACTEMENT ce schéma:

```json
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
```

IMPORTANT:
- Retourne UNIQUEMENT le JSON, pas de texte explicatif
- Un conseil par position dans conseils_positions
- Les conseils doivent être actionnables et précis
- Priorise les actions selon l'urgence
"""
    
    return prompt


def generate_portfolio_analysis(positions, latest_analyses, model, num_threads=12):
    """
    Génère l'analyse du portefeuille via Ollama.
    
    Args:
        positions: Liste des positions ouvertes
        latest_analyses: Dict des dernières analyses par ticker
        model: Modèle Ollama à utiliser
        num_threads: Nombre de threads CPU
    
    Returns:
        tuple: (analyse_json, temps_écoulé) ou (None, 0) en cas d'erreur
    """
    import json
    
    if not positions:
        print("⚠️ Aucune position ouverte à analyser")
        return None, 0
    
    print(f"🤖 IA ({model}) - Analyse du portefeuille ({len(positions)} positions)...")
    start_time = time.time()
    
    # Construire le prompt
    prompt = build_portfolio_analysis_prompt(positions, latest_analyses)
    
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': """Tu es un gestionnaire de portefeuille expérimenté.
Tu analyses les positions d'un investisseur et fournis des conseils actionnables.
Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après.
Tu priorises la gestion du risque et la préservation du capital.
Tu donnes des conseils précis et justifiés pour chaque position.
Tu identifies les opportunités d'optimisation du portefeuille."""
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            format='json',
            options={
                'temperature': 0.3,
                'top_p': 0.9,
                'num_thread': num_threads,
                'num_predict': 3000,
                'repeat_penalty': 1.1,
            }
        )
        
        elapsed_time = time.time() - start_time
        analysis_text = response['message']['content']
        
        # Nettoyer les backticks markdown si présents
        clean_text = analysis_text.strip()
        if clean_text.startswith('```'):
            # Extraire le contenu entre les backticks
            lines = clean_text.split('\n')
            # Retirer la première ligne (```json ou ```)
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Retirer la dernière ligne si c'est ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean_text = '\n'.join(lines)
        
        # Validation JSON
        try:
            analysis_json = json.loads(clean_text)
            print(f"✅ Analyse portefeuille JSON valide reçue")
            return analysis_json, elapsed_time
        except json.JSONDecodeError as e:
            print(f"⚠️ Réponse non-JSON valide: {e}")
            print(f"   Réponse brute: {clean_text[:200]}...")
            return {'raw_response': analysis_text, 'error': 'JSON parse failed'}, elapsed_time
            
    except Exception as e:
        print(f"❌ Erreur analyse portefeuille: {type(e).__name__}: {e}")
        return None, 0
