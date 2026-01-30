"""Extraction du signal et résumé depuis l'analyse IA - Support JSON structuré"""
import re
import json


def extract_signal_from_analysis(analysis_text):
    """
    Extrait le signal, la conviction et données structurées depuis l'analyse IA.
    Supporte le nouveau format JSON structuré avec fallback regex pour compatibilité.
    
    Returns:
        dict: {
            'signal': str,
            'confidence': str,
            'summary': str,
            'structured_data': dict | None  # Données JSON si disponibles
        }
    """
    
    # === TENTATIVE DE PARSING JSON ===
    json_result = _try_parse_json(analysis_text)
    if json_result:
        return json_result
    
    # === FALLBACK: EXTRACTION REGEX (ancien format) ===
    return _extract_with_regex(analysis_text)


def _try_parse_json(analysis_text):
    """
    Tente de parser la réponse comme JSON structuré.
    
    Returns:
        dict | None: Résultat structuré ou None si échec
    """
    try:
        # Nettoyer le texte (enlever markdown code blocks si présents)
        clean_text = analysis_text.strip()
        
        # Retirer les blocs de code markdown ```json ... ```
        if clean_text.startswith('```'):
            # Trouver le premier saut de ligne et le dernier ```
            first_newline = clean_text.find('\n')
            last_backticks = clean_text.rfind('```')
            if first_newline > 0 and last_backticks > first_newline:
                clean_text = clean_text[first_newline:last_backticks].strip()
        
        # Parser le JSON
        data = json.loads(clean_text)
        
        # Valider les champs requis
        if not isinstance(data, dict):
            return None
            
        signal = data.get('signal', '').upper()
        conviction = data.get('conviction', 'Moyenne')
        resume = data.get('resume', '')
        
        # Normaliser le signal
        signal = _normalize_signal(signal)
        
        # Valider la conviction
        conviction = _normalize_conviction(conviction)
        
        # Construire le résumé s'il manque
        if not resume or len(resume) < 10:
            resume = data.get('conclusion', f"Analyse {signal.lower()} avec conviction {conviction.lower()}.")
        
        # Limiter longueur résumé
        if len(resume) > 250:
            resume = resume[:247] + '...'
        
        return {
            'signal': signal,
            'confidence': conviction,
            'summary': resume,
            'structured_data': {
                'analyse_technique': data.get('analyse_technique'),
                'analyse_fondamentale': data.get('analyse_fondamentale'),
                'catalyseurs': data.get('catalyseurs', []),
                'risques': data.get('risques', []),
                'niveaux': data.get('niveaux'),
                'conclusion': data.get('conclusion', '')
            }
        }
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"⚠️ JSON parsing échoué, fallback regex: {str(e)[:50]}")
        return None


def _normalize_signal(signal):
    """Normalise le signal vers les valeurs attendues"""
    signal = signal.upper().strip()
    
    if signal in ['ACHETER', 'ACHAT', 'BUY']:
        return 'ACHAT'
    elif signal in ['VENDRE', 'VENTE', 'SELL']:
        return 'VENTE'
    elif signal in ['CONSERVER', 'HOLD', 'NEUTRE', 'NEUTRAL']:
        return 'CONSERVER'
    else:
        return 'NEUTRE'


def _normalize_conviction(conviction):
    """Normalise la conviction vers les valeurs attendues"""
    conviction = conviction.strip().lower()
    
    if conviction in ['forte', 'high', 'élevée']:
        return 'Forte'
    elif conviction in ['faible', 'low', 'basse']:
        return 'Faible'
    else:
        return 'Moyenne'


