"""
Système de rapport email quotidien - Finance AI Dashboard
Envoie un résumé des analyses chaque matin à 8h
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import schedule
import time
import sys

# Import database module - chemin partagé via volume Docker
sys.path.insert(0, '/app')
from database import get_latest_by_ticker, init_db

# Initialiser la base de données
init_db()


# ============================================
# CONFIGURATION
# ============================================
class EmailConfig:
    """Configuration email - À personnaliser"""
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', SMTP_USER)
    RECIPIENT_EMAILS = os.getenv('RECIPIENT_EMAILS', '').split(',')
    
    REPORT_HOUR = os.getenv('REPORT_HOUR', '08:00')
    DATA_DIR = os.getenv('DATA_DIR', '/app/data')
    
    @classmethod
    def is_configured(cls) -> bool:
        return all([
            cls.SMTP_SERVER,
            cls.SMTP_USER,
            cls.SMTP_PASSWORD,
            cls.RECIPIENT_EMAILS[0]
        ])


# ============================================
# COLLECTE DES DONNÉES
# ============================================
def get_latest_analyses(data_dir: str = None, hours: int = 24) -> List[Dict]:
    """Récupère la dernière analyse de chaque ticker des dernières X heures depuis la DB"""
    # Utiliser la base de données SQLite
    latest_dict = get_latest_by_ticker(hours=hours)
    
    if not latest_dict:
        print(f"⚠️ Aucune analyse trouvée dans les {hours} dernières heures")
        return []
    
    analyses = list(latest_dict.values())
    
    # Trier par signal (ACHAT en premier) puis par variation
    def sort_key(item):
        signal_order = {'ACHAT': 0, 'ACHETER': 0, 'CONSERVER': 1, 'VENTE': 2, 'VENDRE': 2, 'NEUTRE': 3}
        signal = item.get('signal', 'NEUTRE').upper()
        return (signal_order.get(signal, 3), -item.get('change_1d', 0))
    
    return sorted(analyses, key=sort_key)


def calculate_score(analysis: Dict) -> int:
    """Calcule un score de santé 0-100"""
    score = 50
    indicators = analysis.get('indicators', {})
    signal = analysis.get('signal', '').upper()
    
    rsi = indicators.get('rsi')
    if rsi:
        if 30 <= rsi <= 70:
            score += 20
        elif rsi < 30:
            score += 10
        else:
            score -= 10
    
    macd_hist = indicators.get('macd_histogram')
    if macd_hist:
        score += 15 if macd_hist > 0 else -5
    
    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio:
        if vol_ratio > 1.2:
            score += 10
        elif vol_ratio < 0.5:
            score -= 5
    
    if 'ACHAT' in signal or 'BUY' in signal:
        score += 15
    elif 'VENTE' in signal or 'SELL' in signal:
        score -= 10
    
    return max(0, min(100, score))


def get_market_summary(analyses: List[Dict]) -> Dict:
    """Génère un résumé du marché"""
    if not analyses:
        return {
            'total': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'avg_change_1d': 0,
            'avg_change_1mo': 0,
            'best_performer': None,
            'worst_performer': None,
            'high_conviction_buys': [],
            'high_conviction_sells': [],
            'oversold': [],
            'overbought': []
        }
    
    buy_signals = [a for a in analyses if 'ACHAT' in a.get('signal', '').upper() or 'BUY' in a.get('signal', '').upper()]
    sell_signals = [a for a in analyses if 'VENT' in a.get('signal', '').upper() or 'SELL' in a.get('signal', '').upper()]
    hold_signals = [a for a in analyses if a not in buy_signals and a not in sell_signals]
    
    changes_1d = [a.get('change_1d', 0) for a in analyses]
    changes_1mo = [a.get('change_1mo', 0) for a in analyses]
    
    sorted_by_change = sorted(analyses, key=lambda x: x.get('change_1d', 0), reverse=True)
    
    # Haute conviction
    high_conviction_buys = [a for a in buy_signals if a.get('confidence', '').lower() == 'forte']
    high_conviction_sells = [a for a in sell_signals if a.get('confidence', '').lower() == 'forte']
    
    # RSI extrêmes
    oversold = [a for a in analyses if a.get('indicators', {}).get('rsi', 50) < 30]
    overbought = [a for a in analyses if a.get('indicators', {}).get('rsi', 50) > 70]
    
    return {
        'total': len(analyses),
        'buy_signals': len(buy_signals),
        'sell_signals': len(sell_signals),
        'hold_signals': len(hold_signals),
        'avg_change_1d': sum(changes_1d) / len(changes_1d) if changes_1d else 0,
        'avg_change_1mo': sum(changes_1mo) / len(changes_1mo) if changes_1mo else 0,
        'best_performer': sorted_by_change[0] if sorted_by_change else None,
        'worst_performer': sorted_by_change[-1] if sorted_by_change else None,
        'high_conviction_buys': high_conviction_buys,
        'high_conviction_sells': high_conviction_sells,
        'oversold': oversold,
        'overbought': overbought
    }


# ============================================
# GÉNÉRATION DU RAPPORT HTML (THÈME BLANC)
# ============================================
def generate_html_report(analyses: List[Dict], summary: Dict) -> str:
    """Génère le rapport HTML avec thème clair"""
    
    date_str = datetime.now().strftime('%A %d %B %Y')
    time_str = datetime.now().strftime('%H:%M')
    
    # Couleurs - Thème QoQa (comme le dashboard)
    c = {
        'bg': '#fef7f3',
        'bg_alt': '#fef3ed',
        'bg_card': '#ffffff',
        'border': '#fde5d9',
        'text': '#1f1a16',
        'text_secondary': '#5c5046',
        'text_muted': '#9a8c80',
        'primary': '#ff3366',
        'primary_gradient': 'linear-gradient(135deg, #ff3366, #7c3aed)',
        'success': '#06d6a0',
        'success_bg': 'rgba(6, 214, 160, 0.12)',
        'success_border': 'rgba(6, 214, 160, 0.35)',
        'danger': '#ff3366',
        'danger_bg': 'rgba(255, 51, 102, 0.1)',
        'danger_border': 'rgba(255, 51, 102, 0.35)',
        'warning': '#ffb347',
        'warning_bg': 'rgba(255, 179, 71, 0.12)',
        'warning_border': 'rgba(255, 179, 71, 0.35)',
    }
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Finance AI - {date_str}</title>
</head>
<body style="margin: 0; padding: 0; background: linear-gradient(145deg, #fff5f0 0%, #f0f4ff 40%, #f0fff8 70%, #fff5f5 100%); font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: {c['text']}; line-height: 1.7;">
    
    <div style="max-width: 680px; margin: 0 auto; padding: 32px 20px;">
        
        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, #ff3366 0%, #7c3aed 50%, #06d6a0 100%); border-radius: 20px; padding: 48px 32px; margin-bottom: 28px; text-align: center; box-shadow: 0 12px 40px rgba(255, 51, 102, 0.3);">
            <h1 style="margin: 0; color: #ffffff; font-size: 38px; font-weight: 900; letter-spacing: -1px; text-shadow: 0 2px 10px rgba(0,0,0,0.15);">
                🚀 Finance AI
            </h1>
            <p style="margin: 12px 0 0; color: rgba(255,255,255,0.95); font-size: 15px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">
                Rapport Quotidien
            </p>
            <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500;">
                {date_str} à {time_str}
            </p>
        </div>
        
        <!-- RÉSUMÉ RAPIDE -->
        <div style="background: {c['bg_card']}; border: 2px solid {c['border']}; border-top: 4px solid #ff3366; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(255, 51, 102, 0.08);">
            <h2 style="margin: 0 0 28px; font-size: 22px; font-weight: 800; color: {c['text']}; letter-spacing: -0.5px;">
                🎯 Vue d'ensemble
            </h2>
            
            <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 24px;">
                <!-- Achats -->
                <div style="flex: 1; min-width: 100px; background: {c['success_bg']}; border: 2px solid {c['success_border']}; border-radius: 12px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 800; color: {c['success']};">{summary['buy_signals']}</div>
                    <div style="font-size: 11px; color: {c['success']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">Achats</div>
                </div>
                <!-- Conserver -->
                <div style="flex: 1; min-width: 100px; background: {c['warning_bg']}; border: 2px solid {c['warning_border']}; border-radius: 12px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 800; color: {c['warning']};">{summary['hold_signals']}</div>
                    <div style="font-size: 11px; color: {c['warning']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">Conserver</div>
                </div>
                <!-- Ventes -->
                <div style="flex: 1; min-width: 100px; background: {c['danger_bg']}; border: 2px solid {c['danger_border']}; border-radius: 12px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 800; color: {c['danger']};">{summary['sell_signals']}</div>
                    <div style="font-size: 11px; color: {c['danger']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">Ventes</div>
                </div>
            </div>
            
            <!-- Performances moyennes -->
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 150px; background: {c['bg_alt']}; border: 1px solid {c['border']}; border-radius: 12px; padding: 16px;">
                    <div style="font-size: 11px; color: {c['text_secondary']}; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Performance 24h (moy.)</div>
                    <div style="font-size: 24px; font-weight: 800; color: {c['success'] if summary['avg_change_1d'] >= 0 else c['danger']};">
                        {'+' if summary['avg_change_1d'] >= 0 else ''}{summary['avg_change_1d']:.2f}%
                    </div>
                </div>
                <div style="flex: 1; min-width: 150px; background: {c['bg_alt']}; border: 1px solid {c['border']}; border-radius: 12px; padding: 16px;">
                    <div style="font-size: 11px; color: {c['text_secondary']}; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Performance 1 mois (moy.)</div>
                    <div style="font-size: 24px; font-weight: 800; color: {c['success'] if summary['avg_change_1mo'] >= 0 else c['danger']};">
                        {'+' if summary['avg_change_1mo'] >= 0 else ''}{summary['avg_change_1mo']:.2f}%
                    </div>
                </div>
            </div>
        </div>
"""
    
    # SIGNAUX HAUTE CONVICTION - ACHATS
    if summary['high_conviction_buys']:
        html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['success_border']}; border-top: 4px solid {c['success']}; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(6, 214, 160, 0.12);">
            <h2 style="margin: 0 0 24px; font-size: 22px; font-weight: 800; color: {c['success']}; letter-spacing: -0.5px;">
                🚀 Signaux d'ACHAT (Haute conviction)
            </h2>
