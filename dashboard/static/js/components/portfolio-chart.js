/**
 * Portfolio Chart Inline Component
 * Displays portfolio performance chart with time range controls and mode toggle
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';

// Time range options
const TIME_RANGES = [
  { days: 1, label: '1J' },
  { days: 7, label: '1S' },
  { days: 30, label: '1M' },
  { days: 90, label: '3M' },
  { days: 365, label: '1A' },
  { days: 0, label: 'Tout' }
];

export class PortfolioChart extends BaseComponent {
  static properties = {
    ...super.properties,
    // Data
    labels: { type: Array },
    values: { type: Array },
    pnlData: { type: Array },
    invested: { type: Array },
    
    // State
    mode: { type: String },         // 'pnl', 'value', 'all'
    timeRangeIndex: { type: Number },
    changePercent: { type: Number },
    minValue: { type: Number },
    maxValue: { type: Number },
    hideValues: { type: Boolean, attribute: 'hide-values' },
    
    // Options
    currency: { type: String },
    chartLabel: { type: String },
    loading: { type: Boolean },
    error: { type: String },
    
    // API
    apiEndpoint: { type: String }
  };
  
  static styles = [
    sharedStyles,
    css`
      :host {
        display: block;
      }
      
      .portfolio-chart-inline {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: var(--spacing-sm);
        transition: var(--transition-fast);
        position: relative;
        overflow: hidden;
      }

      :host([theme="dark"]) .portfolio-chart-inline {
        background: var(--bg-secondary);
        border-color: var(--border-color);
      }

      .portfolio-chart-inline::before {
        display: none;
      }
      
      .portfolio-chart-inline:hover {
        border-color: var(--brand-secondary);
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
      }
      
      /* Header */
      .portfolio-chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-xs);
        gap: var(--spacing-xs);
      }
      
      /* Time Range Navigation */
      .portfolio-time-range {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      
      .time-nav-btn {
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        background: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: var(--radius-full);
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--text-secondary);
        cursor: pointer;
        transition: var(--transition-fast);
      }
      
      .time-nav-btn:hover {
        background: var(--bg-hover);
        border-color: var(--brand-secondary);
        color: var(--brand-secondary);
      }
      
      .time-nav-btn:active {
        transform: scale(0.95);
      }
      
      .time-nav-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      
      .time-range-label {
        min-width: 32px;
        text-align: center;
        font-size: 0.75rem;
        font-weight: 800;
        color: var(--text-secondary);
        background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      /* Chart Mode Toggle */
      .chart-mode-toggle {
        display: flex;
        gap: 4px;
      }
      
      .chart-mode-btn {
        width: 32px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        background: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: var(--radius-full);
        font-size: 0.8rem;
        cursor: pointer;
        transition: var(--transition-fast);
      }
      
      .chart-mode-btn:hover {
        background: var(--bg-hover);
        border-color: var(--brand-secondary);
      }
      
      .chart-mode-btn.active {
        background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
        border-color: transparent;
        box-shadow: 0 2px 6px rgba(139, 92, 246, 0.2);
      }
      
      /* Chart Info */
      .portfolio-chart-info {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
      }
      
      .chart-value {
        font-size: 0.8rem;
        font-weight: 900;
        padding: 3px 8px;
        border-radius: var(--radius-full);
        font-family: 'JetBrains Mono', monospace;
      }
      
      .chart-value.positive {
        background: linear-gradient(135deg, rgba(6, 214, 160, 0.25), rgba(0, 255, 136, 0.15));
        color: var(--success);
        border: 1px solid rgba(6, 214, 160, 0.4);
      }
      
      .chart-value.negative {
        background: linear-gradient(135deg, rgba(255, 51, 102, 0.25), rgba(255, 107, 107, 0.15));
        color: var(--danger);
        border: 1px solid rgba(255, 51, 102, 0.4);
      }
      
      .refresh-btn {
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        background: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: var(--radius-full);
        color: var(--text-muted);
        cursor: pointer;
        transition: var(--transition-fast);
      }
      
      .refresh-btn:hover {
        background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
        border-color: transparent;
        color: white;
        box-shadow: 0 2px 6px rgba(139, 92, 246, 0.2);
      }
      
      .refresh-btn:hover svg {
        animation: spin 0.6s ease-in-out;
      }
      
      .refresh-btn.loading svg {
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      /* Chart Container */
      .portfolio-chart-container {
        position: relative;
        width: 100%;
        min-height: 120px;
      }
      
      .portfolio-chart-container.loading::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 30px;
        height: 30px;
        margin: -15px 0 0 -15px;
        border: 3px solid var(--border-color);
        border-top-color: var(--brand-secondary);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      
      canvas {
        width: 100%;
        height: 120px;
        cursor: crosshair;
        filter: drop-shadow(0 2px 4px rgba(139, 92, 246, 0.1));
      }
      
      @supports (mix-blend-mode: screen) {
        canvas {
          mix-blend-mode: normal;
        }
      }
      
      /* Chart Footer */
      .portfolio-chart-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 var(--spacing-xs);
        margin-top: var(--spacing-xs);
      }
      
      .chart-min,
      .chart-max {
        font-size: 0.7rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
      }
      
      .chart-min {
        color: var(--danger);
      }
      
      .chart-max {
        color: var(--success);
      }
      
      .chart-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      
      /* No Data / Error States */
      .no-data-message,
      .error-message {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 120px;
        text-align: center;
        color: var(--text-muted);
      }
      
      .no-data-message .icon,
      .error-message .icon {
        font-size: 2.5rem;
        margin-bottom: var(--spacing-sm);
      }
      
      .no-data-message p,
      .error-message p {
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0 0 4px 0;
      }
      
      .no-data-message small {
        font-size: 0.75rem;
        opacity: 0.7;
      }
      
      /* Tooltip */
      .chart-tooltip {
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid var(--brand-secondary);
        border-radius: var(--radius-sm);
        padding: 8px 12px;
        font-size: 0.75rem;
        color: white;
        pointer-events: none;
        z-index: 100;
        opacity: 0;
        transition: opacity 0.15s ease;
        white-space: nowrap;
      }
      
      .chart-tooltip.visible {
        opacity: 1;
      }
      
      .tooltip-date {
        font-weight: 700;
        margin-bottom: 4px;
        color: var(--text-muted);
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 4px;
      }
      
      .tooltip-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        line-height: 1.6;
      }
      
      .tooltip-label {
        color: #aaa;
      }
      
      .tooltip-value {
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
      }
      
      .tooltip-value.positive { color: var(--success); }
      .tooltip-value.negative { color: var(--danger); }
    `
  ];
  
  constructor() {
    super();
    this.mode = 'pnl';
    this.timeRangeIndex = 2; // Default 1M
    this.changePercent = 0;
    this.minValue = 0;
    this.maxValue = 0;
    this.hideValues = false;
    this.currency = 'USD';
    this.chartLabel = 'P&L';
    this.loading = false;
    this.error = null;
    this.apiEndpoint = '/api/portfolio/chart-data';
    
    this.labels = [];
    this.values = [];
    this.pnlData = [];
    this.invested = [];
    
    this._chart = null;
    this._canvasCtx = null;
  }
  
  get currencySymbol() {
    const symbols = { USD: '$', EUR: '€', CHF: 'CHF ', GBP: '£' };
    return symbols[this.currency] || '$';
  }
  
  get currentTimeRange() {
    return TIME_RANGES[this.timeRangeIndex];
  }
  
  get isPositive() {
    return this.changePercent >= 0;
  }
  
  // Lifecycle
  firstUpdated() {
    this._canvasCtx = this.shadowRoot.querySelector('canvas')?.getContext('2d');
    // Only fetch if apiEndpoint is set
    if (this.apiEndpoint) {
      this.fetchData();
    }
    
    // IntersectionObserver: redraw when visible (fixes chart not appearing on initial load)
    this._intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && this.values.length > 0) {
          requestAnimationFrame(() => this._drawChart());
        }
      });
    }, { threshold: 0.1 });
    this._intersectionObserver.observe(this);
  }
  
  disconnectedCallback() {
    super.disconnectedCallback && super.disconnectedCallback();
    if (this._intersectionObserver) {
      this._intersectionObserver.disconnect();
      this._intersectionObserver = null;
    }
  }
  
  updated(changedProperties) {
    if (changedProperties.has('mode') || changedProperties.has('timeRangeIndex')) {
      this._updateMinMax();
      this._drawChart();
    }
    if (changedProperties.has('values') || changedProperties.has('pnlData')) {
      this._updateMinMax();
      this.requestUpdate();
      // Use requestAnimationFrame to ensure canvas is ready
      requestAnimationFrame(() => this._drawChart());
    }
  }
  
  // API
  async fetchData() {
    const days = this.currentTimeRange.days;
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`${this.apiEndpoint}?days=${days}`);
      const data = await response.json();
      
      if (!data.success || !data.labels || data.labels.length === 0) {
        this.error = 'no-data';
        this.loading = false;
        return;
      }
      
      this.labels = data.labels;
      this.values = data.datasets.value || [];
      this.pnlData = data.datasets.global_pnl || data.datasets.pnl || [];
      this.invested = data.datasets.invested || [];
      
      // Calculate stats
      const lastPnl = this.pnlData[this.pnlData.length - 1] || 0;
      const pnlPercent = data.datasets.global_pnl_percent || data.datasets.pnl_percent || [];
      this.changePercent = pnlPercent[pnlPercent.length - 1] || 0;
      
      // Update min/max based on mode
      this._updateMinMax();
      
      this.loading = false;
      this._drawChart();
      
      this.emit('data-loaded', { data });
      
    } catch (err) {
      console.error('Error fetching portfolio data:', err);
      this.error = 'error';
      this.loading = false;
    }
  }
  
  _updateMinMax() {
    let dataSet;
    switch (this.mode) {
      case 'pnl':
        dataSet = this.pnlData;
        this.chartLabel = 'P&L';
        break;
      case 'value':
        dataSet = this.values;
        this.chartLabel = 'Valeur';
        break;
      default:
        dataSet = this.values;
        this.chartLabel = 'Portfolio';
    }
    
    if (dataSet.length > 0) {
      this.minValue = Math.min(...dataSet);
      this.maxValue = Math.max(...dataSet);
    }
  }
  
  // Actions
  _changeTimeRange(direction) {
    const newIndex = this.timeRangeIndex + direction;
    if (newIndex < 0 || newIndex >= TIME_RANGES.length) return;
    
    this.timeRangeIndex = newIndex;
    this._updateMinMax();
    this.fetchData();
    
    this.emit('time-range-changed', { 
      index: newIndex, 
      range: TIME_RANGES[newIndex] 
    });
  }
  
  _switchMode(newMode) {
    this.mode = newMode;
    this._updateMinMax();
    this.emit('mode-changed', { mode: newMode });
  }
  
  _refresh() {
    this.fetchData();
    this.emit('refresh');
  }
  
  // Chart Drawing
  _drawChart() {
    const canvas = this.shadowRoot.querySelector('canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    // Set canvas size for high DPI
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    
    // Clear
    ctx.clearRect(0, 0, width, height);
    
    const padding = { top: 10, bottom: 10, left: 5, right: 5 };
    
    switch (this.mode) {
      case 'pnl':
        // P&L with colored fill and neutral line
        this._drawPnlChart(ctx, width, height, padding, this.pnlData);
        break;
        
      case 'value':
        // Value (blue solid) + Invested (purple dotted), no fill
        if (this.values.length > 1 && this.invested.length > 1) {
          // Calculate combined min/max for both datasets with padding
          const allData = [...this.values, ...this.invested];
          let min = Math.min(...allData);
          let max = Math.max(...allData);
          // Add 5% padding to range for better visualization
          const rangePadding = (max - min) * 0.1 || max * 0.02;
          min = min - rangePadding;
          max = max + rangePadding;
          this._drawLineWithRange(ctx, width, height, padding, this.invested, '#8b5cf6', min, max, [5, 5]); // Invested dotted
          this._drawLineWithRange(ctx, width, height, padding, this.values, '#3b82f6', min, max); // Value solid
        }
        break;
        
      case 'all':
        // All 3 lines: Value (blue solid), Invested (purple dotted), P&L (green/red based on value)
        if (this.values.length > 1 && this.invested.length > 1) {
          // Value and Invested share same scale with padding
          const valueInvestedData = [...this.values, ...this.invested];
          let minVI = Math.min(...valueInvestedData);
          let maxVI = Math.max(...valueInvestedData);
          // Add padding to range
          const rangePadding = (maxVI - minVI) * 0.1 || maxVI * 0.02;
          minVI = minVI - rangePadding;
          maxVI = maxVI + rangePadding;
          this._drawLineWithRange(ctx, width, height, padding, this.invested, '#8b5cf6', minVI, maxVI, [5, 5]); // Invested dotted
          this._drawLineWithRange(ctx, width, height, padding, this.values, '#3b82f6', minVI, maxVI); // Value solid
        }
        // P&L on its own scale (thinner line)
        if (this.pnlData.length > 1) {
          const lastPnl = this.pnlData[this.pnlData.length - 1] || 0;
          const pnlColor = lastPnl >= 0 ? '#22c55e' : '#ef4444';
          this._drawLine(ctx, width, height, padding, this.pnlData, pnlColor, false, false, null, 1.5);
        }
        break;
    }
  }
  
  // Draw P&L chart with zero line and proper fill (neutral line color)
  _drawPnlChart(ctx, width, height, padding, data) {
    if (!data || data.length < 2) return;
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const min = Math.min(...data, 0); // Include 0 in range
    const max = Math.max(...data, 0); // Include 0 in range
    const range = max - min || 1;
    
    // Calculate zero line position
    const zeroY = padding.top + chartHeight - ((0 - min) / range) * chartHeight;
    
    const points = data.map((val, i) => ({
      x: padding.left + (i / (data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((val - min) / range) * chartHeight,
      value: val
    }));
    
    // Draw dotted zero line
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.moveTo(padding.left, zeroY);
    ctx.lineTo(width - padding.right, zeroY);
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.5)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw filled areas - split by positive/negative
    // Positive fill (green) - above zero line
    ctx.beginPath();
    let started = false;
    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      if (p.value >= 0) {
        if (!started) {
          ctx.moveTo(p.x, zeroY);
          started = true;
        }
        ctx.lineTo(p.x, p.y);
      } else if (started) {
        // Find intersection with zero line
        const prev = points[i - 1];
        const intersectX = prev.x + (p.x - prev.x) * (prev.value / (prev.value - p.value));
        ctx.lineTo(intersectX, zeroY);
        ctx.closePath();
        
        const gradient = ctx.createLinearGradient(0, padding.top, 0, zeroY);
        gradient.addColorStop(0, 'rgba(34, 197, 94, 0.4)');
        gradient.addColorStop(1, 'rgba(34, 197, 94, 0.05)');
        ctx.fillStyle = gradient;
        ctx.fill();
        
        ctx.beginPath();
        started = false;
      }
    }
    if (started) {
      ctx.lineTo(points[points.length - 1].x, zeroY);
      ctx.closePath();
      const gradient = ctx.createLinearGradient(0, padding.top, 0, zeroY);
      gradient.addColorStop(0, 'rgba(34, 197, 94, 0.4)');
      gradient.addColorStop(1, 'rgba(34, 197, 94, 0.05)');
      ctx.fillStyle = gradient;
      ctx.fill();
    }
    
    // Negative fill (red) - below zero line
    ctx.beginPath();
    started = false;
    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      if (p.value < 0) {
        if (!started) {
          ctx.moveTo(p.x, zeroY);
          started = true;
        }
        ctx.lineTo(p.x, p.y);
      } else if (started) {
        // Find intersection with zero line
        const prev = points[i - 1];
        const intersectX = prev.x + (p.x - prev.x) * (-prev.value / (p.value - prev.value));
        ctx.lineTo(intersectX, zeroY);
        ctx.closePath();
        
        const gradient = ctx.createLinearGradient(0, zeroY, 0, height - padding.bottom);
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.05)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0.4)');
        ctx.fillStyle = gradient;
        ctx.fill();
        
        ctx.beginPath();
        started = false;
      }
    }
    if (started) {
      ctx.lineTo(points[points.length - 1].x, zeroY);
      ctx.closePath();
      const gradient = ctx.createLinearGradient(0, zeroY, 0, height - padding.bottom);
      gradient.addColorStop(0, 'rgba(239, 68, 68, 0.05)');
      gradient.addColorStop(1, 'rgba(239, 68, 68, 0.4)');
      ctx.fillStyle = gradient;
      ctx.fill();
    }
    
    // Draw the main line with NEUTRAL color (gray/white)
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      ctx.quadraticCurveTo(prev.x, prev.y, cpx, (prev.y + curr.y) / 2);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    
    ctx.strokeStyle = 'rgba(180, 180, 180, 0.9)'; // Neutral gray
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
  
  // Draw line with specific min/max range (for overlaying multiple datasets)
  _drawLineWithRange(ctx, width, height, padding, data, color, min, max, dash = null, lineWidth = 2) {
    if (!data || data.length < 2) return;
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const range = max - min || 1;
    
    const points = data.map((val, i) => ({
      x: padding.left + (i / (data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((val - min) / range) * chartHeight
    }));
    
    // Draw line
    ctx.beginPath();
    if (dash) ctx.setLineDash(dash);
    else ctx.setLineDash([]);
    
    ctx.moveTo(points[0].x, points[0].y);
    
    // Smooth curve using quadratic bezier
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      ctx.quadraticCurveTo(prev.x, prev.y, cpx, (prev.y + curr.y) / 2);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.setLineDash([]);
  }
  
  _drawLine(ctx, width, height, padding, data, color, fill = true, useZeroBase = false, dash = null, lineWidth = 2.5) {
    if (!data || data.length < 2) return;
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    
    const points = data.map((val, i) => ({
      x: padding.left + (i / (data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((val - min) / range) * chartHeight
    }));
    
    // Draw gradient fill
    if (fill) {
      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, color.replace(')', ', 0.3)').replace('rgb', 'rgba').replace('#3b82f6', 'rgba(59, 130, 246, 0.3)'));
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      
      ctx.beginPath();
      ctx.moveTo(points[0].x, height - padding.bottom);
      points.forEach(p => ctx.lineTo(p.x, p.y));
      ctx.lineTo(points[points.length - 1].x, height - padding.bottom);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();
    }
    
    // Draw line
    ctx.beginPath();
    if (dash) ctx.setLineDash(dash);
    else ctx.setLineDash([]);
    
    ctx.moveTo(points[0].x, points[0].y);
    
    // Smooth curve using quadratic bezier
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      ctx.quadraticCurveTo(prev.x, prev.y, cpx, (prev.y + curr.y) / 2);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.setLineDash([]);
  }
  
  _formatValue(value) {
    if (value === undefined || value === null) return '--';
    const sign = value >= 0 ? '' : '';
    return `${this.currencySymbol}${value.toFixed(0)}`;
  }
  
  _formatPercent(value) {
    if (value === undefined || value === null) return '--%';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  }
  
  render() {
    return html`
      <div class="portfolio-chart-inline">
        <div class="portfolio-chart-header">
          <!-- Time Range Navigation -->
          <div class="portfolio-time-range">
            <button 
              class="time-nav-btn" 
              @click=${() => this._changeTimeRange(-1)}
              ?disabled=${this.timeRangeIndex === 0}
              title="Réduire"
            >−</button>
            <span class="time-range-label">${this.currentTimeRange.label}</span>
            <button 
              class="time-nav-btn" 
              @click=${() => this._changeTimeRange(1)}
              ?disabled=${this.timeRangeIndex === TIME_RANGES.length - 1}
              title="Augmenter"
            >+</button>
          </div>
          
          <!-- Chart Mode Toggle -->
          <div class="chart-mode-toggle">
            <button 
              class="chart-mode-btn ${this.mode === 'pnl' ? 'active' : ''}"
              @click=${() => this._switchMode('pnl')}
              title="P&L"
            >📈</button>
            <button 
              class="chart-mode-btn ${this.mode === 'value' ? 'active' : ''}"
              @click=${() => this._switchMode('value')}
              title="Valeur"
            >💰</button>
            <button 
              class="chart-mode-btn ${this.mode === 'all' ? 'active' : ''}"
              @click=${() => this._switchMode('all')}
              title="Tout"
            >📊</button>
          </div>
          
          <!-- Chart Info -->
          <div class="portfolio-chart-info">
            <span class="chart-value ${this.isPositive ? 'positive' : 'negative'}">
              ${this._formatPercent(this.changePercent)}
            </span>
            <button 
              class="refresh-btn ${this.loading ? 'loading' : ''}" 
              @click=${this._refresh}
              title="Rafraîchir"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M21 21v-5h-5"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="portfolio-chart-container ${this.loading ? 'loading' : ''}">
          ${this.error === 'no-data' ? html`
            <div class="no-data-message">
              <span class="icon">📊</span>
              <p>Aucune donnée de portfolio disponible</p>
              <small>Les snapshots sont générés toutes les heures</small>
            </div>
          ` : this.error === 'error' ? html`
            <div class="error-message">
              <span class="icon">⚠️</span>
              <p>Erreur de chargement des données</p>
            </div>
          ` : html`
            <canvas></canvas>
          `}
          
          ${!this.error ? html`
            <div class="portfolio-chart-footer">
              <span class="chart-min">${this.hideValues ? '••••' : this._formatValue(this.minValue)}</span>
              <span class="chart-label">${this.chartLabel}</span>
              <span class="chart-max">${this.hideValues ? '••••' : this._formatValue(this.maxValue)}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('portfolio-chart', PortfolioChart);