def _extract_with_regex(analysis_text):
    """
    Extraction par regex pour l'ancien format de réponse.
    Fallback si le parsing JSON échoue.
    """
    analysis_lower = analysis_text.lower()
    
    # === DÉTECTION DU SIGNAL ===
    signal = "NEUTRE"
    
    # Patterns pour ACHAT
    buy_patterns = [
        r'signal:\s*achat',
        r'signal:\s*acheter',
        r'recommandation:\s*achat',
        r"opportunité\s+d'achat",
        r"conseillé\s+d'acheter",
        r'\*\*signal:\s*achat\*\*',
        r'position:\s*achat'
    ]
    
    # Patterns pour VENTE
    sell_patterns = [
        r'signal:\s*vente',
        r'signal:\s*vendre',
        r'recommandation:\s*vente',
        r'conseillé\s+de\s+vendre',
        r'\*\*signal:\s*vente\*\*',
        r'position:\s*vente'
    ]
    
    # Patterns pour CONSERVER
    hold_patterns = [
        r'signal:\s*conservation',
        r'signal:\s*conserver',
        r'recommandation:\s*conservation',
        r'recommandation:\s*conserver',
        r'position:\s*neutre',
        r'\*\*signal:\s*conservation\*\*'
    ]
    
    # Vérifier les patterns
    if any(re.search(pattern, analysis_lower) for pattern in buy_patterns):
        signal = "ACHAT"
    elif any(re.search(pattern, analysis_lower) for pattern in sell_patterns):
        signal = "VENTE"
    elif any(re.search(pattern, analysis_lower) for pattern in hold_patterns):
        signal = "CONSERVER"
    
    # === DÉTECTION DE LA CONVICTION ===
    confidence = "Moyenne"
    
    if any(word in analysis_lower for word in [
        'forte conviction', 
        'fortement recommandé', 
        'conviction forte',
        'conviction: forte',
        'très favorable'
    ]):
        confidence = "Forte"
    elif any(word in analysis_lower for word in [
        'faible conviction',
        'prudence',
        'conviction faible',
        'conviction: faible',
        'incertain'
    ]):
        confidence = "Faible"
    
    # === EXTRACTION DU RÉSUMÉ ===
    summary_match = re.search(
        r'\*\*résumé en 1 phrase:\*\*\s*(.+?)(?:\n|$)', 
        analysis_text, 
        re.IGNORECASE
    )
    
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        # Essayer le pattern RÉSUMÉ: directement
        resume_match = re.search(
            r'résumé:\s*(.+?)(?:\n|$)',
            analysis_text,
            re.IGNORECASE
        )
        if resume_match:
            summary = resume_match.group(1).strip()
        else:
            # Prendre les premières phrases significatives
            lines = [
                line.strip() 
                for line in analysis_text.split('\n') 
                if line.strip() and not line.startswith('**') and not line.startswith('#')
            ]
            
            sentences = []
            for line in lines[:5]:
                parts = line.split('.')
                sentences.extend([s.strip() for s in parts if len(s.strip()) > 20])
                if len(sentences) >= 2:
                    break
            
            summary = '. '.join(sentences[:2])
            if summary and not summary.endswith('.'):
                summary += '.'
    
    # Limiter à 250 caractères
    if len(summary) > 250:
        summary = summary[:247] + '...'
    
    # Si pas de résumé, créer un générique
    if not summary or len(summary) < 20:
        summary = f"Analyse {signal.lower()} avec conviction {confidence.lower()}."
    
    return {
        'signal': signal,
        'confidence': confidence,
        'summary': summary,
        'structured_data': None  # Pas de données structurées en mode regex
    }


def validate_signal(signal_info):
    """Valide que le signal extrait est correct"""
    valid_signals = ['ACHAT', 'VENTE', 'CONSERVER', 'NEUTRE']
    valid_confidences = ['Forte', 'Moyenne', 'Faible']
    
    if signal_info['signal'] not in valid_signals:
        signal_info['signal'] = 'NEUTRE'
    
    if signal_info['confidence'] not in valid_confidences:
        signal_info['confidence'] = 'Moyenne'
    
    return signal_info


def format_structured_analysis(structured_data):
    """
    Formate les données structurées en texte lisible pour l'affichage.
    Utilisé pour la compatibilité avec l'ancien champ 'analysis' texte.
    """
    if not structured_data:
        return ""
    
    lines = []
    
    # Analyse technique
    tech = structured_data.get('analyse_technique')
    if tech:
        lines.append("### Analyse Technique")
        if tech.get('tendance'):
            lines.append(f"**Tendance:** {tech['tendance']}")
        if tech.get('rsi_interpretation'):
            lines.append(f"**RSI:** {tech['rsi_interpretation']}")
        if tech.get('macd_interpretation'):
            lines.append(f"**MACD:** {tech['macd_interpretation']}")
        if tech.get('volatilite'):
            lines.append(f"**Volatilité:** {tech['volatilite']}")
        lines.append("")
    
    # Analyse fondamentale
    fond = structured_data.get('analyse_fondamentale')
    if fond:
        lines.append("### Analyse Fondamentale")
        if fond.get('valorisation'):
            lines.append(f"**Valorisation:** {fond['valorisation']}")
        if fond.get('points_forts'):
            lines.append("**Points forts:**")
            for p in fond['points_forts']:
                lines.append(f"• {p}")
        if fond.get('points_faibles'):
            lines.append("**Points faibles:**")
            for p in fond['points_faibles']:
                lines.append(f"• {p}")
        lines.append("")
    
    # Catalyseurs & Risques
    catalyseurs = structured_data.get('catalyseurs', [])
    risques = structured_data.get('risques', [])
    if catalyseurs or risques:
        lines.append("### Catalyseurs & Risques")
        for cat in catalyseurs:
            icon = "🟢" if cat.get('type') == 'positif' else "🔴"
            lines.append(f"{icon} {cat.get('description', '')}")
        for risque in risques:
            lines.append(f"⚠️ {risque}")
        lines.append("")
    
    # Niveaux d'action
    niveaux = structured_data.get('niveaux')
    if niveaux:
        lines.append("### Niveaux d'Action")
        if niveaux.get('achat_recommande'):
            lines.append(f"• Achat recommandé: ${niveaux['achat_recommande']:.2f}")
        if niveaux.get('stop_loss'):
            lines.append(f"• Stop-loss: ${niveaux['stop_loss']:.2f}")
        if niveaux.get('objectif_1'):
            lines.append(f"• Objectif 1: ${niveaux['objectif_1']:.2f}")
        if niveaux.get('objectif_2'):
            lines.append(f"• Objectif 2: ${niveaux['objectif_2']:.2f}")
        lines.append("")
    
    # Conclusion
    conclusion = structured_data.get('conclusion')
    if conclusion:
        lines.append("### Conclusion")
        lines.append(conclusion)
    
    return "\n".join(lines)
