/**
 * Analysis Page - Main AI analysis view component
 * Displays news, search, latest analyses, and history
 * Includes ticker configuration and on-demand analysis
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';
import { BaseComponent, sharedStyles } from '../base-component.js';
import '../analysis-history-card.js';
import '../button.js';
import '../form-input.js';
import '../news-panel.js';
import '../portfolio-analysis-card.js';
import '../ticker-config.js';

export class AnalysisPage extends BaseComponent {
    static properties = {
        ...BaseComponent.properties,
        // Data
        analyses: { type: Array },
        latestAnalyses: { type: Array },
        tickers: { type: Array },
        trackedTickers: { type: Array },
        favorites: { type: Array },
        portfolioAnalysis: { type: Object },
        // Filters
        daysFilter: { type: Number },
        tickerFilter: { type: String },
        searchQuery: { type: String },
        // Latest filters
        latestSortBy: { type: String },
        latestSignalFilter: { type: String },
        latestSectorFilter: { type: String },
        // Market summary
        marketSummary: { type: Object },
        marketSummaryExpanded: { type: Boolean },
        // UI state
        loading: { type: Boolean },
        loadingAnalysis: { type: Boolean },
        historyExpanded: { type: Boolean },
        // API
        apiBase: { type: String, attribute: 'api-base' }
    };

    static styles = [
        sharedStyles,
        css`
            :host {
                display: block;
                width: 100%;
                overflow-x: hidden;
            }

            /* News Panel Spacing */
            news-panel {
                margin-bottom: 16px;
            }

            /* Analysis Container */
            .analysis-container {
                margin-bottom: 16px;
            }

            /* Search Section */
            .search-section {
                margin-bottom: 16px;
            }

            .search-bar {
                display: flex;
                gap: 8px;
                align-items: center;
                max-width: 220px;
            }

            .search-bar form-input {
                flex: 1;
                --input-padding: 4px 10px;
                --input-font-size: 0.65rem;
            }

            .search-bar form-input::part(input),
            .search-bar form-input input {
                padding: 4px 10px;
                font-size: 0.65rem;
                height: 26px;
            }

            .clear-search-btn {
                width: 26px;
                height: 26px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--bg-tertiary);
                border: 2px solid var(--border-color);
                border-radius: var(--radius-full);
                color: var(--text-muted);
                font-size: 0.75rem;
                cursor: pointer;
                transition: all 0.2s ease;
                flex-shrink: 0;
            }

            .clear-search-btn:hover {
                background: var(--danger);
                border-color: var(--danger);
                color: white;
            }

            /* Latest Analyses Grid */
            .latest-section {
                margin-bottom: 20px;
            }

            .section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
            }

            .section-title {
                font-size: 0.9rem;
                font-weight: 800;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .section-title .icon {
                font-size: 1.1rem;
            }

            .section-badge {
                font-size: 0.65rem;
                padding: 3px 8px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-full);
                color: var(--text-muted);
                font-weight: 600;
            }

            .latest-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                width: 100%;
                box-sizing: border-box;
                overflow: hidden;
            }

            .latest-grid > * {
                min-width: 0;
                overflow: hidden;
            }

            @media (max-width: 850px) {
                .latest-grid {
                    grid-template-columns: 1fr;
                }
            }

            /* History Section */
            .history-section {
                margin-top: 20px;
            }

            .history-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 0;
                margin-bottom: 12px;
                border-top: 2px solid var(--border-color);
                cursor: pointer;
            }

            .history-header:hover .toggle-icon {
                color: var(--brand-secondary);
            }

            .toggle-icon {
                font-size: 1.2rem;
                color: var(--text-muted);
                transition: transform 0.3s ease, color 0.2s ease;
            }

            .history-section.expanded .toggle-icon {
                transform: rotate(90deg);
                color: var(--brand-secondary);
            }

            .history-content {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease;
            }

            .history-section.expanded .history-content {
                max-height: 3000px;
            }

            /* Filters */
            .filters-bar {
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
                flex-wrap: wrap;
                overflow-x: hidden;
            }

            .filter-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
                min-width: 0;
            }

            .filter-label {
                font-size: 0.6rem;
                font-weight: 700;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .filter-buttons {
                display: flex;
                gap: 4px;
                flex-wrap: wrap;
            }

            .filter-btn {
                padding: 4px 10px;
                background: var(--bg-gradient-card);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-full);
                color: var(--text-secondary);
                font-size: 0.65rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .filter-btn:hover {
                border-color: var(--brand-secondary);
                color: var(--brand-secondary);
            }

            .filter-btn.active {
                background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
                border-color: transparent;
                color: white;
            }

            .ticker-chips {
                display: flex;
                gap: 4px;
                flex-wrap: wrap;
                max-width: 300px;
            }

            /* Latest Filters Bar */
            .latest-filters {
                display: flex;
                gap: 8px;
                margin-bottom: 12px;
                flex-wrap: wrap;
                align-items: flex-start;
                overflow-x: hidden;
            }

            .latest-filter-group {
                display: flex;
                gap: 4px;
                align-items: center;
                flex-wrap: wrap;
            }

            .latest-filter-label {
                font-size: 0.6rem;
                font-weight: 700;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                flex-shrink: 0;
            }

            .sort-buttons {
                display: flex;
                gap: 4px;
                flex-wrap: wrap;
            }

            .latest-filter-btn {
                padding: 4px 10px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-full);
                color: var(--text-secondary);
                font-size: 0.65rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .latest-filter-btn:hover {
                border-color: var(--brand-secondary);
                color: var(--brand-secondary);
            }

            .latest-filter-btn.active {
                background: var(--brand-secondary);
                border-color: var(--brand-secondary);
                color: white;
            }

            /* Ticker Config Section */
            ticker-config {
                display: block;
                margin-top: 16px;
            }

            /* Date Groups */
            .date-group {
                margin-bottom: 16px;
            }

            .date-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                margin-bottom: 8px;
                border-bottom: 2px dashed var(--border-color);
            }

            .date-label {
                font-size: 0.8rem;
                font-weight: 800;
                background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-transform: capitalize;
            }

            .date-count {
                font-size: 0.65rem;
                color: var(--text-muted);
                background: var(--bg-tertiary);
                padding: 4px 10px;
                border-radius: var(--radius-full);
                font-weight: 700;
            }

            .date-items {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                width: 100%;
                box-sizing: border-box;
                overflow: hidden;
            }

            .date-items > * {
                min-width: 0;
                overflow: hidden;
            }

            @media (max-width: 850px) {
                .date-items {
                    grid-template-columns: 1fr;
                }
            }

            /* Empty & Loading States */
            .empty-state {
                text-align: center;
                padding: 40px 20px;
                color: var(--text-secondary);
            }

            .empty-state .icon {
                font-size: 3rem;
                margin-bottom: 12px;
                opacity: 0.5;
            }

            .loading-skeleton {
                background: linear-gradient(90deg,
                    var(--bg-secondary) 25%,
                    var(--bg-tertiary) 50%,
                    var(--bg-secondary) 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: var(--radius-md);
            }

            @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .skeleton-card {
                height: 80px;
                margin-bottom: 8px;
            }

            .skeleton-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 12px;
                margin-bottom: 16px;
            }

            .skeleton-grid-item {
                height: 100px;
            }

            /* Market Summary Panel */
            .market-panel {
                background: var(--bg-secondary);
                border: 2px solid var(--border-color);
                border-radius: var(--radius-md);
                overflow: hidden;
                margin-bottom: 16px;
                transition: all 0.25s ease;
            }

            .market-panel-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 14px;
                cursor: pointer;
                user-select: none;
            }

            .market-panel-header:hover {
                background: var(--bg-tertiary);
            }

            .market-header-left {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .market-panel-title {
                font-size: 0.9rem;
                font-weight: 800;
                color: var(--text-primary);
            }

            .market-toggle-icon {
                font-size: 1.2rem;
                color: var(--text-muted);
                transition: transform 0.3s ease;
            }

            .market-panel.expanded .market-toggle-icon {
                transform: rotate(90deg);
                color: var(--brand-secondary);
            }

            .market-panel-content {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.35s ease;
            }

            .market-panel.expanded .market-panel-content {
                max-height: 500px;
            }

            .market-content-inner {
                padding: 0 14px 14px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .market-badges-row {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                align-items: center;
            }

            .market-badges-label {
                font-size: 0.7rem;
                font-weight: 700;
                margin-right: 4px;
            }

            .market-badge {
                display: inline-block;
                padding: 2px 8px;
                margin: 2px;
                border-radius: var(--radius-full);
                font-size: 0.7rem;
                font-weight: 700;
                cursor: help;
            }

            .market-badge.buy {
                background: rgba(6,214,160,0.1);
                border: 1px solid var(--success);
                color: var(--success);
            }

            .market-badge.sell {
                background: rgba(255,51,102,0.1);
                border: 1px solid var(--danger);
                color: var(--danger);
            }

            .market-badge.sector {
                background: var(--bg-primary);
                border: 1px solid var(--border-color);
                font-size: 0.65rem;
            }

            .market-meta {
                font-size: 0.6rem;
                color: var(--text-muted);
            }

            /* Favorites separator */
            .favorites-separator {
                display: flex;
                align-items: center;
                gap: 8px;
                margin: 12px 0 8px 0;
                color: var(--text-muted);
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .favorites-separator::after {
                content: '';
                flex: 1;
                height: 1px;
                background: var(--border-color);
            }

            /* Favorite button on card */
            .fav-btn {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: transparent;
                border: none;
                cursor: pointer;
                font-size: 1rem;
                opacity: 0.4;
                transition: all 0.2s ease;
                padding: 0;
                flex-shrink: 0;
            }

            .fav-btn:hover {
                opacity: 1;
                transform: scale(1.2);
            }

            .fav-btn.active {
                opacity: 1;
            }

            /* Responsive */
            @media (max-width: 640px) {
                .filters-bar {
                    flex-direction: column;
                    gap: 12px;
                }

                .ticker-chips {
                    max-width: 100%;
                }

            }
        `
    ];

    constructor() {
        super();
        this.analyses = [];
        this.latestAnalyses = [];
        this.tickers = [];
        this.trackedTickers = [];
        this.favorites = [];
        this.portfolioAnalysis = null;
        this.daysFilter = 7;
        this.tickerFilter = '';
        this.searchQuery = '';
        this.latestSortBy = 'time'; // 'time', 'ticker', 'signal', 'health'
        this.latestSignalFilter = ''; // '', 'acheter', 'vendre', 'conserver'
        this.latestSectorFilter = ''; // '', 'Technology', etc.
        this.marketSummary = null;
        this.marketSummaryExpanded = false;
        this.loading = true;
        this.loadingAnalysis = false;
        this.historyExpanded = false;
        this.apiBase = '';
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
    }

    async _loadData() {
        this.loading = true;
        this.loadingAnalysis = true;
        try {
            // Load latest, history and tracked tickers in parallel
            const [latestData, historyData, tickersData] = await Promise.all([
                this._fetchLatest(),
                this._fetchHistory(),
                this._fetchTrackedTickers()
            ]);
            
            // latest is an object keyed by ticker, convert to array
            const latestObj = latestData.latest || {};
            this.latestAnalyses = Object.values(latestObj);
            this.favorites = latestData.favorites || [];
            this.analyses = historyData.analyses || [];
            this.trackedTickers = tickersData.tickers || [];
            
            // Extract unique tickers
            this._updateTickers();

            // Load portfolio analysis and market summary separately
            await Promise.all([
                this._loadPortfolioAnalysis(),
                this._loadMarketSummary()
            ]);
        } catch (error) {
            console.error('Error loading analyses:', error);
        } finally {
            this.loading = false;
            this.loadingAnalysis = false;
        }
    }

    async _fetchLatest() {
        const response = await fetch(`${this.apiBase}/api/latest`);
        return response.json();
    }

    async _fetchTrackedTickers() {
        const response = await fetch(`${this.apiBase}/api/settings/tickers`);
        return response.json();
    }

    async _fetchHistory() {
        let url = `${this.apiBase}/api/analyses?days=${this.daysFilter}`;
        if (this.tickerFilter) {
            url += `&ticker=${this.tickerFilter}`;
        }
        const response = await fetch(url);
        return response.json();
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

    async _loadMarketSummary() {
        try {
            const response = await fetch(`${this.apiBase}/api/market/summary`);
            const data = await response.json();
            if (data.success && data.summary) {
                this.marketSummary = data;
            }
        } catch (error) {
            console.error('Error loading market summary:', error);
            this.marketSummary = null;
        }
    }

    async _reloadHistory() {
        try {
            const historyData = await this._fetchHistory();
            this.analyses = historyData.analyses || [];
        } catch (error) {
            console.error('Error reloading history:', error);
        }
    }

    _updateTickers() {
        const tickerSet = new Set();
        this.analyses.forEach(a => tickerSet.add(a.ticker));
        this.latestAnalyses.forEach(a => tickerSet.add(a.ticker));
        this.tickers = Array.from(tickerSet).sort();
    }

    _handleDaysFilter(e, days) {
        e.stopPropagation();
        e.preventDefault();
        this.daysFilter = days;
        this._reloadHistory();
    }

    _handleTickerFilter(e, ticker) {
        e.stopPropagation();
        e.preventDefault();
        this.tickerFilter = ticker;
        this._reloadHistory();
    }

    _handleLatestSort(e, sortBy) {
        this.latestSortBy = sortBy;
        this.requestUpdate();
    }

    _handleLatestSignalFilter(e, signal) {
        this.latestSignalFilter = this.latestSignalFilter === signal ? '' : signal;
        this.requestUpdate();
    }

    _handleLatestSectorFilter(e, sector) {
        this.latestSectorFilter = this.latestSectorFilter === sector ? '' : sector;
        this.requestUpdate();
    }

    _toggleMarketSummary() {
        this.marketSummaryExpanded = !this.marketSummaryExpanded;
    }

    _isFavorite(ticker) {
        return this.favorites.includes(ticker);
    }

    async _toggleFavorite(e, ticker) {
        e.stopPropagation();
        e.preventDefault();
        const isFav = this._isFavorite(ticker);
        try {
            const response = await fetch(`${this.apiBase}/api/favorites/${ticker}`, {
                method: isFav ? 'DELETE' : 'POST'
            });
            const data = await response.json();
            if (data.success) {
                if (isFav) {
                    this.favorites = this.favorites.filter(t => t !== ticker);
                } else {
                    this.favorites = [...this.favorites, ticker];
                }
                this.requestUpdate();
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }

    _handleSearch(e) {
        // Handle both native input event and custom event from form-input
        this.searchQuery = e.detail?.value ?? e.target?.value ?? '';
    }

    _clearSearch() {
        this.searchQuery = '';
    }

    _toggleHistory() {
        this.historyExpanded = !this.historyExpanded;
    }

    _handleTickersChanged(e) {
        this.trackedTickers = e.detail.tickers || [];
        this.requestUpdate();
    }

    _handleAnalysisSelect(e) {
        this.dispatchEvent(new CustomEvent('analysis-select', {
            detail: e.detail,
            bubbles: true,
            composed: true
        }));
    }

    _normalizeSignal(signal) {
        const s = (signal || '').toUpperCase();
        if (s.includes('ACHAT') || s.includes('ACHET') || s.includes('BUY') || s.startsWith('A')) return 'acheter';
        if (s.includes('VENTE') || s.includes('VEND') || s.includes('SELL') || s.startsWith('V')) return 'vendre';
        return 'conserver';
    }

    _calculateHealthScore(analysis) {
        const ind = analysis?.indicators || {};
        const signal = this._normalizeSignal(analysis?.signal);
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

    _formatTime(timestamp) {
        if (!timestamp) return '';
        return new Date(timestamp).toLocaleTimeString('fr-CH', { hour: '2-digit', minute: '2-digit' });
    }

    _formatDateHeader(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) return "Aujourd'hui";
        if (date.toDateString() === yesterday.toDateString()) return "Hier";
        
        return date.toLocaleDateString('fr-CH', { weekday: 'long', day: 'numeric', month: 'long' });
    }

    _groupByDate(analyses) {
        const grouped = {};
        analyses.forEach(a => {
            const date = new Date(a.timestamp).toISOString().split('T')[0];
            if (!grouped[date]) grouped[date] = [];
            grouped[date].push(a);
        });
        // Sort by date descending
        return Object.entries(grouped).sort((a, b) => new Date(b[0]) - new Date(a[0]));
    }

    get uniqueSectors() {
        const sectors = new Set();
        this.latestAnalyses.forEach(a => {
            if (a.sector && a.sector !== 'N/A' && a.sector !== null) {
                sectors.add(a.sector);
            }
        });
        return Array.from(sectors).sort();
    }

    _getSectorTrend(sector) {
        // Get trend for a sector from market summary (sector_trends format)
        if (!this.marketSummary || !this.marketSummary.summary) return null;

        const summary = this.marketSummary.summary;

        // New format: sector_trends array
        if (summary.sector_trends && Array.isArray(summary.sector_trends)) {
            const sectorData = summary.sector_trends.find(s => s.sector === sector);
            if (sectorData) {
                return sectorData.trend; // "Haussier", "Baissier", "Neutre"
            }
        }

        // Legacy format: sector_performance array (for backwards compatibility)
        if (summary.sector_performance && Array.isArray(summary.sector_performance)) {
            const sectorData = summary.sector_performance.find(s => s.sector === sector);
            if (sectorData) {
                return sectorData.trend;
            }
        }

        return null;
    }

    _getTrendIcon(trend) {
        if (trend === 'Haussier') return '▲';
        if (trend === 'Baissier') return '▼';
        if (trend === 'Neutre') return '●';
        return '';
    }

    _getTrendColor(trend) {
        if (trend === 'Haussier') return 'var(--success)';
        if (trend === 'Baissier') return 'var(--danger)';
        if (trend === 'Neutre') return 'var(--text-muted)';
        return 'var(--text-secondary)';
    }

    get filteredLatest() {
        let result = [...this.latestAnalyses];
        
        // Filter by tracked tickers
        if (this.trackedTickers.length > 0) {
            result = result.filter(a => this.trackedTickers.includes(a.ticker));
        }
        
        // Filter by search query
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            result = result.filter(a => a.ticker.toLowerCase().includes(query));
        }
        
        // Filter by signal
        if (this.latestSignalFilter) {
            result = result.filter(a => this._normalizeSignal(a.signal) === this.latestSignalFilter);
        }

        // Filter by sector
        if (this.latestSectorFilter) {
            result = result.filter(a => a.sector === this.latestSectorFilter);
        }

        // Sort
        switch (this.latestSortBy) {
            case 'ticker':
                result.sort((a, b) => (a.ticker || '').localeCompare(b.ticker || ''));
                break;
            case 'signal':
                const signalOrder = { 'acheter': 0, 'conserver': 1, 'vendre': 2 };
                result.sort((a, b) => {
                    const orderA = signalOrder[this._normalizeSignal(a.signal)] ?? 1;
                    const orderB = signalOrder[this._normalizeSignal(b.signal)] ?? 1;
                    return orderA - orderB;
                });
                break;
            case 'health':
                result.sort((a, b) => this._calculateHealthScore(b) - this._calculateHealthScore(a));
                break;
            case 'time':
            default:
                result.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
                break;
        }
        
        return result;
    }

    render() {
        if (this.loading) {
            return this._renderLoading();
        }

        return html`
            <!-- News Panel -->
            <news-panel
                theme="${this.theme}"
                api-base="${this.apiBase}"
            ></news-panel>

            <!-- Market Summary -->
            ${this._renderMarketSummary()}

            <!-- Latest Analyses -->
            ${this._renderLatest()}

            <!-- Ticker Configuration -->
            <ticker-config
                .trackedTickers="${this.trackedTickers}"
                .theme="${this.theme}"
                api-base="${this.apiBase}"
                @tickers-changed="${this._handleTickersChanged}"
            ></ticker-config>

            <!-- History Section -->
            ${this._renderHistory()}
        `;
    }

    _renderLoading() {
        return html`
            <div class="skeleton-grid">
                ${[1, 2, 3, 4].map(() => html`
                    <div class="loading-skeleton skeleton-grid-item"></div>
                `)}
            </div>
            <div class="skeleton-card loading-skeleton"></div>
            <div class="skeleton-card loading-skeleton"></div>
            <div class="skeleton-card loading-skeleton"></div>
        `;
    }

    _renderLatest() {
        const latest = this.filteredLatest;

        return html`
            <div class="latest-section">
                <div class="section-header">
                    <div class="section-title">
                        <span class="icon">⚡</span>
                        Dernières Analyses
                    </div>
                    <span class="section-badge">${latest.length} tickers</span>
                </div>

                <!-- Filters and Sort -->
                <div class="latest-filters">
                    <div class="latest-filter-group">
                        <span class="latest-filter-label">Trier:</span>
                        <div class="sort-buttons">
                            ${[
                                { key: 'time', label: '🕐 Récent'},
                                { key: 'ticker', label: '🔤 Ticker'},
                                { key: 'signal', label: '📊 Signal'},
                                { key: 'health', label: '💪 Santé'}
                            ].map(s => html`
                                <app-button
                                    variant="${this.latestSortBy === s.key ? 'primary' : 'filter'}"
                                    label="${s.label}"
                                    size="sm"
                                    ?active="${this.latestSortBy === s.key}"
                                    .theme="${this.theme}"
                                    @click="${(e) => this._handleLatestSort(e, s.key)}"
                                ></app-button>
                            `)}
                        </div>
                    </div>

                    <!-- Sector Filter -->
                    ${this.uniqueSectors.length > 0 ? html`
                        <div class="latest-filter-group">
                            <span class="latest-filter-label">Secteur:</span>
                            <div class="sort-buttons" style="flex-wrap: wrap;">
                                <button
                                    class="latest-filter-btn ${this.latestSectorFilter === '' ? 'active' : ''}"
                                    @click="${(e) => { e.stopPropagation(); this.latestSectorFilter = ''; this.requestUpdate(); }}"
                                >Tous</button>
                                ${this.uniqueSectors.map(sector => {
                                    const trend = this._getSectorTrend(sector);
                                    const icon = trend ? this._getTrendIcon(trend) : '';
                                    const color = trend ? this._getTrendColor(trend) : '';
                                    return html`
                                        <button
                                            class="latest-filter-btn ${this.latestSectorFilter === sector ? 'active' : ''}"
                                            @click="${(e) => { e.stopPropagation(); this._handleLatestSectorFilter(e, sector); }}"
                                        >
                                            ${icon ? html`<span style="color: ${color}; margin-right: 4px;">${icon}</span>` : ''}
                                            ${sector}
                                        </button>
                                    `;
                                })}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Search -->
                    <div class="search-bar">
                        <form-input
                            type="text"
                            placeholder="🔍 Rechercher..."
                            .value="${this.searchQuery}"
                            @input="${this._handleSearch}"                            size="sm"                            theme="${this.theme}"
                        ></form-input>
                        ${this.searchQuery ? html`
                            <button 
                                class="clear-search-btn" 
                                @click="${this._clearSearch}"
                                title="Effacer"
                            >✕</button>
                        ` : ''}
                    </div>
                </div>

                ${latest.length === 0 ? html`
                    <div class="empty-state">
                        <div class="icon">📊</div>
                        <div>Aucune analyse récente</div>
                    </div>
                ` : html`
                    ${(() => {
                        const favs = latest.filter(a => this._isFavorite(a.ticker));
                        const rest = latest.filter(a => !this._isFavorite(a.ticker));
                        return html`
                            ${favs.length > 0 ? html`
                                <div class="latest-grid">
                                    ${favs.map(a => html`
                                        <div style="position: relative;">
                                            <button class="fav-btn active" title="Retirer des favoris" @click="${(e) => this._toggleFavorite(e, a.ticker)}" style="position:absolute;top:8px;right:8px;z-index:2;">★</button>
                                            <analysis-history-card
                                                theme="${this.theme}"
                                                .analysis="${a}"
                                                .allAnalyses="${this.analyses}"
                                                @select="${this._handleAnalysisSelect}"
                                            ></analysis-history-card>
                                        </div>
                                    `)}
                                </div>
                                ${rest.length > 0 ? html`
                                    <div class="favorites-separator">Autres actions</div>
                                ` : ''}
                            ` : ''}
                            ${rest.length > 0 ? html`
                                <div class="latest-grid">
                                    ${rest.map(a => html`
                                        <div style="position: relative;">
                                            <button class="fav-btn" title="Ajouter aux favoris" @click="${(e) => this._toggleFavorite(e, a.ticker)}" style="position:absolute;top:8px;right:8px;z-index:2;">☆</button>
                                            <analysis-history-card
                                                theme="${this.theme}"
                                                .analysis="${a}"
                                                .allAnalyses="${this.analyses}"
                                                @select="${this._handleAnalysisSelect}"
                                            ></analysis-history-card>
                                        </div>
                                    `)}
                                </div>
                            ` : ''}
                        `;
                    })()}
                `}
            </div>
        `;
    }

    _renderMarketSummary() {
        // Market summary panel is removed - sector trends are now shown in the sector filter buttons
        return '';
    }

    _renderHistory() {
        const groupedAnalyses = this._groupByDate(this.analyses);

        return html`
            <div class="history-section ${this.historyExpanded ? 'expanded' : ''}">
                <div class="history-header" @click="${this._toggleHistory}">
                    <div class="section-title">
                        <span class="icon">📜</span>
                        Historique
                    </div>
                    <span class="toggle-icon">›</span>
                </div>

                <div class="history-content">
                    <!-- Filters -->
                    <div class="filters-bar">
                        <div class="filter-group">
                            <label class="filter-label">Période</label>
                            <div class="filter-buttons">
                                ${[
                                    { days: 1, label: "Aujourd'hui" },
                                    { days: 7, label: '7j' },
                                    { days: 30, label: '30j' },
                                    { days: 90, label: '90j' }
                                ].map(f => html`
                                    <button 
                                        class="filter-btn ${this.daysFilter === f.days ? 'active' : ''}"
                                        @click="${(e) => this._handleDaysFilter(e, f.days)}"
                                    >${f.label}</button>
                                `)}
                            </div>
                        </div>
                        <div class="filter-group">
                            <label class="filter-label">Action</label>
                            <div class="ticker-chips">
                                <button 
                                    class="filter-btn ${this.tickerFilter === '' ? 'active' : ''}"
                                    @click="${(e) => this._handleTickerFilter(e, '')}"
                                >⭐ Toutes</button>
                                ${this.tickers.slice(0, 8).map(ticker => html`
                                    <button 
                                        class="filter-btn ${this.tickerFilter === ticker ? 'active' : ''}"
                                        @click="${(e) => this._handleTickerFilter(e, ticker)}"
                                    >${ticker}</button>
                                `)}
                            </div>
                        </div>
                    </div>

                    <!-- Grouped History -->
                    ${groupedAnalyses.length === 0 ? html`
                        <div class="empty-state">
                            <div class="icon">📋</div>
                            <div>Aucune analyse trouvée</div>
                        </div>
                    ` : html`
                        ${groupedAnalyses.map(([date, analyses]) => html`
                            <div class="date-group">
                                <div class="date-header">
                                    <span class="date-label">${this._formatDateHeader(date)}</span>
                                    <span class="date-count">${analyses.length}</span>
                                </div>
                                <div class="date-items">
                                    ${analyses.map(analysis => html`
                                        <analysis-history-card
                                            theme="${this.theme}"
                                            .analysis="${analysis}"
                                            .allAnalyses="${this.analyses}"
                                            @select="${this._handleAnalysisSelect}"
                                        ></analysis-history-card>
                                    `)}
                                </div>
                            </div>
                        `)}
                    `}
                </div>
            </div>
        `;
    }
}

customElements.define('analysis-page', AnalysisPage);