"""
        for a in summary['high_conviction_buys']:
            ind = a.get('indicators', {})
            html += f"""
            <div style="background: linear-gradient(135deg, rgba(6, 214, 160, 0.08), rgba(6, 214, 160, 0.15)); border: 2px solid {c['success_border']}; border-radius: 16px; padding: 24px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <span style="font-size: 24px; font-weight: 900; color: {c['text']}; letter-spacing: -0.5px;">{a['ticker']}</span>
                        <span style="display: inline-block; background: linear-gradient(135deg, {c['success']}, #00b386); color: white; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; margin-left: 14px; text-transform: uppercase; letter-spacing: 0.5px;">ACHAT FORT</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 18px; font-weight: 700; color: {c['text']};">${a.get('price', 0):.2f}</div>
                        <div style="font-size: 14px; color: {c['success'] if a.get('change_1d', 0) >= 0 else c['danger']};">
                            {'+' if a.get('change_1d', 0) >= 0 else ''}{a.get('change_1d', 0):.2f}% (24h)
                        </div>
                    </div>
                </div>
                <div style="font-size: 14px; color: {c['text_secondary']}; margin-bottom: 12px;">
                    💡 {a.get('summary', 'Aucun résumé')}
                </div>
                <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: {c['text_muted']};">
                    <span>RSI: <strong style="color: {c['text']};">{ind.get('rsi', 0):.0f}</strong></span>
                    <span>Support: <strong style="color: {c['text']};">${ind.get('support', 0):.2f}</strong></span>
                    <span>Résistance: <strong style="color: {c['text']};">${ind.get('resistance', 0):.2f}</strong></span>
                </div>
            </div>
