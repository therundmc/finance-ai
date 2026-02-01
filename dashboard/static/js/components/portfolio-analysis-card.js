/**
 * Portfolio Analysis Card Component
 * Displays AI analysis of the entire portfolio
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';
import './badge.js';

export class PortfolioAnalysisCard extends BaseComponent {
  static properties = {
    ...super.properties,
    analysis: { type: Object },
    loading: { type: Boolean },
    expanded: { type: Boolean, reflect: true }
  };

  static styles = [
    sharedStyles,
    css`
      :host {
        display: block;
      }

      /* Card Container */
      .analysis-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        transition: all 0.2s ease;
      }

      .analysis-card:hover {
        border-color: var(--brand-secondary);
      }

      :host([expanded]) .analysis-card {
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.12);
        border-color: var(--brand-secondary);
      }

      /* Header */
      .card-header {
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        user-select: none;
      }

      .card-header:hover {
        background: var(--bg-tertiary);
      }

      .header-icon {
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
      }

      .header-main {
        flex: 1;
        min-width: 0;
      }

      .header-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 4px 0;
      }

      .header-subtitle {
        font-size: 0.75rem;
        color: var(--text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .health-score {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        background: var(--bg-tertiary);
        border-radius: 20px;
      }

      .health-bar {
        width: 40px;
        height: 5px;
        background: var(--bg-primary);
        border-radius: 999px;
        overflow: hidden;
      }

      .health-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
      }

      .health-fill.good { background: linear-gradient(90deg, var(--success), #34d399); }
      .health-fill.warning { background: linear-gradient(90deg, var(--warning), #fbbf24); }
      .health-fill.danger { background: linear-gradient(90deg, var(--danger), #f87171); }

      .health-value {
        font-size: 0.75rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
      }

      .expand-icon {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        color: var(--text-muted);
        transition: transform var(--transition-fast);
        flex-shrink: 0;
      }

      :host([expanded]) .expand-icon {
        transform: rotate(90deg);
        color: var(--brand-secondary);
      }

      /* Content */
      .card-content {
        display: none;
        padding: 0 12px 16px;
        animation: slideDown 0.3s ease-out;
      }

      :host([expanded]) .card-content {
        display: block;
      }

      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-8px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .content-inner {
        padding-top: 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      /* Sections */
      .section {
        padding: 0;
        background: transparent;
        border-radius: 0;
        margin-bottom: 0;
      }

      .section:last-child {
        margin-bottom: 0;
      }

      /* === SECTION TITLE === */
      .section-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        margin-top: 10px;
        margin-bottom: 8px;
        padding-bottom: 4px;
        border-bottom: 1px solid var(--border-color);
      }

      /* === TEXT SECTIONS === */
      .text-section {
        font-size: 0.85rem;
        color: var(--text-secondary);
        line-height: 1.7;
        padding: 0;
      }

      .text-section strong {
        color: var(--text-primary);
        font-weight: 700;
      }

      /* Main subsection (Tendance, Valorisation, etc.) */
      .text-section .subsection {
        display: block;
        font-size: 0.9rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-top: 12px;
        margin-bottom: 6px;
        padding-left: 8px;
        border-left: 3px solid var(--brand-secondary);
      }

      .text-section .subsection:first-child {
        margin-top: 0;
      }

      /* Technical indicators (RSI, MACD, Volatilité) */
      .text-section .indicator-line {
        display: block;
        margin: 6px 0;
        padding-left: 12px;
      }

      .text-section .indicator-name {
        font-weight: 700;
        color: var(--text-primary);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }

      .text-section .indicator-desc {
        color: var(--text-secondary);
        margin-left: 4px;
      }

      /* Points forts/faibles */
      .text-section .points-section {
        display: block;
        margin-top: 12px;
        margin-bottom: 8px;
      }

      .text-section .points-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        font-weight: 800;
        margin-bottom: 6px;
      }

      .text-section .points-title.positive {
        color: var(--success);
      }

      .text-section .points-title.negative {
        color: var(--danger);
      }

      .text-section .points-title .icon {
        font-size: 0.9rem;
        font-weight: 900;
      }

      .text-section .point-item {
        display: block;
        margin: 6px 0;
        line-height: 1.5;
      }

      .text-section p {
        margin: 6px 0;
      }

      /* === CONCLUSION === */
      .conclusion-text {
        font-size: 0.9rem;
        line-height: 1.7;
        border-radius: var(--radius-sm);
      }

      /* Actions List */
      .actions-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .action-item {
        padding: 8px 12px;
        font-size: 0.8rem;
        line-height: 1.4;
        border-left: 3px solid;
        background: var(--bg-tertiary);
      }

      .action-item.high {
        border-color: var(--danger);
      }

      .action-item.watch {
        border-color: var(--warning);
      }

      .action-item.opportunity {
        border-color: var(--success);
      }

      /* Meta badges */
      .meta-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        padding-top: 8px;
        margin-top: 4px;
      }

      .meta-badge {
        display: flex;
        align-items: center;
        gap: 2px;
        font-size: 0.6rem;
        color: var(--text-muted);
      }

      /* Loading State */
      .loading-state {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 30px;
      }

      .spinner {
        width: 24px;
        height: 24px;
        border: 3px solid var(--border-color);
        border-top-color: var(--brand-secondary);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }

      @keyframes spin {
        to { transform: rotate(360deg); }
      }

      /* Resume section */
      .resume-section {
        border-radius: var(--radius-sm);
        margin-bottom: 14px;
        font-size: 0.8rem;
        line-height: 1.5;
        color: var(--text-secondary);
      }

      /* Plan d'action - clean structured list */
      .plan-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .plan-step {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 12px;
        border-radius: var(--radius-sm);
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
      }

      .plan-num {
        flex-shrink: 0;
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 0.7rem;
        font-weight: 800;
        background: var(--brand-secondary);
        color: white;
      }

      .plan-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .plan-main {
        display: flex;
        align-items: baseline;
        gap: 6px;
        flex-wrap: wrap;
      }

      .plan-action-type {
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
        color: var(--text-primary);
      }

      .plan-ticker {
        font-weight: 800;
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
      }

      .plan-details {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
      }

      .plan-detail-item {
        display: flex;
        align-items: center;
        gap: 3px;
      }

      .plan-detail-label {
        font-weight: 600;
        color: var(--text-secondary);
      }

      .plan-reason {
        font-size: 0.75rem;
        color: var(--text-secondary);
        line-height: 1.4;
        margin-top: 2px;
      }

      /* Sell Recommendations */
      .sell-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .sell-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: rgba(255, 51, 102, 0.06);
        border-left: 3px solid var(--danger);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      }

      .sell-ticker {
        font-weight: 800;
        font-size: 0.9rem;
        color: var(--text-primary);
        min-width: 50px;
      }

      .sell-urgence {
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 10px;
        text-transform: uppercase;
        flex-shrink: 0;
        background: rgba(255, 51, 102, 0.15);
        color: var(--danger);
      }

      .sell-urgence.surveiller {
        background: rgba(255, 179, 71, 0.15);
        color: var(--warning, #f59e0b);
      }

      .sell-reason {
        font-size: 0.75rem;
        color: var(--text-secondary);
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .sell-price {
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        margin-left: auto;
      }

      /* Buy Recommendations */
      .buy-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .buy-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 10px 12px;
        background: rgba(6, 214, 160, 0.06);
        border-left: 3px solid var(--success);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      }

      .buy-item-header {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .buy-ticker {
        font-weight: 800;
        font-size: 0.95rem;
        color: var(--text-primary);
        min-width: 50px;
      }

      .buy-conviction {
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 10px;
        text-transform: uppercase;
        flex-shrink: 0;
      }

      .buy-conviction.forte {
        background: rgba(6, 214, 160, 0.15);
        color: var(--success);
      }

      .buy-conviction.moyenne {
        background: rgba(255, 179, 71, 0.15);
        color: var(--warning, #f59e0b);
      }

      .buy-reason {
        font-size: 0.75rem;
        color: var(--text-secondary);
        flex: 1;
        min-width: 0;
      }

      .buy-order-details {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        padding: 6px;
        background: var(--bg-primary);
        border-radius: var(--radius-sm);
      }

      .buy-detail-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .buy-detail-label {
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.3px;
      }

      .buy-detail-value {
        font-size: 0.8rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
      }

      .buy-detail-value.entry {
        color: var(--info, #3b82f6);
      }

      .buy-detail-value.sl {
        color: var(--danger);
      }

      .buy-detail-value.tp {
        color: var(--success);
      }

      .buy-detail-value.qty {
        color: var(--text-primary);
      }

      .buy-levels {
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        margin-left: auto;
      }

      /* Empty State */
      .empty-state {
        text-align: center;
        padding: 30px 20px;
        color: var(--text-muted);
      }

      .empty-icon {
        font-size: 2rem;
        margin-bottom: 10px;
        opacity: 0.5;
      }

      .empty-text {
        font-size: 0.85rem;
      }
    `
  ];

  constructor() {
    super();
    this.analysis = null;
    this.loading = false;
    this.expanded = false;
  }

  _toggle() {
    this.expanded = !this.expanded;
  }

  _getHealthClass(score) {
    if (!score && score !== 0) return 'warning';
    const n = parseFloat(score);
    if (n >= 70) return 'good';
    if (n >= 40) return 'warning';
    return 'danger';
  }

  _getActionColor(action) {
    const actionLower = (action || '').toLowerCase();
    if (actionLower.includes('vendre')) return { bg: 'rgba(239,68,68,0.15)', color: 'var(--danger)' };
    if (actionLower.includes('acheter')) return { bg: 'rgba(16,185,129,0.15)', color: 'var(--success)' };
    if (actionLower.includes('conserver')) return { bg: 'rgba(245,158,11,0.15)', color: 'var(--warning)' };
    if (actionLower.includes('surveiller')) return { bg: 'rgba(124,58,237,0.15)', color: 'var(--brand-secondary)' };
    if (actionLower.includes('alleger') || actionLower.includes('renforcer')) return { bg: 'rgba(59,130,246,0.15)', color: 'var(--info,#3b82f6)' };
    return { bg: 'var(--bg-tertiary)', color: 'var(--text-primary)' };
  }

  _formatText(text) {
    if (!text) return '';

    let formatted = text;

    // 1. Format main subsections (Tendance, Valorisation, etc.)
    formatted = formatted.replace(/^([A-Z][a-zé]+):\s*(.+)$/gm, (match, title, content) => {
      // Skip if it's an indicator line (RSI:, MACD:, etc.)
      if (['RSI', 'MACD', 'Volatilité', 'Volume', 'ADX', 'ATR', 'Stochastique'].includes(title)) {
        return match;
      }
      return `<span class="subsection">${title}</span>\n${content}`;
    });

    // 2. Format indicator lines (RSI:, MACD:, Volatilité:)
    formatted = formatted.replace(/^(RSI|MACD|Volatilité|Volume|ADX|ATR|Stochastique):\s*(.+)$/gm,
      '<span class="indicator-line"><span class="indicator-name">$1</span><span class="indicator-desc"> $2</span></span>');

    // 3. Format Points forts
    formatted = formatted.replace(/^(Points?\s+forts?):\s*$/gmi, (match, title) => {
      return `<span class="points-section"><span class="points-title positive"><span class="icon">✓</span>${title}</span>`;
    });

    // 4. Format Points faibles
    formatted = formatted.replace(/^(Points?\s+faibles?):\s*$/gmi, (match, title) => {
      return `<span class="points-section"><span class="points-title negative"><span class="icon">⚠</span>${title}</span>`;
    });

    // 5. Format bullet items under Points sections - just remove bullets and keep text
    const lines = formatted.split('\n');
    let inPointsSection = false;

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('points-section')) {
        inPointsSection = true;
      } else if (lines[i].includes('section-title') && !lines[i].includes('points-section')) {
        inPointsSection = false;
      } else if (inPointsSection && (lines[i].startsWith('- ') || lines[i].startsWith('• '))) {
        lines[i] = `<span class="point-item">${lines[i].substring(2)}</span>`;
      }
    }

    formatted = lines.join('\n');

    // 6. Format bold text
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 8. Convert newlines to breaks
    formatted = formatted.replace(/\n/g, '<br>');

    return html`<span .innerHTML=${formatted}></span>`;
  }

  _formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  render() {
    // Loading state
    if (this.loading) {
      return html`
        <div class="analysis-card">
          <div class="loading-state">
            <div class="spinner"></div>
          </div>
        </div>
      `;
    }

    // No data state
    if (!this.analysis) {
      return html`
        <div class="analysis-card">
          <div class="empty-state">
            <div class="empty-icon">🤖</div>
            <div class="empty-text">Analyse IA indisponible</div>
          </div>
        </div>
      `;
    }

    const {
      portfolio_state,
      portfolio_trend,
      health_score,
      resume_global = {},
      plan_action = [],
      ventes_recommandees = [],
      created_at
    } = this.analysis;

    const resume = resume_global.resume || '';

    const healthClass = this._getHealthClass(health_score);
    const healthPercent = health_score ? Math.min(100, Math.max(0, health_score)) : 50;

    return html`
      <div class="analysis-card">
        <div class="card-header" @click=${this._toggle}>
          <div class="header-icon"><img src="/static/assets/ai-assistant.png" alt="AI Assistant" style="height: 28px; width: 28px;"></div>
          <div class="header-main">
            <h3 class="header-title">Conseiller Financier</h3>
          </div>
          <div class="header-right">
            ${health_score != null ? html`
              <div class="health-score">
                <div class="health-bar">
                  <div class="health-fill ${healthClass}" style="width: ${healthPercent}%"></div>
                </div>
                <span class="health-value">${Math.round(health_score)}</span>
              </div>
            ` : ''}
            <div class="expand-icon">›</div>
          </div>
        </div>

        <div class="card-content">
          <div class="content-inner">
            <!-- Status badges -->
            ${portfolio_state || portfolio_trend ? html`
              <div class="meta-row">
                ${portfolio_state && portfolio_state !== 'N/A' ? html`
                  <span class="meta-badge">📊 ${portfolio_state}</span>
                ` : ''}
                ${portfolio_trend && portfolio_trend !== 'N/A' ? html`
                  <span class="meta-badge">📈 ${portfolio_trend}</span>
                ` : ''}
                ${created_at ? html`
                  <span class="meta-badge">🕒 ${this._formatDate(created_at)}</span>
                ` : ''}
              </div>
            ` : ''}

            <!-- Résumé -->
            ${resume ? html`
              <div class="resume-section">
                ${resume}
              </div>
            ` : ''}

            <!-- Plan d'action - structured steps -->
            ${plan_action.length ? html`
              <div class="section">
                <div class="section-title">Plan d'action</div>
                <div class="plan-list">
                  ${plan_action.map((step, i) => {
                    // Handle both new structured format and old string format
                    const isObject = typeof step === 'object' && step !== null;
                    const action = isObject ? step.action : '';
                    const tickers = isObject ? (step.tickers || []) : [];
                    const stopLoss = isObject ? step.stop_loss : null;
                    const takeProfit = isObject ? step.take_profit : null;
                    const nombreActions = isObject ? step.nombre_actions : null;
                    const raison = isObject ? step.raison : step;

                    const colors = this._getActionColor(action);

                    return html`
                      <div class="plan-step">
                        <span class="plan-num">${i + 1}</span>
                        <div class="plan-content">
                          <div class="plan-main">
                            ${isObject ? html`
                              <span class="plan-action-type" style="display:inline-block;padding:2px 8px;border-radius:4px;font-weight:800;background:${colors.bg};color:${colors.color};">
                                ${action}
                              </span>
                              ${tickers.length ? html`
                                <span class="plan-ticker">${tickers.join(', ')}</span>
                              ` : ''}
                            ` : html`
                              <span style="font-size:0.8rem;color:var(--text-secondary);">${step}</span>
                            `}
                          </div>
                          ${isObject && (stopLoss || takeProfit || nombreActions) ? html`
                            <div class="plan-details">
                              ${nombreActions ? html`<span class="plan-detail-item"><span class="plan-detail-label">Qté:</span> ${nombreActions}x</span>` : ''}
                              ${stopLoss ? html`<span class="plan-detail-item"><span class="plan-detail-label">SL:</span> ${stopLoss.toFixed(2)}$</span>` : ''}
                              ${takeProfit ? html`<span class="plan-detail-item"><span class="plan-detail-label">TP:</span> ${takeProfit.toFixed(2)}$</span>` : ''}
                            </div>
                          ` : ''}
                          ${isObject && raison ? html`
                            <div class="plan-reason">${raison}</div>
                          ` : ''}
                        </div>
                      </div>
                    `;
                  })}
                </div>
              </div>
            ` : ''}

            <!-- Ventes recommandées -->
            ${ventes_recommandees.length ? html`
              <div class="section">
                <div class="section-title">Ventes recommandées</div>
                <div class="sell-list">
                  ${ventes_recommandees.map(v => html`
                    <div class="sell-item">
                      <span class="sell-ticker">${v.ticker}</span>
                      <span class="sell-urgence ${(v.urgence || '').toLowerCase().replace(/\s+/g, '-')}">${v.urgence || ''}</span>
                      <span class="sell-reason" title="${v.raison || ''}">${v.raison || ''}</span>
                      ${v.prix_actuel ? html`<span class="sell-price">${v.prix_actuel}$</span>` : ''}
                    </div>
                  `)}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('portfolio-analysis-card', PortfolioAnalysisCard);
