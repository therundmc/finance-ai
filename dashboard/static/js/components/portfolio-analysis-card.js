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
        font-size: 0.85rem;
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
        font-size: 0.95rem;
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
        color: var(--text-secondary);
        line-height: 1.7;
        padding: 12px;
        background: rgba(139, 92, 246, 0.05);
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
      summary,
      actions_high_priority = [],
      actions_watch = [],
      actions_opportunities = [],
      conclusion,
      allocation_comment,
      main_risk,
      created_at 
    } = this.analysis;

    const healthClass = this._getHealthClass(health_score);
    const healthPercent = health_score ? Math.min(100, Math.max(0, health_score)) : 50;

    return html`
      <div class="analysis-card">
        <div class="card-header" @click=${this._toggle}>
          <div class="header-icon">🤖</div>
          <div class="header-main">
            <h3 class="header-title">Analyse du Portefeuille</h3>
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

            <!-- Summary -->
            ${summary ? html`
              <div class="section">
                <div class="section-title">Résumé</div>
                <div class="text-section">${summary}</div>
              </div>
            ` : ''}

            <!-- Actions -->
            ${(actions_high_priority.length || actions_watch.length || actions_opportunities.length) ? html`
              <div class="section">
                <div class="section-title">Actions recommandées</div>
                <div class="actions-list">
                  ${actions_high_priority.map(action => html`
                    <div class="action-item high">🚨 ${action}</div>
                  `)}
                  ${actions_watch.map(action => html`
                    <div class="action-item watch">👁️ ${action}</div>
                  `)}
                  ${actions_opportunities.map(action => html`
                    <div class="action-item opportunity">💡 ${action}</div>
                  `)}
                </div>
              </div>
            ` : ''}

            <!-- Risk -->
            ${main_risk ? html`
              <div class="section">
                <div class="section-title">Risque principal</div>
                <div class="text-section">${this._formatText(main_risk)}</div>
              </div>
            ` : ''}

            <!-- Allocation -->
            ${allocation_comment ? html`
              <div class="section">
                <div class="section-title">Allocation</div>
                <div class="text-section">${this._formatText(allocation_comment)}</div>
              </div>
            ` : ''}

            <!-- Conclusion -->
            ${conclusion ? html`
              <div class="section">
                <div class="section-title">Conclusion</div>
                <div class="conclusion-text">${this._formatText(conclusion)}</div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('portfolio-analysis-card', PortfolioAnalysisCard);