"""
        html += "</div>"
    
    # SIGNAUX HAUTE CONVICTION - VENTES
    if summary['high_conviction_sells']:
        html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['danger_border']}; border-top: 4px solid {c['danger']}; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(255, 51, 102, 0.12);">
            <h2 style="margin: 0 0 24px; font-size: 22px; font-weight: 800; color: {c['danger']}; letter-spacing: -0.5px;">
                ⚠️ Signaux de VENTE (Haute conviction)
            </h2>
"""
        for a in summary['high_conviction_sells']:
            ind = a.get('indicators', {})
            html += f"""
            <div style="background: linear-gradient(135deg, rgba(255, 51, 102, 0.06), rgba(255, 51, 102, 0.12)); border: 2px solid {c['danger_border']}; border-radius: 16px; padding: 24px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <span style="font-size: 24px; font-weight: 900; color: {c['text']}; letter-spacing: -0.5px;">{a['ticker']}</span>
                        <span style="display: inline-block; background: linear-gradient(135deg, {c['danger']}, #cc2952); color: white; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; margin-left: 14px; text-transform: uppercase; letter-spacing: 0.5px;">VENTE</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 18px; font-weight: 700; color: {c['text']};">${a.get('price', 0):.2f}</div>
                        <div style="font-size: 14px; color: {c['danger']};">
                            {a.get('change_1d', 0):.2f}% (24h)
                        </div>
                    </div>
                </div>
                <div style="font-size: 14px; color: {c['text_secondary']};">
                    💡 {a.get('summary', 'Aucun résumé')}
                </div>
            </div>
"""
        html += "</div>"
    
    # ALERTES RSI
    if summary['oversold'] or summary['overbought']:
        html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['border']}; border-top: 4px solid #7c3aed; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(124, 58, 237, 0.08);">
            <h2 style="margin: 0 0 24px; font-size: 22px; font-weight: 800; color: {c['text']}; letter-spacing: -0.5px;">
                📉 Alertes RSI
            </h2>
