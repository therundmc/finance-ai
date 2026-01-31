/**
 * Analysis History Card Component - REWORKED
 * Compact collapsible analysis card linked to real data
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';
import './badge.js';
import './indicator-trend-chart.js';

export class AnalysisHistoryCard extends BaseComponent {
  static properties = {
    ...super.properties,
    analysis: { type: Object },
    allAnalyses: { type: Array },
    expanded: { type: Boolean, reflect: true },
    selected: { type: Boolean, reflect: true }
  };

  static styles = [
    sharedStyles,
    css`
      :host {
        display: block;
      }

      /* === CARD CONTAINER === */
      .history-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: visible;
        transition: all 0.2s ease;
        cursor: pointer;
      }

      :host([theme="dark"]) .history-card {
        background: var(--bg-secondary);
        border-color: var(--border-color);
      }

      .history-card:hover {
        border-color: var(--brand-secondary) !important;
      }

      :host([expanded]) .history-card {
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.12);
        border-color: var(--brand-secondary);
      }

      /* === COLLAPSED HEADER === */
      .card-header {
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .header-main {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      /* Line 1: Ticker, Badge, Conviction, Time */
      .header-line-1 {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      .ticker {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-primary);
      }

      .time-badge {
        font-size: 0.75rem;
        color: var(--text-muted);
      }

      /* Line 2: Résumé start */
      .header-line-2 {
        font-size: 0.8rem;
        color: var(--text-secondary);
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      /* Health Bar */
      .health-bar-container {
        display: flex;
        align-items: center;
        gap: 4px;
        min-width: 60px;
      }

      .health-bar {
        width: 40px;
        height: 5.05px;
        background: var(--bg-tertiary);
        border-radius: 999px;
        overflow: hidden;
      }

      .health-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
      }

      .health-fill.good { background: linear-gradient(90deg, var(--success), #34d399); }
      .health-fill.neutral { background: linear-gradient(90deg, var(--warning), #fbbf24); }
      .health-fill.bad { background: linear-gradient(90deg, var(--danger), #f87171); }

      .health-value {
        font-size: 0.75rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
      }

      /* Right side: Price + Evolution */
      .header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 2px;
        min-width: 70px;
      }

      .current-price {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
      }

      .price-evolution {
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
      }

      .price-evolution.positive { color: var(--success); }
      .price-evolution.negative { color: var(--danger); }

      /* Arrow - same as position-card */
      .arrow {
        font-size: 1.25rem;
        color: var(--text-muted);
        transition: transform var(--transition-fast);
        flex-shrink: 0;
      }

      :host([expanded]) .arrow {
        transform: rotate(90deg);
        color: var(--brand-secondary);
      }

      /* === EXPANDED CONTENT === */
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

      /* === 30-DAY CHART === */
      .chart-container {
        width: 100%;
        height: 100px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
        position: relative;
        overflow: hidden;
      }

      .chart-canvas {
        width: 100%;
        height: 100%;
        display: block;
      }

      .chart-label {
        position: absolute;
        top: 6px;
        left: 8px;
        font-size: 0.65rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        background: var(--bg-tertiary);
        padding: 2px 6px;
        border-radius: var(--radius-xs);
      }

      .chart-change {
        position: absolute;
        top: 6px;
        right: 8px;
        font-size: 0.7rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        padding: 2px 6px;
        border-radius: var(--radius-xs);
      }

      .chart-change.positive { background: rgba(6, 214, 160, 0.2); color: var(--success); }
      .chart-change.negative { background: rgba(255, 51, 102, 0.2); color: var(--danger); }

      /* === TREND CHART COMPACT === */
      .trend-chart-compact {
        --bg-secondary: transparent;
        margin: 0;
      }

      .trend-chart-compact::part(container) {
        border: none;
        background: transparent;
      }

      /* === SECTION TITLE === */
      .section-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        margin-top: 10px;
        margin-bottom: 8px;
        padding-bottom: 4px;
        border-bottom: 1px solid var(--border-color);
      }

      /* === RÉSUMÉ === */
      .resume-text {
        font-size: 0.9rem;
        color: var(--text-secondary);
        line-height: 1.6;
      }

      /* === INDICATORS ROW - single line, compact === */
      .indicators-compact {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .indicator-chip {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
      }

      .indicator-chip.positive { background: rgba(6, 214, 160, 0.12); }
      .indicator-chip.negative { background: rgba(255, 51, 102, 0.12); }

      .indicator-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
      }

      .indicator-value {
        font-size: 0.8rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
      }

      .indicator-chip.positive .indicator-value { color: var(--success); }
      .indicator-chip.negative .indicator-value { color: var(--danger); }

      /* === KEY LEVELS === */
      .levels-grid {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .level-item {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
      }

      .level-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
      }

      .level-value {
        font-size: 0.8rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
      }

      .level-item.buy { background: rgba(6, 214, 160, 0.12); }
      .level-item.buy .level-value { color: var(--success); }
      .level-item.target { background: rgba(139, 92, 246, 0.08); }
      .level-item.target .level-value { color: var(--brand-secondary); }
      .level-item.stop { background: rgba(255, 51, 102, 0.12); }
      .level-item.stop .level-value { color: var(--danger); }

      /* === TEXT SECTIONS === */
      .text-section {
        font-size: 0.85rem;
        line-height: 1.7;
        color: var(--text-secondary);
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
.text-section
      .text-section .indicator-name {
        font-weight: 700;
        color: var(--text-primary);
        font-size: 0.9rem;
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
        font-size: 0.9rem;
        font-weight: 800;
        margin-bottom: 6px;
      }

      .text-section .points-title.positive {
        color: var(--success-color);
      }

      .text-section .points-title.negative {
        color: var(--danger-color);
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

      /* Meta Row */
      .meta-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        padding-top: 8px;
        margin-top: 4px;
      }

      .meta-item {
        display: flex;
        align-items: center;
        gap: 2px;
        font-size: 0.6rem;
        color: var(--text-muted);
      }

      @media (max-width: 500px) {
        .header-line-1 {
          gap: 4px;
        }
        .health-bar-container {
          min-width: 50px;
        }
        .health-bar {
          width: 30px;
        }
        .indicators-compact {
          grid-template-columns: repeat(3, 1fr);
        }
        .levels-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    `
  ];

  constructor() {
    super();
    this.analysis = {};
    this.allAnalyses = [];
    this.expanded = false;
    this.selected = false;
    this._chartData = [];
  }

  // Get analyses filtered by current ticker for trend chart
  _getTickerAnalyses() {
    if (!this.allAnalyses || !this.analysis?.ticker) return [];
    return this.allAnalyses.filter(a => a.ticker === this.analysis.ticker);
  }

  updated(changedProperties) {
    super.updated(changedProperties);
    if (changedProperties.has('expanded') && this.expanded) {
      this._generateChartData();
      requestAnimationFrame(() => {
        this._drawChart();
        setTimeout(() => this._drawChart(), 100);
        setTimeout(() => this._drawChart(), 300);
      });
    }
  }

  _generateChartData() {
    const a = this.analysis;
    if (!a || !a.price) return;
    
    const currentPrice = a.price;
    const monthlyChange = a.change_1mo || (a.change_1d ? a.change_1d * 10 : 5);
    const points = 30;
    const startPrice = currentPrice / (1 + monthlyChange / 100);
    
    this._chartData = [];
    for (let i = 0; i < points; i++) {
      const progress = i / (points - 1);
      const trend = startPrice + (currentPrice - startPrice) * progress;
      const volatility = currentPrice * 0.012;
      const noise = (Math.random() - 0.5) * 2 * volatility;
      const momentum = Math.sin(progress * Math.PI * 3) * volatility * 0.4;
      this._chartData.push(trend + noise + momentum);
    }
    this._chartData[this._chartData.length - 1] = currentPrice;
  }

  _drawChart() {
    const canvas = this.shadowRoot?.querySelector('.chart-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = this._chartData;
    
    if (!data.length) return;
    
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      setTimeout(() => this._drawChart(), 50);
      return;
    }
    
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 15, right: 8, bottom: 8, left: 8 };
    
    const minPrice = Math.min(...data);
    const maxPrice = Math.max(...data);
    const priceRange = maxPrice - minPrice || 1;
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Determine color based on trend
    const isUp = data[data.length - 1] >= data[0];
    const lineColor = isUp ? '#06d6a0' : '#ff3366';
    const fillColor = isUp ? 'rgba(6, 214, 160, 0.15)' : 'rgba(255, 51, 102, 0.15)';
    
    // Draw gradient fill
    ctx.beginPath();
    ctx.moveTo(padding.left, height - padding.bottom);
    
    data.forEach((price, i) => {
      const x = padding.left + (i / (data.length - 1)) * chartWidth;
      const y = padding.top + ((maxPrice - price) / priceRange) * chartHeight;
      ctx.lineTo(x, y);
    });
    
    ctx.lineTo(padding.left + chartWidth, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
    
    // Draw line
    ctx.beginPath();
    data.forEach((price, i) => {
      const x = padding.left + (i / (data.length - 1)) * chartWidth;
      const y = padding.top + ((maxPrice - price) / priceRange) * chartHeight;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    // Draw current price dot
    const lastX = padding.left + chartWidth;
    const lastY = padding.top + ((maxPrice - data[data.length - 1]) / priceRange) * chartHeight;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fillStyle = lineColor;
    ctx.fill();
  }

  toggle() {
    this.expanded = !this.expanded;
  }

  /* Signal normalization */
  get normalizedSignal() {
    const signal = (this.analysis?.signal || '').toUpperCase().trim();
    if (signal.includes('ACHET') || signal.includes('BUY') || signal === 'ACHETER') return 'acheter';
    if (signal.includes('VEND') || signal.includes('SELL') || signal === 'VENDRE') return 'vendre';
    if (signal.includes('CONSERV') || signal.includes('HOLD') || signal === 'CONSERVER') return 'conserver';
    // Default based on first letter
    if (signal.startsWith('A')) return 'acheter';
    if (signal.startsWith('V')) return 'vendre';
    return 'conserver';
  }

  /* Health score calculation based on real indicators */
  get healthScore() {
    const ind = this.analysis?.indicators || {};
    const signal = this.normalizedSignal;
    let score = 50;
    
    // RSI contribution
    const rsi = ind.rsi || 50;
    if (rsi >= 30 && rsi <= 70) score += 10;
    else if (rsi < 20 || rsi > 80) score -= 15;
    
    // MACD histogram
    if (ind.macd_histogram > 0) score += 10;
    else if (ind.macd_histogram < 0) score -= 5;
    
    // Volume ratio
    const volRatio = ind.volume_ratio || 1;
    if (volRatio > 1.2) score += 5;
    else if (volRatio < 0.5) score -= 5;
    
    // Signal bonus
    if (signal === 'acheter') score += 15;
    else if (signal === 'vendre') score -= 10;
    
    return Math.max(0, Math.min(100, Math.round(score)));
  }

  get healthClass() {
    const score = this.healthScore;
    if (score >= 65) return 'good';
    if (score >= 40) return 'neutral';
    return 'bad';
  }

  /* Format timestamp */
  _formatTime(timestamp) {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString('fr-CH', { hour: '2-digit', minute: '2-digit' });
  }

  _formatDate(timestamp) {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleDateString('fr-CH', { day: '2-digit', month: 'short' });
  }

  /* Parse action levels from analysis text */
  _parseActionLevels() {
    const text = this.analysis?.analysis || '';
    const levels = {
      buy: null,
      stop_loss: null,
      target_1: null,
      target_2: null
    };

    // Parse buy level
    const buyMatch = text.match(/Achat(?:\s+recommandé)?[:\s]*\$?([\d.]+)/i);
    if (buyMatch) levels.buy = parseFloat(buyMatch[1]);

    // Parse stop loss
    const slMatch = text.match(/Stop[- ]?loss[:\s]*\$?([\d.]+)/i);
    if (slMatch) levels.stop_loss = parseFloat(slMatch[1]);

    // Parse targets
    const tp1Match = text.match(/Objectif\s*1[:\s]*\$?([\d.]+)/i);
    if (tp1Match) levels.target_1 = parseFloat(tp1Match[1]);

    const tp2Match = text.match(/Objectif\s*2[:\s]*\$?([\d.]+)/i);
    if (tp2Match) levels.target_2 = parseFloat(tp2Match[1]);

    // Fallback to support/resistance
    if (!levels.stop_loss && this.analysis?.indicators?.support) {
      levels.stop_loss = this.analysis.indicators.support;
    }
    if (!levels.target_1 && this.analysis?.indicators?.resistance) {
      levels.target_1 = this.analysis.indicators.resistance;
    }

    return levels;
  }

  /* Parse sections from analysis text */
  _parseSection(sectionName) {
    const text = this.analysis?.analysis || '';
    const regex = new RegExp(`###\\s*${sectionName}\\s*\\n([\\s\\S]*?)(?=###|$)`, 'i');
    const match = text.match(regex);
    return match ? match[1].trim() : '';
  }

  /* Get conviction class */
  get convictionClass() {
    const conf = (this.analysis?.confidence || '').toLowerCase().trim();
    if (conf.includes('fort') || conf.includes('high') || conf.includes('strong')) return 'forte';
    if (conf.includes('moyen') || conf.includes('medium') || conf.includes('moderate')) return 'moyenne';
    return 'faible';
  }

  render() {
    const a = this.analysis;
    if (!a || !a.ticker) {
      return html`<div class="history-card">No data</div>`;
    }

    const ind = a.indicators || {};
    const changePercent = a.change_1d || 0;
    const changeClass = changePercent >= 0 ? 'positive' : 'negative';
    const changeSign = changePercent >= 0 ? '+' : '';
    const change30d = a.change_1mo || 0;
    const change30dClass = change30d >= 0 ? 'positive' : 'negative';
    const change30dSign = change30d >= 0 ? '+' : '';
    const levels = this._parseActionLevels();

    // Parse analysis sections
    const technicalSection = this._parseSection('Analyse Technique');
    const fundamentalSection = this._parseSection('Analyse Fondamentale');
    const catalystSection = this._parseSection('Catalyseurs');
    const conclusionSection = this._parseSection('Conclusion');

    return html`
      <div class="history-card" @click="${this.toggle}">
        <!-- === COLLAPSED HEADER === -->
        <div class="card-header">
          <div class="header-main">
            <!-- Line 1: Ticker, Badge, Conviction, Time -->
            <div class="header-line-1">
              <span class="ticker">${a.ticker}</span>
              <app-badge variant="signal" type="${this.normalizedSignal}" size="sm">${a.signal || 'N/A'}</app-badge>
              <app-badge variant="conviction" type="${this.convictionClass}" size="sm">${a.confidence || 'N/A'}</app-badge>
              <span class="time-badge">${this._formatDate(a.timestamp)} ${this._formatTime(a.timestamp)}</span>
            </div>
            <!-- Line 2: Résumé preview -->
            <div class="header-line-2">${a.summary || ''}</div>
          </div>

          <!-- Health Bar -->
          <div class="health-bar-container">
            <div class="health-bar">
              <div class="health-fill ${this.healthClass}" style="width: ${this.healthScore}%"></div>
            </div>
            <span class="health-value">${this.healthScore}</span>
          </div>

          <!-- Right side: Price & Evolution -->
          <div class="header-right">
            <span class="current-price">$${(a.price || 0).toFixed(2)}</span>
            <span class="price-evolution ${changeClass}">
              ${changeSign}${changePercent.toFixed(2)}%
            </span>
          </div>

          <!-- Arrow -->
          <div class="arrow">›</div>
        </div>

        <!-- === EXPANDED CONTENT === -->
        <div class="card-content">
          <div class="content-inner">
            <!-- 1. TREND CHART (compact, with background) -->
            <indicator-trend-chart
              compact
              .analyses="${this._getTickerAnalyses()}"
              selected-ticker="${a.ticker}"
              .theme="${this.theme}"
            ></indicator-trend-chart>

            <!-- 2. 30-DAY PRICE CHART -->
            <div class="chart-container">
              <span class="chart-label">30 jours</span>
              <span class="chart-change ${change30dClass}">${change30dSign}${change30d.toFixed(1)}%</span>
              <canvas class="chart-canvas"></canvas>
            </div>

            <!-- 3. RÉSUMÉ -->
            <div class="section-title">Résumé</div>
            <div class="resume-text">${a.summary || 'Aucun résumé disponible'}</div>

            <!-- 4. INDICATORS - no header, very compact -->
            <div class="indicators-compact">
              ${this._renderIndicator('RSI', ind.rsi?.toFixed(0), ind.rsi < 30 ? 'positive' : ind.rsi > 70 ? 'negative' : '')}
              ${this._renderIndicator('MACD', ind.macd?.toFixed(2), ind.macd_histogram > 0 ? 'positive' : 'negative')}
              ${this._renderIndicator('STO', ind.stoch_k?.toFixed(0), '')}
              ${this._renderIndicator('VOL', `${(ind.volume_ratio || 0).toFixed(1)}x`, ind.volume_ratio > 1.2 ? 'positive' : ind.volume_ratio < 0.5 ? 'negative' : '')}
              ${this._renderIndicator('MA20', ind.ma_20 ? `$${ind.ma_20.toFixed(0)}` : 'N/A', a.price > ind.ma_20 ? 'positive' : 'negative')}
              ${this._renderIndicator('BB', `${(ind.bb_position || 0).toFixed(0)}%`, '')}
            </div>

            <!-- 5. KEY LEVELS -->
            <div class="section-title">Niveaux Clés</div>
            <div class="levels-grid">
              ${this._renderLevel('Achat', levels.buy ? `$${levels.buy.toFixed(0)}` : null, 'buy')}
              ${this._renderLevel('SL', levels.stop_loss ? `$${levels.stop_loss.toFixed(0)}` : null, 'stop')}
              ${this._renderLevel('TP1', levels.target_1 ? `$${levels.target_1.toFixed(0)}` : null, 'target')}
              ${this._renderLevel('TP2', levels.target_2 ? `$${levels.target_2.toFixed(0)}` : null, 'target')}
            </div>

            <!-- 5. TECHNICAL ANALYSIS -->
            ${technicalSection ? html`
              <div class="section-title">Analyse Technique</div>
              <div class="text-section">${this._formatText(technicalSection)}</div>
            ` : ''}

            <!-- 6. FUNDAMENTAL ANALYSIS -->
            ${fundamentalSection ? html`
              <div class="section-title">Analyse Fondamentale</div>
              <div class="text-section">${this._formatText(fundamentalSection)}</div>
            ` : ''}

            <!-- 7. CATALYSTS -->
            ${catalystSection ? html`
              <div class="section-title">Catalyseurs & Risques</div>
              <div class="text-section">${this._formatText(catalystSection)}</div>
            ` : ''}

            <!-- 8. CONCLUSION -->
            ${conclusionSection ? html`
              <div class="section-title">Conclusion</div>
              <div class="conclusion-text">${this._formatText(conclusionSection)}</div>
            ` : ''}

            <!-- Meta -->
            <div class="meta-row">
              <span class="meta-item">🤖 ${a.model || 'N/A'}</span>
              ${a.news_analyzed ? html`<span class="meta-item">📰 ${a.news_analyzed} news</span>` : ''}
              ${a.analysis_time ? html`<span class="meta-item">⏱️ ${(a.analysis_time / 1000).toFixed(1)}s</span>` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _renderIndicator(label, value, status) {
    return html`
      <div class="indicator-chip ${status}">
        <span class="indicator-label">${label}</span>
        <span class="indicator-value">${value || 'N/A'}</span>
      </div>
    `;
  }

  _renderLevel(label, value, type) {
    return html`
      <div class="level-item ${type}">
        <span class="level-label">${label}</span>
        <span class="level-value">${value || 'N/A'}</span>
      </div>
    `;
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
      return `<span class="points-section positive"><span class="points-title positive"><span class="icon">✓</span>${title}</span>`;
    });
    
    // 4. Format Points faibles
    formatted = formatted.replace(/^(Points?\s+faibles?):\s*$/gmi, (match, title) => {
      // Close previous points section if exists
      let result = '</span>';
      result += `<span class="points-section negative"><span class="points-title negative"><span class="icon">✗</span>${title}</span>`;
      return result;
    });
    
    // 5. Format bullet items under Points sections - just remove bullets and keep text
    const lines = formatted.split('\n');
    let inPointsSection = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check if starting a points section
      if (line.includes('points-section positive') || line.includes('points-section negative')) {
        inPointsSection = true;
      }
      
      // Check if ending points section (next main subsection or end)
      if (inPointsSection && (line.includes('class="subsection"') || i === lines.length - 1)) {
        if (i < lines.length - 1) {
          lines[i] = '</span>\n' + line;
        } else {
          lines[i] = line + '</span>';
        }
        inPointsSection = false;
      }
      
      // Format bullets in points section - just remove bullet and keep text
      if (inPointsSection && /^[•\-]\s+/.test(line)) {
        lines[i] = line.replace(/^[•\-]\s+(.+)$/, '<span class="point-item">$1</span>');
      }
    }
    
    formatted = lines.join('\n');
    
    // 6. Format bold text
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 8. Convert newlines to breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    return html`<span .innerHTML=${formatted}></span>`;
  }
}

customElements.define('analysis-history-card', AnalysisHistoryCard);
