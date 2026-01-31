/**
 * Position Card Component
 * Displays a position with expandable details including:
 * - Intraday chart
 * - P&L breakdown (Net, Brut, Frais)
 * Matches original app theme (variables.css)
 * 
 * Usage:
 * <position-card
 *   .position=${positionObject}
 *   expanded
 *   theme="light|dark"
 *   @select=${handleSelect}
 *   @edit=${handleEdit}
 *   @close=${handleClose}
 *   @delete=${handleDelete}
 * ></position-card>
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';
import './button.js';
import './badge.js';

export class PositionCard extends BaseComponent {
  static properties = {
    ...super.properties,
    position: { type: Object },
    expanded: { type: Boolean, reflect: true },
    selected: { type: Boolean, reflect: true },
    currency: { type: String },
    hideValues: { type: Boolean, attribute: 'hide-values' },
    aiAdvice: { type: Object },
    _editingTarget: { type: String, state: true }
  };

  static styles = [
    sharedStyles,
    css`
      :host {
        display: block;
      }

      .position-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
      }

      :host([theme="dark"]) .position-card {
        background: var(--bg-secondary);
        border-color: var(--border-color);
      }

      .position-card::before {
        display: none;
      }

      .position-card:hover {
        border-color: var(--brand-secondary) !important;
      }

      :host([selected]) .position-card {
        border-color: var(--brand-primary);
        background: var(--bg-hover);
      }

      :host([expanded]) .position-card {
        box-shadow: var(--shadow-md);
        border-color: var(--brand-secondary);
      }

      /* Header */
      .card-header {
        display: flex;
        align-items: center;
        padding: 12px 14px;
        gap: 12px;
      }

      .header-left {
        flex: 1;
        min-width: 0;
      }

      .ticker-row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      .ticker {
        font-size: 1rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: 0.5px;
      }

      .market-status {
        display: inline-flex;
        align-items: center;
      }

      .market-status .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        animation: pulse-dot 2s infinite;
      }

      .market-status.open .status-dot {
        background: var(--success);
      }

      .market-status.extended .status-dot {
        background: var(--warning);
      }

      .market-status.closed .status-dot {
        background: var(--text-muted);
        animation: none;
      }

      @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
      }

      .days-held {
        font-size: 0.7rem;
        color: var(--text-muted);
        font-weight: 500;
      }

      .summary {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
      }

      /* P&L Section */
      .header-right {
        text-align: right;
        flex-shrink: 0;
      }

      .pnl-value {
        font-size: 1rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
      }

      .pnl-value.positive {
        background: linear-gradient(90deg, #06d6a0, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      .pnl-value.negative {
        background: linear-gradient(90deg, #ff3366, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .pnl-percent {
        font-size: 0.75rem;
        font-weight: 600;
      }

      .pnl-percent.positive { color: var(--success); }
      .pnl-percent.negative { color: var(--danger); }

      .current-price {
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 2px;
        font-family: 'JetBrains Mono', monospace;
      }

      /* Arrow */
      .arrow {
        font-size: 1.2rem;
        color: var(--text-muted);
        transition: transform var(--transition-fast);
        flex-shrink: 0;
      }

      :host([expanded]) .arrow {
        transform: rotate(90deg);
        color: var(--brand-secondary);
      }

      /* Expanded Content */
      .card-content {
        display: none;
        padding: 6px 12px 16px;
        border-top: 1px solid var(--border-color);
        animation: slideDown 0.3s ease-out;
      }

      :host([expanded]) .card-content {
        display: block;
      }

      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      /* Intraday Chart */
      .chart-section {
        padding: 12px 0;
        border-bottom: 1px solid var(--border-color);
      }

      .chart-container {
        height: 100px;
        background: var(--bg-tertiary);
        border-radius: 8px;
        position: relative;
        overflow: hidden;
      }

      .chart-canvas {
        width: 100%;
        height: 100%;
      }

      .chart-info {
        position: absolute;
        top: 6px;
        left: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
        z-index: 1;
      }

      .chart-label {
        font-size: 0.6rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .chart-percent {
        font-size: 0.7rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
      }

      .chart-percent.positive { color: var(--success); }
      .chart-percent.negative { color: var(--danger); }

      .chart-range {
        display: flex;
        justify-content: space-between;
        margin-top: 6px;
        padding: 0 4px;
      }

      .range-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .range-label {
        font-size: 0.55rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
      }

      .range-value {
        font-size: 0.65rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
      }

      .range-value.high { color: var(--success); }
      .range-value.low { color: var(--danger); }

      .no-chart {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--text-muted);
        font-size: 0.75rem;
      }

      /* P&L Breakdown */
      .pnl-breakdown {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        padding: 12px 0;
        border-bottom: 1px solid var(--border-color);
      }

      .pnl-item {
        text-align: center;
        padding: 10px 8px;
        background: var(--bg-tertiary);
        border-radius: 8px;
      }

      .pnl-item-label {
        font-size: 0.6rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 4px;
      }

      .pnl-item-value {
        font-size: 0.95rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
      }

      .pnl-item-value.positive { color: var(--success); }
      .pnl-item-value.negative { color: var(--danger); }
      .pnl-item-value.neutral { color: var(--text-secondary); }

      /* Stats Grid */
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        padding: 12px 0;
      }

      .stat-item {
        background: var(--bg-tertiary);
        padding: 10px;
        border-radius: 8px;
        text-align: center;
      }

      .stat-label {
        font-size: 0.6rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 4px;
      }

      .stat-value {
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--text-primary);
      }

      /* Targets Bar */
      .targets-section {
        padding: 12px 0;
        border-bottom: 1px solid var(--border-color);
      }

      .targets-header {
        font-size: 0.65rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
      }

      .targets-bar {
        height: 8px;
        background: linear-gradient(90deg, var(--danger) 0%, var(--brand-secondary) 50%, var(--success) 100%);
        border-radius: 4px;
        position: relative;
        opacity: 0.7;
      }

      /* Reference markers for targets */
      .target-reference {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 2px;
        background: rgba(255, 255, 255, 0.3);
        z-index: 1;
      }

      .targets-marker {
        position: absolute;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 16px;
        height: 16px;
        background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        z-index: 2;
      }

      /* Target reached states */
      .targets-marker.sl-reached {
        background: linear-gradient(135deg, var(--danger), #ff0033);
        box-shadow: 0 0 16px rgba(255, 51, 102, 0.8);
        animation: pulse-danger 2s infinite;
      }

      .targets-marker.tp1-reached {
        background: linear-gradient(135deg, var(--brand-secondary), var(--brand-primary));
        box-shadow: 0 0 16px rgba(124, 58, 237, 0.8);
        animation: pulse-success 2s infinite;
      }

      .targets-marker.tp2-reached {
        background: linear-gradient(135deg, var(--success), #00ff88);
        box-shadow: 0 0 16px rgba(6, 214, 160, 0.8);
        animation: pulse-success 2s infinite;
      }

      @keyframes pulse-danger {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.2); }
      }

      @keyframes pulse-success {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.2); }
      }

      .targets-labels {
        position: relative;
        margin-top: 12px;
        height: 40px;
        font-size: 0.65rem;
        font-family: 'JetBrains Mono', monospace;
      }

      .target-label {
        position: absolute;
        transform: translateX(-50%);
        text-align: center;
        padding: 4px 6px;
        border-radius: 6px;
        transition: all 0.3s ease;
        white-space: nowrap;
      }

      .target-label.sl { 
        color: var(--danger);
        left: 0%;
        transform: translateX(0);
      }
      
      .target-label.tp1 { 
        color: var(--brand-secondary); 
      }
      
      .target-label.tp2 { 
        color: var(--success);
        left: 100%;
        transform: translateX(-100%);
      }

      .target-label.reached {
        background: rgba(255, 255, 255, 0.1);
        font-weight: 900;
        transform: scale(1.05);
      }

      .target-label.sl.reached {
        background: rgba(255, 51, 102, 0.2);
        box-shadow: 0 0 12px rgba(255, 51, 102, 0.4);
      }

      .target-label.tp1.reached {
        background: rgba(124, 58, 237, 0.2);
        box-shadow: 0 0 12px rgba(124, 58, 237, 0.4);
      }

      .target-label.tp2.reached {
        background: rgba(6, 214, 160, 0.2);
        box-shadow: 0 0 12px rgba(6, 214, 160, 0.4);
      }

      .target-name {
        display: block;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }

      .target-price {
        font-size: 0.85rem;
        font-weight: 600;
        color: inherit;
      }

      /* Actions */
      .actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding-top: 12px;
      }

      /* AI Advice Section */
      .ai-advice {
        padding: 8px 8px 8px 8px;
        background: rgba(124, 58, 237, 0.08);
        border-radius: var(--radius-sm);
        margin-bottom: 0px;
      }

      .ai-advice-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 6px;
      }

      .ai-advice-icon {
        font-size: 0.9rem;
      }

      .ai-advice-label {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--brand-secondary);
        letter-spacing: 0.5px;
      }

      .ai-advice-action {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: auto;
      }

      .ai-advice-action.buy {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success);
      }

      .ai-advice-action.sell {
        background: rgba(239, 68, 68, 0.15);
        color: var(--danger);
      }

      .ai-advice-action.hold,
      .ai-advice-action.keep,
      .ai-advice-action.conserver {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning);
      }

      .ai-advice-action.watch,
      .ai-advice-action.surveiller {
        background: rgba(124, 58, 237, 0.15);
        color: var(--brand-secondary);
      }

      .ai-advice-text {
        font-size: 0.85rem;
        color: var(--text-secondary);
        line-height: 1.4;
      }

      .ai-advice-level {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 4px;
      }
    `
  ];

  constructor() {
    super();
    this.position = {};
    this.expanded = false;
    this.selected = false;
    this.currency = 'USD';  // Display currency (for reference only)
    this.hideValues = false;
    this.aiAdvice = null;
    this._chartData = [];
    this._editingTarget = null;
  }

  // Get market currency based on ticker suffix
  get marketCurrency() {
    const ticker = this.position?.ticker || '';
    if (ticker.endsWith('.SW') || ticker.endsWith('.VX')) return 'CHF';
    if (ticker.endsWith('.PA') || ticker.endsWith('.DE') || ticker.endsWith('.AS')) return 'EUR';
    if (ticker.endsWith('.L')) return 'GBP';
    return 'USD';
  }

  // Use market currency for all price displays
  get currencySymbol() {
    const symbols = { USD: '$', EUR: '€', CHF: 'CHF ', GBP: '£' };
    return symbols[this.marketCurrency] || '$';
  }

  get marketStatus() {
    const p = this.position;
    const liveData = p.live_data || {};
    const market = liveData.market || {};
    
    if (market.is_open) {
      return { status: 'open', label: 'Ouvert', icon: '🟢' };
    } else if (market.is_extended) {
      return { status: 'extended', label: 'Extended', icon: '🟡' };
    } else {
      return { status: 'closed', label: 'Fermé', icon: '🔴' };
    }
  }

  // CHF to other currency conversion rates (approximate)
  static CHF_RATES = {
    'USD': 1.13,
    'EUR': 1.05,
    'GBP': 0.89,
    'CHF': 1.0
  };

  get pnlData() {
    const p = this.position;
    const liveData = p.live_data || {};
    const currentPrice = liveData.price || p.current_price || p.exit_price || p.entry_price || 0;
    const quantity = p.quantity || 1;
    const entryPrice = p.entry_price || 0;
    
    // Commissions/fees - use commission_native from backend (already converted to market currency)
    // Fallback to CHF commission with conversion if not available
    const buyComm = p.buy_commission || 0;
    const sellComm = p.sell_commission || 0;
    const totalFeesChf = buyComm + sellComm;
    
    // Prefer backend-calculated commission in native market currency
    let totalFees = totalFeesChf;
    if (liveData.pnl && liveData.pnl.commission_native !== undefined) {
      // Use pre-calculated commission in stock's market currency from API
      totalFees = liveData.pnl.commission_native;
    } else {
      // Fallback: convert CHF to market currency using approximate rates
      const rate = PositionCard.CHF_RATES[this.marketCurrency] || 1.0;
      totalFees = totalFeesChf * rate;
    }
    
    let pnlValue, pnlPercent, pnlGross;
    
    if (liveData.pnl) {
      pnlValue = liveData.pnl.pnl_net;
      pnlPercent = liveData.pnl.pnl_percent;
      pnlGross = liveData.pnl.pnl_gross || (pnlValue + totalFees);
    } else if (p.pnl_value !== undefined) {
      pnlValue = p.pnl_value;
      pnlPercent = p.pnl_percent || 0;
      pnlGross = p.pnl_gross || (pnlValue + totalFees);
    } else {
      const exitPrice = p.exit_price || currentPrice;
      const invested = entryPrice * quantity;
      const currentValue = exitPrice * quantity;
      pnlGross = currentValue - invested;
      pnlValue = pnlGross - totalFees;
      pnlPercent = invested > 0 ? (pnlValue / invested * 100) : 0;
    }
    
    return {
      value: pnlValue || 0,
      percent: pnlPercent || 0,
      gross: pnlGross || 0,
      fees: totalFees,
      isProfit: (pnlValue || 0) >= 0,
      currentPrice,
      invested: entryPrice * quantity,
      currentValue: currentPrice * quantity
    };
  }

  get priceChange() {
    const p = this.position;
    const liveData = p.live_data || {};
    
    // Daily change from live data
    const change = liveData.change || p.daily_change || 0;
    const changePercent = liveData.change_percent || p.daily_change_percent || 0;
    
    return {
      value: change,
      percent: changePercent,
      isPositive: change >= 0
    };
  }

  get daysHeld() {
    const p = this.position;
    if (!p.entry_date) return 0;
    return Math.floor((new Date() - new Date(p.entry_date)) / (1000 * 60 * 60 * 24));
  }

  get alertType() {
    const p = this.position;
    const currentPrice = this.pnlData.currentPrice;
    
    if (p.status !== 'open' || !currentPrice) return null;
    
    if (p.stop_loss && currentPrice <= p.stop_loss) return 'sl';
    if (p.take_profit_2 && currentPrice >= p.take_profit_2) return 'tp2';
    if (p.take_profit_1 && currentPrice >= p.take_profit_1) return 'tp1';
    
    return null;
  }

  get markerPosition() {
    const p = this.position;
    const currentPrice = this.pnlData.currentPrice;
    const entry = p.entry_price || currentPrice;
    const sl = p.stop_loss || entry * 0.95;
    const tp1 = p.take_profit_1 || entry * 1.05;
    const tp2 = p.take_profit_2 || tp1 * 1.05;
    
    // Calculate position on bar (0-100%)
    // Bar layout: SL (0%) --- Entry (center) --- TP1 (center-right) --- TP2 (100%)
    const totalRange = tp2 - sl;
    if (totalRange <= 0) return 50; // Fallback
    
    const position = ((currentPrice - sl) / totalRange) * 100;
    
    // Clamp between 2% and 98% for visibility
    return Math.max(2, Math.min(98, position));
  }

  // Calculate where entry price should appear on the bar
  get entryPosition() {
    const p = this.position;
    const entry = p.entry_price || this.pnlData.currentPrice;
    const sl = p.stop_loss || entry * 0.95;
    const tp2 = p.take_profit_2 || entry * 1.1;
    const totalRange = tp2 - sl;
    if (totalRange <= 0) return 50;
    return ((entry - sl) / totalRange) * 100;
  }

  // Calculate where TP1 should appear on the bar  
  get tp1Position() {
    const p = this.position;
    const entry = p.entry_price || this.pnlData.currentPrice;
    const sl = p.stop_loss || entry * 0.95;
    const tp1 = p.take_profit_1 || entry * 1.05;
    const tp2 = p.take_profit_2 || entry * 1.1;
    const totalRange = tp2 - sl;
    if (totalRange <= 0) return 75;
    return ((tp1 - sl) / totalRange) * 100;
  }

  get intradayData() {
    const p = this.position;
    // API returns chart data in live_data.chart
    return p.live_data?.chart || p.live_data?.intraday || p.intraday || p.chart || [];
  }

  get dayRange() {
    const p = this.position;
    const liveData = p.live_data || {};
    return {
      high: liveData.high || null,
      low: liveData.low || null
    };
  }

  updated(changedProperties) {
    if (changedProperties.has('expanded') && this.expanded) {
      // Use requestAnimationFrame to ensure DOM is ready
      requestAnimationFrame(() => {
        this._drawChart();
      });
    }
    // Also redraw when position data changes (live data update)
    if (changedProperties.has('position') && this.expanded) {
      requestAnimationFrame(() => {
        this._drawChart();
      });
    }
  }

  _drawChart() {
    const canvas = this.shadowRoot?.querySelector('.chart-canvas');
    if (!canvas) {
      console.log('Chart canvas not found');
      return;
    }
    
    const ctx = canvas.getContext('2d');
    const data = this.intradayData;
    
    if (!data.length) {
      console.log('No intraday data available');
      return;
    }
    
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      // Canvas not visible yet, retry
      setTimeout(() => this._drawChart(), 50);
      return;
    }
    
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 10, bottom: 10, left: 10 };
    
    const prices = data.map(d => d.price || d.close || d);
    let minPrice = Math.min(...prices);
    let maxPrice = Math.max(...prices);
    
    // Add 10% padding to price range for better visualization
    const pricePadding = (maxPrice - minPrice) * 0.1 || 0.5;
    minPrice -= pricePadding;
    maxPrice += pricePadding;
    const priceRange = maxPrice - minPrice || 1;
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Use the same change percent logic as displayed in the UI
    // This ensures chart color matches the percent shown
    const liveData = this.position?.live_data || {};
    const changePercent = liveData.change_percent || this.position?.daily_change_percent || 0;
    const isUp = changePercent >= 0;
    const lineColor = isUp ? '#06d6a0' : '#ff3366';
    const fillColor = isUp ? 'rgba(6, 214, 160, 0.1)' : 'rgba(255, 51, 102, 0.1)';
    
    // Draw gradient fill
    ctx.beginPath();
    ctx.moveTo(padding.left, height - padding.bottom);
    
    prices.forEach((price, i) => {
      const x = padding.left + (i / (prices.length - 1)) * chartWidth;
      const y = padding.top + ((maxPrice - price) / priceRange) * chartHeight;
      ctx.lineTo(x, y);
    });
    
    ctx.lineTo(padding.left + chartWidth, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
    
    // Draw line
    ctx.beginPath();
    prices.forEach((price, i) => {
      const x = padding.left + (i / (prices.length - 1)) * chartWidth;
      const y = padding.top + ((maxPrice - price) / priceRange) * chartHeight;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Draw current price dot
    const lastX = padding.left + chartWidth;
    const lastY = padding.top + ((maxPrice - prices[prices.length - 1]) / priceRange) * chartHeight;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fillStyle = lineColor;
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  _handleClick() {
    this.expanded = !this.expanded;
    this.emit('select', { position: this.position, expanded: this.expanded });
  }

  _handleEdit(e) {
    e.stopPropagation();
    this.emit('edit', { position: this.position });
  }

  _handleClose(e) {
    e.stopPropagation();
    this.emit('close', { position: this.position });
  }

  _handleDelete(e) {
    e.stopPropagation();
    // Let parent handle confirmation modal
    this.emit('delete', { position: this.position });
  }

  _getAdviceClass(action) {
    if (!action) return 'hold';
    const a = action.toLowerCase();
    if (a.includes('buy') || a.includes('acheter') || a.includes('renforcer')) return 'buy';
    if (a.includes('sell') || a.includes('vendre')) return 'sell';
    if (a.includes('watch') || a.includes('surveiller')) return 'watch';
    return 'hold';
  }

  render() {
    const p = this.position;
    const { value, percent, gross, fees, isProfit, currentPrice, invested, currentValue } = this.pnlData;
    const { value: changeValue, percent: changePercent, isPositive: isPriceUp } = this.priceChange;
    const { status: marketStatusClass, label: marketLabel } = this.marketStatus;
    const ticker = p.symbol || p.ticker || 'N/A';
    const quantity = p.quantity || 1;
    const entryPrice = p.entry_price || 0;
    const isOpen = p.status === 'open';
    const sym = this.currencySymbol;
    const hasIntraday = this.intradayData.length > 0;
    
    const statusMap = {
      open: { label: 'OUVERTE', class: 'open' },
      closed: { label: 'CLÔTURÉE', class: 'closed' },
      stopped: { label: 'STOPPÉE', class: 'stopped' }
    };
    const status = statusMap[p.status] || statusMap.open;
    
    const alertMap = {
      sl: '⚠️ SL',
      tp1: '🎯 TP1',
      tp2: '🎯 TP2'
    };

    return html`
      <div class="position-card" @click=${this._handleClick}>
        <div class="card-header">
          <div class="header-left">
            <div class="ticker-row">
              <span class="ticker">${ticker}</span>
              <app-badge variant="status" type="${status.class}" size="md">${status.label}</app-badge>
              ${isOpen ? html`
                <span class="market-status ${marketStatusClass}" title="${marketLabel}">
                  <span class="status-dot"></span>
                </span>
              ` : ''}
              <span class="days-held">${this.daysHeld}j</span>
              ${this.alertType ? html`
                <app-badge variant="alert" type="${this.alertType}" size="sm">${alertMap[this.alertType]}</app-badge>
              ` : ''}
              <!-- Advice badge always visible in header if available -->
              ${this.aiAdvice && this.aiAdvice.action ? html`
                <app-badge variant="advice" type="${this._getAdviceClass(this.aiAdvice.action)}" size="sm">${this.aiAdvice.action}</app-badge>
              ` : ''}
            </div>
            <div class="summary">
              ${quantity} × ${sym}${entryPrice.toFixed(2)}
              ${p.stop_loss ? html` · SL: ${sym}${p.stop_loss.toFixed(2)}` : ''}
            </div>
          </div>
          <div class="header-right">
            <div class="pnl-value ${isProfit ? 'positive' : 'negative'}">
              ${this.hideValues ? '••••••' : `${isProfit ? '+' : ''}${sym}${value.toFixed(2)}`}
            </div>
            <div class="pnl-percent ${isProfit ? 'positive' : 'negative'}">
              ${this.hideValues ? '••••' : `${percent >= 0 ? '+' : ''}${percent.toFixed(1)}%`}
            </div>
            <div class="current-price">${sym}${currentPrice.toFixed(2)}</div>
          </div>
          <div class="arrow">›</div>
        </div>
        <div class="card-content">
          <!-- AI Advice -->
          ${this.aiAdvice ? html`
            <div class="ai-advice">
              <div class="ai-advice-header">
                <span class="ai-advice-icon"><img src="/static/assets/ai-assistant.png" alt="AI Assistant" style="height: 22px; width: 22px;"></span>
                <span class="ai-advice-label">Analyse Assistant</span>
                <span class="ai-advice-action ${this._getAdviceClass(this.aiAdvice.action)}">${this.aiAdvice.action || 'Conserver'}</span>
              </div>
              <div class="ai-advice-text">${this.aiAdvice.conseil || this.aiAdvice.raison || this.aiAdvice.reason || ''}</div>
              ${this.aiAdvice.niveau_cle ? html`
                <div class="ai-advice-level">📍 Niveau clé: ${this.aiAdvice.niveau_cle}</div>
              ` : ''}
            </div>
          ` : ''}

          <!-- Intraday Chart - only show if data available -->
          ${hasIntraday ? html`
            <div class="chart-section">
              <div class="chart-container">
                <div class="chart-info">
                  <span class="chart-label">Intraday</span>
                  ${isOpen ? html`
                    <span class="chart-percent ${isPriceUp ? 'positive' : 'negative'}">
                      ${isPriceUp ? '+' : ''}${changePercent.toFixed(2)}%
                    </span>
                  ` : ''}
                </div>
                <canvas class="chart-canvas"></canvas>
              </div>
              ${this.dayRange.high && this.dayRange.low ? html`
                <div class="chart-range">
                  <div class="range-item">
                    <span class="range-label">Min</span>
                    <span class="range-value low">${sym}${this.dayRange.low.toFixed(2)}</span>
                  </div>
                  <div class="range-item">
                    <span class="range-label">Max</span>
                    <span class="range-value high">${sym}${this.dayRange.high.toFixed(2)}</span>
                  </div>
                </div>
              ` : ''}
            </div>
          ` : ''}
          
          <!-- P&L Breakdown -->
          <div class="pnl-breakdown">
            <div class="pnl-item">
              <div class="pnl-item-label">P&L Net</div>
              <div class="pnl-item-value ${isProfit ? 'positive' : 'negative'}">
                ${this.hideValues ? '••••••' : `${sym}${isProfit ? '+' : ''}${value.toFixed(2)}`}
              </div>
            </div>
            <div class="pnl-item">
              <div class="pnl-item-label">Brut</div>
              <div class="pnl-item-value ${gross >= 0 ? 'positive' : 'negative'}">
                ${this.hideValues ? '••••••' : `${sym}${gross >= 0 ? '+' : ''}${gross.toFixed(2)}`}
              </div>
            </div>
            <div class="pnl-item">
              <div class="pnl-item-label">Frais</div>
              <div class="pnl-item-value neutral">
                ${this.hideValues ? '••••' : `-${sym}${fees.toFixed(2)}`}
              </div>
            </div>
          </div>
          
          <!-- Stats Grid -->
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-label">Investi</div>
              <div class="stat-value">${this.hideValues ? '••••••' : `${sym}${invested.toFixed(2)}`}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Valeur</div>
              <div class="stat-value">${this.hideValues ? '••••••' : `${sym}${currentValue.toFixed(2)}`}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Prix d'entrée</div>
              <div class="stat-value">${sym}${entryPrice.toFixed(2)}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Quantité</div>
              <div class="stat-value">${quantity}</div>
            </div>
          </div>
          
          ${isOpen ? html`
            <div class="targets-section">
              <div class="targets-header">Objectifs</div>
              <div class="targets-bar">
                <!-- Reference lines for entry and TP1 -->
                ${p.entry_price ? html`<div class="target-reference" style="left: ${this.entryPosition}%"></div>` : ''}
                ${p.take_profit_1 ? html`<div class="target-reference" style="left: ${this.tp1Position}%"></div>` : ''}
                <!-- Current price marker -->
                <div class="targets-marker ${this.alertType ? this.alertType + '-reached' : ''}" style="left: ${this.markerPosition}%"></div>
              </div>
              <div class="targets-labels">
                <!-- SL always at 0% -->
                <div class="target-label sl ${currentPrice <= p.stop_loss ? 'reached' : ''}">
                  <span class="target-name">SL</span>
                  <span class="target-price">${p.stop_loss ? sym + p.stop_loss.toFixed(2) : '-'}</span>
                </div>
                <!-- TP1 at its calculated position -->
                ${p.take_profit_1 ? html`
                  <div class="target-label tp1 ${currentPrice >= p.take_profit_1 ? 'reached' : ''}" style="left: ${this.tp1Position}%">
                    <span class="target-name">TP1</span>
                    <span class="target-price">${sym}${p.take_profit_1.toFixed(2)}</span>
                  </div>
                ` : ''}
                <!-- TP2 always at 100% -->
                <div class="target-label tp2 ${currentPrice >= p.take_profit_2 ? 'reached' : ''}">
                  <span class="target-name">TP2</span>
                  <span class="target-price">${p.take_profit_2 ? sym + p.take_profit_2.toFixed(2) : '-'}</span>
                </div>
              </div>
            </div>
          ` : ''}
          
          <div class="actions">
            ${isOpen ? html`
              <app-button
                variant="primary"
                icon="✏️"
                size="sm"
                .theme=${this.theme}
                title="Modifier"
                @click=${this._handleEdit}
              ></app-button>
              <app-button
                variant="primary"
                icon="🔒"
                size="sm"
                .theme=${this.theme}
                title="Clôturer"
                @click=${this._handleClose}
              ></app-button>
            ` : ''}
            <app-button
              variant="primary"
              icon="🗑️"
              size="sm"
              .theme=${this.theme}
              title="Supprimer"
              @click=${this._handleDelete}
            ></app-button>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('position-card', PositionCard);