"""
        if summary['oversold']:
            html += f"""
            <div style="margin-bottom: 16px;">
                <div style="font-size: 14px; font-weight: 600; color: {c['success']}; margin-bottom: 8px;">Survendus (RSI &lt; 30) - Opportunités potentielles</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
"""
            for a in summary['oversold']:
                rsi = a.get('indicators', {}).get('rsi', 0)
                html += f"""
                    <span style="background: linear-gradient(135deg, rgba(6, 214, 160, 0.1), rgba(6, 214, 160, 0.2)); border: 2px solid {c['success_border']}; color: {c['success']}; padding: 10px 16px; border-radius: 25px; font-size: 13px; font-weight: 700;">
                        {a['ticker']} (RSI: {rsi:.0f})
                    </span>
"""
            html += "</div></div>"
        
        if summary['overbought']:
            html += f"""
            <div>
                <div style="font-size: 14px; font-weight: 600; color: {c['danger']}; margin-bottom: 8px;">Surachetés (RSI &gt; 70) - Prudence recommandée</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
"""
            for a in summary['overbought']:
                rsi = a.get('indicators', {}).get('rsi', 0)
                html += f"""
                    <span style="background: linear-gradient(135deg, rgba(255, 51, 102, 0.08), rgba(255, 51, 102, 0.15)); border: 2px solid {c['danger_border']}; color: {c['danger']}; padding: 10px 16px; border-radius: 25px; font-size: 13px; font-weight: 700;">
                        {a['ticker']} (RSI: {rsi:.0f})
                    </span>
"""
            html += "</div></div>"
        html += "</div>"
    
    # TOP / FLOP
    if summary['best_performer'] and summary['worst_performer']:
        bp = summary['best_performer']
        wp = summary['worst_performer']
        html += f"""
        <div style="display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, rgba(6, 214, 160, 0.06), rgba(6, 214, 160, 0.12)); border: 2px solid {c['success_border']}; border-radius: 20px; padding: 28px; box-shadow: 0 4px 20px rgba(6, 214, 160, 0.1);">
                <div style="font-size: 11px; color: {c['success']}; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">🏆 Meilleure perf. 24h</div>
                <div style="font-size: 32px; font-weight: 900; color: {c['text']}; letter-spacing: -1px;">{bp['ticker']}</div>
                <div style="font-size: 28px; font-weight: 900; color: {c['success']}; margin-top: 6px;">+{bp.get('change_1d', 0):.2f}%</div>
                <div style="font-size: 15px; color: {c['text_secondary']}; margin-top: 8px; font-weight: 600;">${bp.get('price', 0):.2f}</div>
            </div>
            <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, rgba(255, 51, 102, 0.04), rgba(255, 51, 102, 0.1)); border: 2px solid {c['danger_border']}; border-radius: 20px; padding: 28px; box-shadow: 0 4px 20px rgba(255, 51, 102, 0.1);">
                <div style="font-size: 11px; color: {c['danger']}; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">📉 Pire perf. 24h</div>
                <div style="font-size: 32px; font-weight: 900; color: {c['text']}; letter-spacing: -1px;">{wp['ticker']}</div>
                <div style="font-size: 28px; font-weight: 900; color: {c['danger']}; margin-top: 6px;">{wp.get('change_1d', 0):.2f}%</div>
                <div style="font-size: 15px; color: {c['text_secondary']}; margin-top: 8px; font-weight: 600;">${wp.get('price', 0):.2f}</div>
            </div>
        </div>
