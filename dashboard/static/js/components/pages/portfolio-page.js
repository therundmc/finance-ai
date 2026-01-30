/**
 * Portfolio Page - Main portfolio view component
 * Embeds all portfolio components: stats, chart, positions
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';
import { BaseComponent, sharedStyles } from '../base-component.js';
import '../stat-card.js';
import '../position-card.js';
import '../portfolio-chart.js';
import '../button.js';
import '../section-toggle-btn.js';
import '../live-indicator.js';

export class PortfolioPage extends BaseComponent {
    static properties = {
        ...BaseComponent.properties,
        // Data
        positions: { type: Array },
        stats: { type: Object },
        portfolioAnalysis: { type: Object },
        // UI state
        filter: { type: String },
        loading: { type: Boolean },
        loadingAnalysis: { type: Boolean },
        currency: { type: String },
        exchangeRates: { type: Object },
        hideValues: { type: Boolean, attribute: 'hide-values' },
        expandAll: { type: Boolean, state: true },
        // API endpoints
        apiBase: { type: String, attribute: 'api-base' }
    };

    static styles = [
        sharedStyles,
        css`
            :host {
                display: block;
                width: 100%;
                max-width: 2400px;
                box-sizing: border-box;
            }

            /* Stats Grid - always 3 columns */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin-bottom: 16px;
            }

            /* Wide screen: all 6 stats on one line */
            @media (min-width: 1200px) {
                .stats-grid {
                    grid-template-columns: repeat(6, 1fr);
                }
            }

            .stats-grid stat-card {
                --stat-card-padding: 12px;
            }

            /* Chart Container */
            .chart-container {
                margin-bottom: 16px;
            }

            /* Filter Bar - single line layout */
            .filter-bar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 12px;
            }

            .filter-tabs {
                display: flex;
                gap: 6px;
                align-items: center;
            }

            .live-status {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-left: auto;
                margin-right: 8px;
            }

            .btn-new-position {
                flex-shrink: 0;
            }

            /* Positions List */
            .positions-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            /* Wide screen grid support */
            @media (min-width: 900px) {
                .positions-list {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 12px;
                }
            }

            @media (min-width: 1300px) {
                .positions-list {
                    grid-template-columns: repeat(3, 1fr);
                }
            }

            @media (min-width: 1800px) {
                .positions-list {
                    grid-template-columns: repeat(4, 1fr);
                }
            }

            /* Expand all button - hidden by default, shown on grid layout */
            .expand-all-btn {
                display: none;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                padding: 0;
                font-size: 0.85rem;
                color: var(--text-secondary);
                background: var(--bg-tertiary);
                border: 2px solid var(--border-color);
                border-radius: var(--radius-full);
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            /* Show expand button only when grid is active */
            @media (min-width: 900px) {
                .expand-all-btn {
                    display: flex;
                }
            }

            .expand-all-btn:hover {
                background: var(--bg-hover);
                border-color: var(--brand-secondary);
                color: var(--brand-secondary);
                transform: translateY(-2px);
            }

            .expand-all-btn.active {
                background-color: var(--brand-secondary);
                background-image: linear-gradient(135deg, var(--brand-secondary) 0%, var(--brand-pink) 100%);
                border: none;
                color: white;
                box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
            }

            .expand-all-btn .icon {
                transition: transform 0.2s ease;
            }

            .expand-all-btn.active .icon {
                transform: rotate(90deg);
            }

            .positions-empty {
                text-align: center;
                padding: 40px 20px;
                color: var(--text-secondary);
                font-size: 0.9rem;
            }

            .positions-empty-icon {
                font-size: 3rem;
                margin-bottom: 12px;
                opacity: 0.5;
            }

            /* Loading State */
            .loading-skeleton {
                background: linear-gradient(90deg,
                    var(--bg-secondary) 25%,
                    var(--bg-tertiary) 50%,
                    var(--bg-secondary) 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 12px;
            }

            @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .skeleton-stats {
                height: 140px;
                margin-bottom: 16px;
            }

            .skeleton-chart {
                height: 200px;
                margin-bottom: 16px;
            }

            .skeleton-position {
                height: 80px;
                margin-bottom: 8px;
            }
        `
    ];

    constructor() {
        super();
        this.positions = [];
        this.stats = {
            value: 0,
            invested: 0,
            openPositions: 0,
            pnlOpen: 0,
            pnlRealized: 0,
            pnlGlobal: 0
        };
        this.portfolioAnalysis = null;
        this.filter = 'open';
        this.loading = true;
        this.loadingAnalysis = false;
        this.currency = 'USD';
        this.exchangeRates = { USD: 1, CHF: 0.88, EUR: 0.92, GBP: 0.79 };
        this.hideValues = false;
        this.expandAll = false;
        this.apiBase = '';
        
        // SSE connection for live prices
        this._priceEventSource = null;
        
        // Scroll state for analysis card
        this._lastScrollY = 0;
        this._scrollThreshold = 100;
    }

    // Currency conversion helpers
    get currencySymbol() {
        const symbols = { USD: '$', EUR: '€', CHF: 'CHF ', GBP: '£' };
        return symbols[this.currency] || '$';
    }

    _getTickerCurrency(ticker) {
        if (ticker.endsWith('.SW') || ticker.endsWith('.VX')) return 'CHF';
        if (ticker.endsWith('.PA') || ticker.endsWith('.DE') || ticker.endsWith('.AS')) return 'EUR';
        if (ticker.endsWith('.L')) return 'GBP';
        return 'USD';
    }

    _convertToDisplayCurrency(price, fromCurrency) {
        if (fromCurrency === this.currency) return price;
        // Convert to USD first, then to target
        const usdPrice = price / this.exchangeRates[fromCurrency];
        return usdPrice * this.exchangeRates[this.currency];
    }

    _formatPrice(price, fromCurrency = 'USD') {
        const converted = this._convertToDisplayCurrency(price, fromCurrency);
        return `${this.currencySymbol}${converted.toFixed(2)}`;
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
        this._connectPriceStream(); // Start SSE connection
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', this._handleVisibilityChange);
        
        // Listen for scroll to minimize/maximize analysis card
        window.addEventListener('scroll', this._handleScroll);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._disconnectPriceStream(); // Clean up SSE connection
        document.removeEventListener('visibilitychange', this._handleVisibilityChange);
        window.removeEventListener('scroll', this._handleScroll);
    }

    _handleScroll = () => {
        const currentScrollY = window.scrollY;
        const sectionToggle = document.querySelector('.main-section-toggle');
        
        if (!sectionToggle) return;
        
        if (currentScrollY > this._scrollThreshold) {
            sectionToggle.classList.add('minimized');
        } else {
            sectionToggle.classList.remove('minimized');
        }
        
        this._lastScrollY = currentScrollY;
    };

    _handleVisibilityChange = () => {
        if (document.hidden) {
            this._disconnectPriceStream();
        } else {
            this._loadData();
            this._connectPriceStream();
        }
    };

    async _loadData() {
        this.loading = true;
        this.loadingAnalysis = true;
        try {
            await Promise.all([
                this._loadPositions(),
                this._loadStats(),
                this._loadPortfolioAnalysis()
            ]);
        } catch (error) {
            console.error('Error loading portfolio data:', error);
        } finally {
            this.loading = false;
            this.loadingAnalysis = false;
        }
    }

    async _loadPortfolioAnalysis() {
        try {
            const response = await fetch(`${this.apiBase}/api/portfolio/analysis`);
            const data = await response.json();
            if (data.success && data.analysis) {
                this.portfolioAnalysis = data.analysis;
                console.log('📊 Portfolio analysis loaded:', this.portfolioAnalysis);
            }
        } catch (error) {
            console.error('Error loading portfolio analysis:', error);
            this.portfolioAnalysis = null;
        }
    }

    async _loadPositions() {
        try {
            const response = await fetch(`${this.apiBase}/api/positions`);
            const data = await response.json();
            this.positions = data.positions || [];
            
            // Fetch live prices for open positions
            await this._fetchLivePrices();
        } catch (error) {
            console.error('Error loading positions:', error);
            this.positions = [];
        }
    }

    async _loadStats() {
        try {
            const response = await fetch(`${this.apiBase}/api/portfolio/performance`);
            const data = await response.json();
            
            if (data.success && data.latest_snapshot) {
                const snapshot = data.latest_snapshot;
                this.stats = {
                    value: snapshot.total_value || 0,
                    invested: snapshot.total_invested || 0,
                    openPositions: snapshot.open_positions_count || 0,
                    pnlOpen: snapshot.total_pnl || 0,
                    pnlRealized: snapshot.realized_pnl || 0,
                    pnlGlobal: snapshot.global_pnl || 0
                };
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async _fetchLivePrices() {
        const openPositions = this.positions.filter(p => p.status === 'open');
        if (openPositions.length === 0) return;

        const tickers = [...new Set(openPositions.map(p => p.ticker))];
        const positionsForCalc = openPositions.map(p => ({
            ticker: p.ticker,
            entry_price: p.entry_price,
            quantity: p.quantity || 1,
            buy_commission: p.buy_commission || 0,
            sell_commission: p.sell_commission || 0
        }));

        try {
            const response = await fetch(`${this.apiBase}/api/live/prices`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tickers, positions: positionsForCalc })
            });
            const result = await response.json();

            if (result.success && result.prices) {
                // Apply live data to positions
                this.positions = this.positions.map(p => {
                    if (p.status === 'open' && result.prices[p.ticker]) {
                        const liveData = result.prices[p.ticker];
                        return {
                            ...p,
                            current_price: liveData.price,
                            live_data: liveData,
                            pnl_value: liveData.pnl?.pnl_net,
                            pnl_percent: liveData.pnl?.pnl_percent,
                            pnl_gross: liveData.pnl?.pnl_gross,
                            current_value: liveData.pnl?.current_value,
                            invested: liveData.pnl?.invested
                        };
                    }
                    return p;
                });

                // Update stats from live prices
                this._updateStatsFromPositions();
            }
        } catch (error) {
            console.error('Error fetching live prices:', error);
        }
    }

    _updateStatsFromPositions() {
        const openPositions = this.positions.filter(p => p.status === 'open');
        
        let totalValue = 0;
        let totalInvested = 0;
        let pnlOpen = 0;

        openPositions.forEach(p => {
            const invested = p.invested || (p.entry_price * (p.quantity || 1));
            const value = p.current_value || invested;
            const pnl = p.pnl_value || 0;

            totalInvested += invested;
            totalValue += value;
            pnlOpen += pnl;
        });

        this.stats = {
            ...this.stats,
            value: totalValue,
            invested: totalInvested,
            openPositions: openPositions.length,
            pnlOpen: pnlOpen,
            pnlGlobal: pnlOpen + (this.stats.pnlRealized || 0)
        };
    }

    _startLivePriceUpdates() {
        // Legacy method - now handled by SSE
        console.log('📈 Live price updates via SSE');
    }

    _stopLivePriceUpdates() {
        // Legacy method - now handled by SSE
    }

    _connectPriceStream() {
        // Disconnect existing stream if any
        this._disconnectPriceStream();
        
        // Create new EventSource for SSE
        this._priceEventSource = new EventSource(`${this.apiBase}/api/stream/prices`);
        
        this._priceEventSource.onmessage = (event) => {
            try {
                const result = JSON.parse(event.data);
                if (result.success && result.prices) {
                    console.log('📡 Received live prices via SSE:', Object.keys(result.prices).length, 'tickers');
                    
                    // Flash live indicator
                    const indicator = this.shadowRoot?.querySelector('#live-indicator');
                    if (indicator) {
                        indicator.active = true;
                        setTimeout(() => { indicator.active = false; }, 2000);
                    }
                    
                    // Apply live data to positions
                    this.positions = this.positions.map(p => {
                        if (p.status === 'open' && result.prices[p.ticker]) {
                            const liveData = result.prices[p.ticker];
                            return {
                                ...p,
                                current_price: liveData.price,
                                live_data: liveData,
                                pnl_value: liveData.pnl?.pnl_net,
                                pnl_percent: liveData.pnl?.pnl_percent,
                                pnl_gross: liveData.pnl?.pnl_gross,
                                current_value: liveData.pnl?.current_value,
                                invested: liveData.pnl?.invested
                            };
                        }
                        return p;
                    });

                    // Update stats from live prices
                    this._updateStatsFromPositions();
                    this.requestUpdate();
                }
            } catch (error) {
                console.error('❌ Error processing SSE price update:', error);
            }
        };

        this._priceEventSource.onerror = (error) => {
            console.error('❌ SSE connection error:', error);
            // Auto-reconnect after 5 seconds
            setTimeout(() => {
                if (this.isConnected) {
                    console.log('🔄 Reconnecting to price stream...');
                    this._connectPriceStream();
                }
            }, 5000);
        };

        this._priceEventSource.onopen = () => {
            console.log('✅ Connected to live price stream (SSE)');
        };
    }

    _disconnectPriceStream() {
        if (this._priceEventSource) {
            this._priceEventSource.close();
            this._priceEventSource = null;
            console.log('⏹️ Disconnected from price stream');
        }
    }

    _handleFilterChange(status) {
        this.filter = status;
    }

    _handleRefresh() {
        this._loadData();
        
        // Also refresh the chart
        const chart = this.shadowRoot.querySelector('portfolio-chart');
        if (chart) {
            chart.refresh();
        }
    }

    _handleNewPosition() {
        this.dispatchEvent(new CustomEvent('new-position', {
            bubbles: true,
            composed: true
        }));
    }

    _handlePositionEdit(e) {
        this.dispatchEvent(new CustomEvent('position-edit', {
            detail: e.detail,
            bubbles: true,
            composed: true
        }));
    }

    _handlePositionClose(e) {
        this.dispatchEvent(new CustomEvent('position-close', {
            detail: e.detail,
            bubbles: true,
            composed: true
        }));
    }

    _handlePositionDelete(e) {
        this.dispatchEvent(new CustomEvent('position-delete', {
            detail: e.detail,
            bubbles: true,
            composed: true
        }));
    }

    _formatCurrency(value) {
        const symbol = this.currency === 'EUR' ? '€' : 
                       this.currency === 'CHF' ? 'CHF ' :
                       this.currency === 'GBP' ? '£' : '$';
        return `${symbol}${value.toLocaleString('fr-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    _formatPnl(value) {
        const formatted = this._formatCurrency(Math.abs(value));
        return value >= 0 ? `+${formatted}` : `-${formatted}`;
    }

    get filteredPositions() {
        if (this.filter === 'open') {
            return this.positions.filter(p => p.status === 'open');
        } else if (this.filter === 'closed') {
            return this.positions.filter(p => p.status !== 'open');
        }
        return this.positions;
    }

    render() {
        if (this.loading) {
            return this._renderLoading();
        }

        return html`
            <!-- Stats Block -->
            ${this._renderStats()}

            <!-- Portfolio Chart -->
            <div class="chart-container">
                <portfolio-chart
                    theme="${this.theme}"
                    api-endpoint="${this.apiBase}/api/portfolio/chart-data"
                    ?hide-values="${this.hideValues}"
                ></portfolio-chart>
            </div>

            <!-- Filter Bar -->
            ${this._renderFilterBar()}

            <!-- Positions List -->
            ${this._renderPositions()}
        `;
    }

    _renderLoading() {
        return html`
            <div class="skeleton-stats loading-skeleton"></div>
            <div class="skeleton-chart loading-skeleton"></div>
            <div class="skeleton-position loading-skeleton"></div>
            <div class="skeleton-position loading-skeleton"></div>
            <div class="skeleton-position loading-skeleton"></div>
        `;
    }

    _renderStats() {
        const { value, invested, openPositions, pnlOpen, pnlRealized, pnlGlobal } = this.stats;
        
        // Convert values from USD to display currency
        const rate = this.exchangeRates[this.currency] || 1;
        const convertedValue = value * rate;
        const convertedInvested = invested * rate;
        const convertedPnlOpen = pnlOpen * rate;
        const convertedPnlRealized = pnlRealized * rate;
        const convertedPnlGlobal = pnlGlobal * rate;
        
        return html`
            <div class="stats-grid">
                <stat-card 
                    label="Valeur" 
                    value="${convertedValue.toFixed(2)}" 
                    currency="${this.currency}"
                    variant="primary"
                    size="small"
                    theme="${this.theme}"
                    ?hide-value="${this.hideValues}"
                ></stat-card>
                <stat-card 
                    label="Investi" 
                    value="${convertedInvested.toFixed(2)}" 
                    currency="${this.currency}"
                    size="small"
                    theme="${this.theme}"
                    ?hide-value="${this.hideValues}"
                ></stat-card>
                <stat-card 
                    label="Positions" 
                    value="${openPositions}"
                    size="small"
                    theme="${this.theme}"
                ></stat-card>
                <stat-card 
                    label="P&L Open" 
                    value="${convertedPnlOpen.toFixed(2)}" 
                    currency="${this.currency}"
                    auto-color
                    show-sign
                    size="small"
                    theme="${this.theme}"
                    ?hide-value="${this.hideValues}"
                ></stat-card>
                <stat-card 
                    label="P&L Réalisé" 
                    value="${convertedPnlRealized.toFixed(2)}" 
                    currency="${this.currency}"
                    auto-color
                    show-sign
                    size="small"
                    theme="${this.theme}"
                    ?hide-value="${this.hideValues}"
                ></stat-card>
                <stat-card 
                    label="P&L Global" 
                    value="${convertedPnlGlobal.toFixed(2)}" 
                    currency="${this.currency}"
                    auto-color
                    show-sign
                    size="small"
                    theme="${this.theme}"
                    ?hide-value="${this.hideValues}"
                ></stat-card>
            </div>
        `;
    }

    _renderFilterBar() {
        return html`
            <div class="filter-bar">
                <div class="filter-tabs">
                    <app-button 
                        variant="filter" 
                        icon="🟢" 
                        ?active="${this.filter === 'open'}"
                        theme="${this.theme}"
                        @click="${() => this._handleFilterChange('open')}"
                    ></app-button>
                    <app-button 
                        variant="filter" 
                        icon="🔴" 
                        ?active="${this.filter === 'closed'}"
                        theme="${this.theme}"
                        @click="${() => this._handleFilterChange('closed')}"
                    ></app-button>
                    <button 
                        class="expand-all-btn ${this.expandAll ? 'active' : ''}"
                        @click="${this._handleToggleExpandAll}"
                        title="${this.expandAll ? 'Réduire tout' : 'Déplier tout'}"
                    >
                        <span class="icon">▶</span>
                    </button>
                </div>
                <div class="live-status">
                    <live-indicator id="live-indicator" size="small"></live-indicator>
                </div>
                <app-button 
                    class="btn-new-position"
                    variant="primary" 
                    icon="➕" 
                    label="Nouvelle position"
                    size="small"
                    theme="${this.theme}"
                    @click="${this._handleNewPosition}"
                ></app-button>
            </div>
        `;
    }

    _handleToggleExpandAll() {
        this.expandAll = !this.expandAll;
    }

    _getPositionAdvice(ticker) {
        if (!this.portfolioAnalysis) return null;
        const positions = this.portfolioAnalysis.position_advice || 
                         this.portfolioAnalysis.conseils_positions || 
                         this.portfolioAnalysis.positions || [];
        return positions.find(p => p.ticker === ticker) || null;
    }

    _renderPositions() {
        const positions = this.filteredPositions;

        if (positions.length === 0) {
            return html`
                <div class="positions-empty">
                    <div class="positions-empty-icon">${this.filter === 'open' ? '📈' : '📊'}</div>
                    <div>Aucune position ${this.filter === 'open' ? 'ouverte' : 'clôturée'}</div>
                </div>
            `;
        }

        return html`
            <div class="positions-list">
                ${positions.map(position => html`
                    <position-card
                        theme="${this.theme}"
                        ticker="${position.ticker}"
                        .position="${position}"
                        .aiAdvice="${this._getPositionAdvice(position.ticker)}"
                        ?hide-values="${this.hideValues}"
                        ?expanded="${this.expandAll}"
                        @edit="${this._handlePositionEdit}"
                        @close="${this._handlePositionClose}"
                        @delete="${this._handlePositionDelete}"
                    ></position-card>
                `)}
            </div>
        `;
    }
}

customElements.define('portfolio-page', PortfolioPage);
