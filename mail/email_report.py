"""
Système de rapport email quotidien - Finance AI Dashboard
Envoie le résumé du conseiller financier chaque matin à 8h
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
import schedule
import time
import sys

# Import database module - chemin partagé via volume Docker
sys.path.insert(0, '/app')
from database import get_latest_portfolio_analysis, get_latest_by_ticker, init_db

# Initialiser la base de données
init_db()


# ============================================
# CONFIGURATION
# ============================================
class EmailConfig:
    """Configuration email"""

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
# GÉNÉRATION DU RAPPORT HTML - PORTFOLIO ANALYSIS
# ============================================
def generate_portfolio_html_report(analysis: Dict) -> str:
    """Génère le rapport HTML basé sur l'analyse portfolio AI"""

    date_str = datetime.now().strftime('%A %d %B %Y')
    time_str = datetime.now().strftime('%H:%M')

    health_score = analysis.get('health_score', 50)
    portfolio_state = analysis.get('portfolio_state', 'N/A')
    portfolio_trend = analysis.get('portfolio_trend', 'N/A')
    resume_global = analysis.get('resume_global', {})
    resume_text = resume_global.get('resume', '')
    plan_action = analysis.get('plan_action', [])
    achats = analysis.get('achats_recommandes', [])
    ventes = analysis.get('ventes_recommandees', [])
    position_advice = analysis.get('position_advice', [])
    projections = analysis.get('projections', {})
    main_risk = analysis.get('main_risk', '')

    # Colors
    c = {
        'bg': '#fef7f3',
        'bg_alt': '#fef3ed',
        'bg_card': '#ffffff',
        'border': '#fde5d9',
        'text': '#1f1a16',
        'text_secondary': '#5c5046',
        'text_muted': '#9a8c80',
        'primary': '#ff3366',
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

    # Health color
    if health_score >= 70:
        health_color = c['success']
        health_bg = c['success_bg']
    elif health_score >= 40:
        health_color = c['warning']
        health_bg = c['warning_bg']
    else:
        health_color = c['danger']
        health_bg = c['danger_bg']

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conseiller Finance AI - {date_str}</title>
</head>
<body style="margin: 0; padding: 0; background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: {c['text']}; line-height: 1.5;">

    <div style="max-width: 600px; margin: 0 auto; padding: 12px;">

        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, #ff3366, #7c3aed); border-radius: 12px; padding: 20px 16px; margin-bottom: 12px; text-align: center;">
            <h1 style="margin: 0; color: #fff; font-size: 22px; font-weight: 800;">
                🤖 Finance AI
            </h1>
            <p style="margin: 6px 0 0; color: rgba(255,255,255,0.9); font-size: 12px; font-weight: 600;">
                {date_str}
            </p>
        </div>

        <!-- HEALTH SCORE -->
        <div style="background: {c['bg_card']}; border: 1px solid {c['border']}; border-left: 4px solid {health_color}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <h2 style="margin: 0; font-size: 16px; font-weight: 700; color: {c['text']};">
                    Santé {health_score}/100
                </h2>
                <div style="display: flex; gap: 4px;">
                    <span style="background: {health_bg}; color: {health_color}; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: 700;">{portfolio_state}</span>
                    <span style="background: {c['bg_alt']}; color: {c['text_secondary']}; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: 600;">{portfolio_trend}</span>
                </div>
            </div>

            <!-- Score bar -->
            <div style="background: {c['bg_alt']}; border-radius: 8px; height: 16px; overflow: hidden;">
                <div style="background: {health_color}; height: 100%; width: {min(100, max(0, health_score))}%; border-radius: 8px;"></div>
            </div>
"""

    # PROJECTIONS
    if projections:
        pnl_1w = projections.get('expected_pnl_1w', 0)
        pnl_1m = projections.get('expected_pnl_1m', 0)
        pnl_1y = projections.get('expected_pnl_1y', 0)

        html += f"""
            <div style="display: flex; gap: 6px; margin-top: 10px;">
                <div style="flex: 1; background: {c['bg_alt']}; border-radius: 6px; padding: 8px; text-align: center;">
                    <div style="font-size: 9px; color: {c['text_muted']}; font-weight: 600;">1 sem</div>
                    <div style="font-size: 16px; font-weight: 700; color: {c['success'] if pnl_1w >= 0 else c['danger']};">{'+' if pnl_1w >= 0 else ''}{pnl_1w:.1f}%</div>
                </div>
                <div style="flex: 1; background: {c['bg_alt']}; border-radius: 6px; padding: 8px; text-align: center;">
                    <div style="font-size: 9px; color: {c['text_muted']}; font-weight: 600;">1 mois</div>
                    <div style="font-size: 16px; font-weight: 700; color: {c['success'] if pnl_1m >= 0 else c['danger']};">{'+' if pnl_1m >= 0 else ''}{pnl_1m:.1f}%</div>
                </div>
                <div style="flex: 1; background: {c['bg_alt']}; border-radius: 6px; padding: 8px; text-align: center;">
                    <div style="font-size: 9px; color: {c['text_muted']}; font-weight: 600;">1 an</div>
                    <div style="font-size: 16px; font-weight: 700; color: {c['success'] if pnl_1y >= 0 else c['danger']};">{'+' if pnl_1y >= 0 else ''}{pnl_1y:.1f}%</div>
                </div>
            </div>
"""

    html += "        </div>"

    # RÉSUMÉ
    if resume_text:
        html += f"""
        <div style="background: {c['bg_card']}; border: 1px solid {c['border']}; border-left: 3px solid #7c3aed; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <div style="font-size: 13px; color: {c['text_secondary']}; line-height: 1.6;">{resume_text}</div>
        </div>
"""

    # PLAN D'ACTION
    if plan_action:
        html += f"""
        <div style="background: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            <h2 style="margin: 0 0 10px; font-size: 16px; font-weight: 700; color: {c['text']};">
                📋 Plan d'action
            </h2>
"""
        for i, step in enumerate(plan_action, 1):
            html += f"""
            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                <div style="flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%; background: #7c3aed; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #fff;">{i}</div>
                <div style="flex: 1; font-size: 13px; color: {c['text_secondary']}; line-height: 1.4;">{step}</div>
            </div>
"""
        html += "        </div>"

    # ACHATS RECOMMANDÉS
    if achats:
        html += f"""
        <div style="background: {c['bg_card']}; border: 1px solid {c['success_border']}; border-left: 3px solid {c['success']}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            <h2 style="margin: 0 0 10px; font-size: 16px; font-weight: 700; color: {c['success']};">
                🚀 Achats
            </h2>
"""
        for a in achats:
            ticker = a.get('ticker', '?')
            raison = a.get('raison', '')
            prix = a.get('prix_entree', '')
            sl = a.get('stop_loss', '')
            objectif = a.get('objectif', '')
            conviction = a.get('conviction', 'Moyenne')
            nombre_actions = a.get('nombre_actions', '')

            conv_color = c['success'] if conviction.lower() == 'forte' else c['warning']

            html += f"""
            <div style="background: {c['success_bg']}; border: 1px solid {c['success_border']}; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                    <span style="font-size: 16px; font-weight: 800; color: {c['text']};">{ticker}</span>
                    <span style="background: {conv_color}; color: #fff; padding: 2px 6px; border-radius: 10px; font-size: 9px; font-weight: 700;">{conviction}</span>
                    {f'<span style="background: {c["bg_alt"]}; color: {c["text_secondary"]}; padding: 2px 6px; border-radius: 10px; font-size: 9px; font-weight: 700;">{nombre_actions} actions</span>' if nombre_actions else ''}
                </div>
                <div style="font-size: 12px; color: {c['text_secondary']}; margin-bottom: 6px; line-height: 1.4;">
                    {raison[:120]}{'...' if len(raison) > 120 else ''}
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 11px; color: {c['text_muted']};">
                    {f'<span>Entrée: <strong>{prix}$</strong></span>' if prix else ''}
                    {f'<span>SL: <strong>{sl}$</strong></span>' if sl else ''}
                    {f'<span>TP: <strong>{objectif}$</strong></span>' if objectif else ''}
                </div>
            </div>
"""
        html += "        </div>"

    # VENTES RECOMMANDÉES
    if ventes:
        html += f"""
        <div style="background: {c['bg_card']}; border: 1px solid {c['danger_border']}; border-left: 3px solid {c['danger']}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            <h2 style="margin: 0 0 10px; font-size: 16px; font-weight: 700; color: {c['danger']};">
                🔻 Ventes
            </h2>
"""
        for v in ventes:
            vticker = v.get('ticker', '?')
            vraison = v.get('raison', '')
            vprix = v.get('prix_actuel', '')
            vurgence = v.get('urgence', '')

            html += f"""
            <div style="background: {c['danger_bg']}; border: 1px solid {c['danger_border']}; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                    <span style="font-size: 16px; font-weight: 800; color: {c['text']};">{vticker}</span>
                    <span style="background: {c['danger']}; color: #fff; padding: 2px 6px; border-radius: 10px; font-size: 9px; font-weight: 700;">{vurgence}</span>
                    {f'<span style="margin-left: auto; font-size: 13px; font-weight: 600; color: {c["text_secondary"]};">{vprix}$</span>' if vprix else ''}
                </div>
                <div style="font-size: 12px; color: {c['text_secondary']}; line-height: 1.4;">{vraison[:120]}{'...' if len(vraison) > 120 else ''}</div>
            </div>
"""
        html += "        </div>"

    # POSITION ADVICE (compact table)
    if position_advice:
        html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['border']}; border-top: 4px solid #7c3aed; border-radius: 20px; padding: 32px; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(124, 58, 237, 0.08);">
            <h2 style="margin: 0 0 24px; font-size: 22px; font-weight: 800; color: {c['text']};">
                📊 Conseils par Position
            </h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="border-bottom: 3px solid {c['border']};">
                        <th style="text-align: left; padding: 12px 8px; color: {c['text_secondary']}; font-weight: 800; font-size: 10px; text-transform: uppercase;">Ticker</th>
                        <th style="text-align: center; padding: 12px 8px; color: {c['text_secondary']}; font-weight: 800; font-size: 10px; text-transform: uppercase;">Action</th>
                        <th style="text-align: center; padding: 12px 8px; color: {c['text_secondary']}; font-weight: 800; font-size: 10px; text-transform: uppercase;">Urgence</th>
                        <th style="text-align: left; padding: 12px 8px; color: {c['text_secondary']}; font-weight: 800; font-size: 10px; text-transform: uppercase;">Conseil</th>
                    </tr>
                </thead>
                <tbody>
"""
        for pa in position_advice:
            action_str = pa.get('action', '').upper()
            if 'VENDRE' in action_str or 'SELL' in action_str:
                action_color = c['danger']
            elif 'ACHETER' in action_str or 'RENFORCER' in action_str or 'BUY' in action_str:
                action_color = c['success']
            else:
                action_color = c['warning']

            urgence = pa.get('urgence', 'Normale')
            urgence_color = c['danger'] if urgence.lower() in ['haute', 'urgente', 'critique'] else c['text_muted']

            html += f"""
                    <tr style="border-bottom: 1px solid {c['border']};">
                        <td style="padding: 12px 8px; font-weight: 800; color: {c['text']};">{pa.get('ticker', '?')}</td>
                        <td style="text-align: center; padding: 12px 8px;">
                            <span style="color: {action_color}; font-weight: 700; font-size: 11px;">{pa.get('action', '-')}</span>
                        </td>
                        <td style="text-align: center; padding: 12px 8px; color: {urgence_color}; font-weight: 700; font-size: 11px;">{urgence}</td>
                        <td style="padding: 12px 8px; color: {c['text_secondary']}; font-size: 12px;">{pa.get('conseil', '')}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""

    # RISKS
    if main_risk:
        html += f"""
        <div style="background: {c['bg_card']}; border: 2px solid {c['danger_border']}; border-radius: 20px; padding: 24px; margin-bottom: 28px;">
            <div style="font-size: 14px; font-weight: 700; color: {c['danger']}; margin-bottom: 8px;">⚠️ Risque principal</div>
            <div style="font-size: 14px; color: {c['text_secondary']};">{main_risk}</div>
        </div>
"""

    # FOOTER
    html += f"""
        <div style="text-align: center; padding: 32px 20px; margin-top: 16px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #ff3366, #7c3aed); padding: 2px; border-radius: 12px;">
                <div style="background: {c['bg']}; border-radius: 10px; padding: 16px 28px;">
                    <p style="margin: 0; color: {c['text']}; font-size: 14px; font-weight: 600;">
                        Rapport généré par <span style="background: linear-gradient(135deg, #ff3366, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">Finance AI</span>
                    </p>
                    <p style="margin: 8px 0 0; font-size: 13px; color: {c['text_muted']};">
                        Made with ❤️ by Anca
                    </p>
                </div>
            </div>
        </div>

    </div>
</body>
</html>
"""

    return html


# ============================================
# LEGACY REPORT (fallback)
# ============================================
def _generate_legacy_html_report() -> Optional[str]:
    """Fallback: per-stock report if no portfolio analysis available"""
    latest_dict = get_latest_by_ticker(hours=24)
    if not latest_dict:
        return None

    analyses = sorted(latest_dict.values(), key=lambda x: x.get('change_1d', 0), reverse=True)

    date_str = datetime.now().strftime('%A %d %B %Y')
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; padding: 20px; background: #f8f9fa;">
<div style="max-width: 600px; margin: 0 auto;">
<h1 style="color: #ff3366;">Finance AI - {date_str}</h1>
<p>{len(analyses)} analyses disponibles (fallback mode)</p>
<table style="width:100%; border-collapse: collapse;">
<tr style="background:#eee;"><th style="padding:8px;text-align:left;">Ticker</th><th>Signal</th><th>Prix</th><th>24h</th></tr>"""

    for a in analyses:
        signal = a.get('signal', 'N/A')
        color = '#06d6a0' if 'ACHAT' in signal.upper() else '#ff3366' if 'VENT' in signal.upper() else '#999'
        html += f"""<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px;font-weight:700;">{a['ticker']}</td>
<td style="text-align:center;color:{color};font-weight:700;">{signal}</td>
<td style="text-align:right;">${a.get('price', 0):.2f}</td>
<td style="text-align:right;color:{'#06d6a0' if a.get('change_1d', 0) >= 0 else '#ff3366'}">{a.get('change_1d', 0):+.2f}%</td>
</tr>"""

    html += "</table></div></body></html>"
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
    """Génère et envoie le rapport quotidien basé sur l'analyse portfolio"""
    print(f"\n{'='*50}")
    print(f"📧 Génération du rapport - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    date_str = datetime.now().strftime('%d/%m/%Y')
    recipients = [r.strip() for r in EmailConfig.RECIPIENT_EMAILS if r.strip()]

    # Try portfolio analysis first
    analysis = get_latest_portfolio_analysis()

    if analysis:
        print(f"📊 Analyse portfolio trouvée (score: {analysis.get('health_score', '?')}/100)")

        achats = analysis.get('achats_recommandes', [])
        health_score = analysis.get('health_score', 50)

        html_report = generate_portfolio_html_report(analysis)

        n_achats = len(achats)
        subject = f"Finance AI | {date_str} | Santé: {health_score}/100 | {n_achats} achat(s) recommandé(s)"

        return send_email(subject=subject, html_content=html_report, recipients=recipients)

    # Fallback to legacy per-stock report
    print("⚠️ Pas d'analyse portfolio, fallback vers rapport legacy")
    legacy_html = _generate_legacy_html_report()

    if legacy_html:
        subject = f"Finance AI | {date_str} | Rapport (legacy)"
        return send_email(subject=subject, html_content=legacy_html, recipients=recipients)

    print("⚠️ Aucune analyse trouvée pour le rapport")
    return False


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
            analysis = get_latest_portfolio_analysis()
            if analysis:
                html = generate_portfolio_html_report(analysis)
            else:
                html = _generate_legacy_html_report() or '<p>No data</p>'
            with open('/tmp/report_preview.html', 'w') as f:
                f.write(html)
            print(f"📄 Preview: /tmp/report_preview.html")
        else:
            print("Commandes: test | now | preview")
    else:
        run_scheduler()