"""
    
    # TABLEAU COMPLET
    html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['border']}; border-top: 4px solid #ffb347; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(255, 179, 71, 0.08);">
            <h2 style="margin: 0 0 28px; font-size: 22px; font-weight: 800; color: {c['text']}; letter-spacing: -0.5px;">
                📋 Toutes les analyses ({summary['total']} actions)
            </h2>
            
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="border-bottom: 3px solid {c['border']};">
                        <th style="text-align: left; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">ACTION</th>
                        <th style="text-align: center; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">SIGNAL</th>
                        <th style="text-align: right; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">PRIX</th>
                        <th style="text-align: right; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">24H</th>
                        <th style="text-align: right; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">1 MOIS</th>
                        <th style="text-align: center; padding: 16px 12px; color: {c['text_secondary']}; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">RSI</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for analysis in analyses:
        signal = analysis.get('signal', 'NEUTRE').upper()
        if 'ACHAT' in signal or 'BUY' in signal:
            signal_display = 'ACHAT'
            signal_color = c['success']
            signal_bg = c['success_bg']
        elif 'VENT' in signal or 'SELL' in signal:
            signal_display = 'VENTE'
            signal_color = c['danger']
            signal_bg = c['danger_bg']
        elif 'CONSERV' in signal or 'HOLD' in signal:
            signal_display = 'CONSERVER'
            signal_color = c['warning']
            signal_bg = c['warning_bg']
        else:
            signal_display = 'NEUTRE'
            signal_color = c['text_muted']
            signal_bg = c['bg_alt']
        
        change_1d = analysis.get('change_1d', 0)
        change_1mo = analysis.get('change_1mo', 0)
        rsi = analysis.get('indicators', {}).get('rsi', 0)
        
        rsi_color = c['success'] if rsi < 30 else c['danger'] if rsi > 70 else c['text']
        
        html += f"""
                    <tr style="border-bottom: 1px solid {c['border']};">
                        <td style="padding: 18px 12px;">
                            <div style="font-weight: 800; color: {c['text']}; font-size: 16px; letter-spacing: -0.3px;">{analysis['ticker']}</div>
                            <div style="font-size: 11px; color: {c['text_muted']}; font-weight: 600; margin-top: 2px;">{analysis.get('confidence', 'Moyenne')}</div>
                        </td>
                        <td style="text-align: center; padding: 18px 12px;">
                            <span style="display: inline-block; background: {signal_bg}; border: 2px solid {signal_color}; color: {signal_color}; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{signal_display}</span>
                        </td>
                        <td style="text-align: right; padding: 18px 12px; font-weight: 800; color: {c['text']}; font-size: 16px;">
                            ${analysis.get('price', 0):.2f}
                        </td>
                        <td style="text-align: right; padding: 18px 12px; font-weight: 800; color: {c['success'] if change_1d >= 0 else c['danger']}; font-size: 16px;">
                            {'+' if change_1d >= 0 else ''}{change_1d:.2f}%
                        </td>
                        <td style="text-align: right; padding: 18px 12px; font-weight: 800; color: {c['success'] if change_1mo >= 0 else c['danger']}; font-size: 16px;">
                            {'+' if change_1mo >= 0 else ''}{change_1mo:.2f}%
                        </td>
                        <td style="text-align: center; padding: 18px 12px; font-weight: 800; color: {rsi_color}; font-size: 16px;">
                            {rsi:.0f}
                        </td>
                    </tr>
