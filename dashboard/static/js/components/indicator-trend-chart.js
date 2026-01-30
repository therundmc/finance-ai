/**
 * Indicator Trend Chart Component
 * Displays health score over time with signal-colored dots
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';

// Signal colors
const SIGNAL_COLORS = {
    buy: '#22C55E',    // Green
    keep: '#F59E0B',   // Orange/Yellow
    sell: '#EF4444'    // Red
};

export class IndicatorTrendChart extends BaseComponent {
    static properties = {
        ...super.properties,
        analyses: { type: Array },
        selectedTicker: { type: String, attribute: 'selected-ticker' },
        loading: { type: Boolean },
        compact: { type: Boolean, reflect: true }
    };

    static styles = [
        sharedStyles,
        css`
            :host {
                display: block;
                margin-bottom: 16px;
            }

            :host([compact]) {
                margin-bottom: 8px;
            }

            .chart-container {
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                overflow: hidden;
            }

            :host([compact]) .chart-container {
                background: var(--bg-tertiary);
                border: none;
                border-radius: var(--radius-sm);
                position: relative;
                overflow: hidden;
            }

            :host([compact]) .canvas-wrapper {
                padding: 8px;
                height: 80px;
            }

            :host([compact]) .empty-state {
                height: 80px;
                font-size: 0.7rem;
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
                z-index: 1;
            }

            .chart-footer-compact {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 12px;
                padding: 4px 8px 8px;
                font-size: 0.6rem;
                font-weight: 600;
            }

            .chart-footer-compact .data-count {
                color: var(--text-muted);
                margin-left: auto;
            }

            .chart-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                border-bottom: 1px solid var(--border-color);
            }

            .header-left {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .chart-title {
                font-size: 0.9rem;
                font-weight: 800;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .chart-title .icon {
                font-size: 1.1rem;
            }

            .ticker-select {
                padding: 6px 12px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 0.75rem;
                font-weight: 600;
                cursor: pointer;
            }

            .ticker-select:focus {
                outline: none;
                border-color: var(--brand-secondary);
            }

            .canvas-wrapper {
                padding: 12px 16px;
                height: 120px;
                position: relative;
            }

            canvas {
                width: 100%;
                height: 100%;
            }

            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 120px;
                color: var(--text-muted);
                font-size: 0.8rem;
            }

            .empty-state .icon {
                font-size: 1.5rem;
                margin-bottom: 6px;
                opacity: 0.5;
            }

            .chart-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 16px 12px;
            }

            .legend {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }

            .legend-item {
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 0.65rem;
                color: var(--text-secondary);
            }

            .legend-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }

            .legend-dot.buy { background: #22C55E; }
            .legend-dot.keep { background: #F59E0B; }
            .legend-dot.sell { background: #EF4444; }

            .data-count {
                font-size: 0.65rem;
                color: var(--text-muted);
            }
        `
    ];

    constructor() {
        super();
        this.analyses = [];
        this.selectedTicker = '';
        this.loading = false;
        this.compact = false;
    }

    // Get signal type from analysis
    _getSignalType(signal) {
        const s = (signal || '').toUpperCase();
        if (s.includes('ACHAT') || s.includes('ACHET') || s.includes('BUY') || s.startsWith('A')) return 'buy';
        if (s.includes('VENTE') || s.includes('VEND') || s.includes('SELL') || s.startsWith('V')) return 'sell';
        return 'keep';
    }

    // Calculate health score (same logic as analysis-page)
    _calculateHealthScore(analysis) {
        const ind = analysis?.indicators || {};
        const signalType = this._getSignalType(analysis?.signal);
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
        if (signalType === 'buy') score += 15;
        else if (signalType === 'sell') score -= 10;
        
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    get availableTickers() {
        const tickers = new Set();
        this.analyses.forEach(a => tickers.add(a.ticker));
        return Array.from(tickers).sort();
    }

    get filteredAnalyses() {
        if (!this.selectedTicker) return [];
        return this.analyses
            .filter(a => a.ticker === this.selectedTicker)
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    }

    firstUpdated() {
        super.firstUpdated();
        this._autoSelectTicker();
        // Try to draw immediately
        this._drawChart();
        // Fallback: observe for canvas insertion if not present
        if (!this.shadowRoot.querySelector('canvas')) {
            this._mutationObserver = new MutationObserver(() => {
                if (this.shadowRoot.querySelector('canvas')) {
                    this._drawChart();
                    this._mutationObserver.disconnect();
                }
            });
            this._mutationObserver.observe(this.shadowRoot, { childList: true, subtree: true });
        }
        // IntersectionObserver: redraw when visible
        this._intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
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
        if (this._mutationObserver) {
            this._mutationObserver.disconnect();
            this._mutationObserver = null;
        }
    }

    updated(changedProperties) {
        super.updated(changedProperties);
        if (changedProperties.has('analyses')) {
            this._autoSelectTicker();
        }
        // Always force a draw after update
        setTimeout(() => this._drawChart(), 0);
    }

    _autoSelectTicker() {
        if (this.availableTickers.length > 0 && !this.selectedTicker) {
            this.selectedTicker = this.availableTickers[0];
        }
    }

    _handleTickerChange(e) {
        this.selectedTicker = e.target.value;
        this.dispatchEvent(new CustomEvent('ticker-change', {
            detail: { ticker: this.selectedTicker },
            bubbles: true,
            composed: true
        }));
    }

    _drawChart() {
        const canvas = this.shadowRoot.querySelector('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const padding = { top: 15, right: 15, bottom: 25, left: 15 };

        // Clear
        ctx.clearRect(0, 0, width, height);

        const data = this.filteredAnalyses;
        if (data.length < 2) {
            return;
        }

        // Draw health line with signal-colored dots
        this._drawHealthLine(ctx, data, width, height, padding);
    }

    _drawHealthLine(ctx, data, width, height, padding) {
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;
        const minVal = 0;
        const maxVal = 100;
        const range = 100;

        // Draw colored line segments by signal
        for (let i = 1; i < data.length; i++) {
            const prev = data[i - 1];
            const curr = data[i];
            const healthPrev = this._calculateHealthScore(prev);
            const healthCurr = this._calculateHealthScore(curr);
            const x0 = padding.left + ((i - 1) / (data.length - 1)) * chartWidth;
            const y0 = padding.top + chartHeight - ((healthPrev - minVal) / range) * chartHeight;
            const x1 = padding.left + (i / (data.length - 1)) * chartWidth;
            const y1 = padding.top + chartHeight - ((healthCurr - minVal) / range) * chartHeight;
            const signalType = this._getSignalType(curr.signal);
            ctx.beginPath();
            ctx.strokeStyle = SIGNAL_COLORS[signalType];
            ctx.lineWidth = 3;
            ctx.moveTo(x0, y0);
            ctx.lineTo(x1, y1);
            ctx.stroke();
        }

        // Draw date labels (first and last only)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = '9px Inter, sans-serif';
        if (data.length > 0) {
            const firstDate = new Date(data[0].timestamp);
            ctx.textAlign = 'left';
            ctx.fillText(firstDate.toLocaleDateString('fr-CH', { day: '2-digit', month: '2-digit' }), padding.left, height - 4);
            const lastDate = new Date(data[data.length - 1].timestamp);
            ctx.textAlign = 'right';
            ctx.fillText(lastDate.toLocaleDateString('fr-CH', { day: '2-digit', month: '2-digit' }), width - padding.right, height - 4);
        }
    }

    render() {
        const tickers = this.availableTickers;
        const hasData = this.filteredAnalyses.length >= 2;
        const dataCount = this.filteredAnalyses.length;
        
        // Compact mode: no header, no selector, minimal footer
        if (this.compact) {
            return html`
                <div class="chart-container">
                    ${!hasData ? html`
                        <div class="empty-state">
                            <div class="icon">📊</div>
                            <div>Pas assez de données</div>
                        </div>
                    ` : html`
                        <span class="chart-label">Tendance Santé</span>
                        <div class="canvas-wrapper">
                            <canvas></canvas>
                        </div>
                        <div class="chart-footer-compact">
                            <span style="color:#22C55E">● Achat</span>
                            <span style="color:#F59E0B">● Conserv.</span>
                            <span style="color:#EF4444">● Vente</span>
                            <span class="data-count">${dataCount} pts</span>
                        </div>
                    `}
                </div>
            `;
        }
        
        return html`
            <div class="chart-container">
                <div class="chart-header">
                    <div class="header-left">
                        <div class="chart-title">
                            <span class="icon">📈</span>
                            Tendance Santé
                        </div>
                    </div>
                    <select class="ticker-select" 
                            .value="${this.selectedTicker}"
                            @change="${this._handleTickerChange}">
                        ${tickers.map(t => html`<option value="${t}" ?selected="${t === this.selectedTicker}">${t}</option>`)}
                    </select>
                </div>
                ${!hasData ? html`
                    <div class="empty-state">
                        <div class="icon">📊</div>
                        <div>Pas assez de données pour ${this.selectedTicker || 'ce ticker'}</div>
                    </div>
                ` : html`
                    <div class="canvas-wrapper">
                        <canvas></canvas>
                    </div>
                `}
                <div class="chart-footer">
                    <div class="legend">
                        <div class="legend-item" style="color:#22C55E">Acheter</div>
                        <div class="legend-item" style="color:#F59E0B">Conserver</div>
                        <div class="legend-item" style="color:#EF4444">Vendre</div>
                    </div>
                    ${hasData ? html`<span class="data-count">${dataCount} analyses</span>` : ''}
                </div>
            </div>
        `;
    }
}

customElements.define('indicator-trend-chart', IndicatorTrendChart);