"""
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <!-- FOOTER -->\n        <div style=\"text-align: center; padding: 32px 20px; margin-top: 16px;\">\n            <div style=\"display: inline-block; background: linear-gradient(135deg, #ff3366, #7c3aed); padding: 2px; border-radius: 12px;\">\n                <div style=\"background: {c['bg']}; border-radius: 10px; padding: 16px 28px;\">\n                    <p style=\"margin: 0; color: {c['text']}; font-size: 14px; font-weight: 600;\">\n                        Rapport généré par <span style=\"background: linear-gradient(135deg, #ff3366, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;\">Finance AI</span>\n                    </p>\n                    <p style=\"margin: 8px 0 0; font-size: 13px; color: {c['text_muted']};\">\n                        Made with ❤️ by Anca\n                    </p>\n                </div>\n            </div>\n        </div>
        
    </div>
</body>
</html>
"""
    
    return html


# ============================================
# ENVOI EMAIL
# ============================================
def send_email(subject: str, html_content: str, recipients: List[str]) -> bool:
    """Envoie l'email via SMTP"""
    if not EmailConfig.is_configured():
        print("❌ Configuration email incomplète")
        return False
    
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = EmailConfig.SENDER_EMAIL
        message['To'] = ', '.join(recipients)
        
        text_content = "Consultez ce rapport dans un client email compatible HTML."
        message.attach(MIMEText(text_content, 'plain'))
        message.attach(MIMEText(html_content, 'html'))
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
            server.sendmail(
                EmailConfig.SENDER_EMAIL,
                recipients,
                message.as_string()
            )
        
        print(f"✅ Email envoyé à {', '.join(recipients)}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False


# ============================================
# FONCTION PRINCIPALE
# ============================================
def send_daily_report():
    """Génère et envoie le rapport quotidien"""
    print(f"\n{'='*50}")
    print(f"📧 Génération du rapport - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")
    
    analyses = get_latest_analyses(EmailConfig.DATA_DIR, hours=24)
    
    if not analyses:
        print("⚠️ Aucune analyse trouvée pour le rapport")
        return False
    
    print(f"📊 {len(analyses)} analyse(s) trouvée(s)")
    
    summary = get_market_summary(analyses)
    html_report = generate_html_report(analyses, summary)
    
    # Sujet dynamique
    date_str = datetime.now().strftime('%d/%m/%Y')
    subject = f"Finance AI | {date_str} | {summary['buy_signals']} Achats • {summary['hold_signals']} Conserver • {summary['sell_signals']} Ventes"
    
    return send_email(
        subject=subject,
        html_content=html_report,
        recipients=[r.strip() for r in EmailConfig.RECIPIENT_EMAILS if r.strip()]
    )


def test_email():
    """Envoie un email de test"""
    print("🧪 Test d'envoi email...")
    
    test_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: sans-serif; padding: 40px; background: #f8f9fa;">
        <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h1 style="color: #10b981; margin: 0 0 16px;">✅ Test réussi !</h1>
            <p style="color: #64748b; margin: 0 0 20px; font-size: 15px;">
                Votre configuration email Finance AI Dashboard fonctionne correctement.
            </p>
            <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                Envoyé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        subject="✅ Test Finance AI Dashboard",
        html_content=test_html,
        recipients=[r.strip() for r in EmailConfig.RECIPIENT_EMAILS if r.strip()]
    )


def run_scheduler():
    """Lance le planificateur"""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║   📧 FINANCE AI - SERVICE DE RAPPORT EMAIL                ║
║   Envoi quotidien à {EmailConfig.REPORT_HOUR}                              ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    if not EmailConfig.is_configured():
        print("❌ Configuration email incomplète!")
        print("\nVariables requises dans .env:")
        print("  SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAILS")
        return
    
    print(f"✅ Configuration OK")
    print(f"📬 Destinataires: {', '.join(EmailConfig.RECIPIENT_EMAILS)}")
    print(f"⏰ Heure d'envoi: {EmailConfig.REPORT_HOUR}")
    print(f"📁 Dossier données: {EmailConfig.DATA_DIR}")
    print("\n🔄 En attente...\n")
    
    schedule.every().day.at(EmailConfig.REPORT_HOUR).do(send_daily_report)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            test_email()
        elif command == 'now':
            send_daily_report()
        elif command == 'preview':
            analyses = get_latest_analyses(EmailConfig.DATA_DIR, hours=24)
            summary = get_market_summary(analyses)
            html = generate_html_report(analyses, summary)
            with open('/tmp/report_preview.html', 'w') as f:
                f.write(html)
            print(f"📄 Preview: /tmp/report_preview.html")
        else:
            print("Commandes: test | now | preview")
    else:
        run_scheduler()
