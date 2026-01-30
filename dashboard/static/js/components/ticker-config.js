/**
 * Ticker Configuration Component
 * Manage tracked tickers for analysis
 */

import { html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';
import { BaseComponent, sharedStyles } from './base-component.js';

export class TickerConfig extends BaseComponent {
    static properties = {
        ...BaseComponent.properties,
        trackedTickers: { type: Array },
        newTicker: { type: String },
        expanded: { type: Boolean, reflect: true },
        apiBase: { type: String, attribute: 'api-base' }
    };

    static styles = [
        sharedStyles,
        css`
            :host {
                display: block;
            }

            .config-card {
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                overflow: hidden;
                transition: all 0.2s ease;
            }

            .config-card:hover {
                border-color: var(--brand-secondary);
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
            }

            .config-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                cursor: pointer;
                user-select: none;
            }

            .header-left {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .header-icon {
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
                border-radius: var(--radius-sm);
                font-size: 1rem;
            }

            .header-text {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .header-title {
                font-size: 0.8rem;
                font-weight: 700;
                color: var(--text-primary);
            }

            .header-subtitle {
                font-size: 0.65rem;
                color: var(--text-muted);
            }

            .header-right {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .ticker-count {
                padding: 4px 10px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-full);
                font-size: 0.65rem;
                font-weight: 700;
                color: var(--text-secondary);
            }

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

            .config-content {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease;
            }

            :host([expanded]) .config-content {
                max-height: 500px;
            }

            .config-body {
                padding: 0 16px 16px;
                border-top: 1px solid var(--border-color);
            }

            /* Add Ticker Section */
            .add-section {
                padding: 12px 0;
                border-bottom: 1px solid var(--border-color);
            }

            .add-row {
                display: flex;
                gap: 8px;
            }

            .add-input {
                flex: 1;
                padding: 10px 14px;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-full);
                background: var(--bg-tertiary);
                color: var(--text-primary);
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                transition: all 0.2s ease;
            }

            .add-input::placeholder {
                text-transform: none;
                color: var(--text-muted);
            }

            .add-input:focus {
                outline: none;
                border-color: var(--brand-secondary);
                background: var(--bg-secondary);
            }

            .add-btn {
                padding: 10px 16px;
                background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
                border: none;
                border-radius: var(--radius-full);
                color: white;
                font-size: 0.7rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .add-btn:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }

            /* Tickers Grid */
            .tickers-section {
                padding-top: 12px;
            }

            .section-label {
                font-size: 0.6rem;
                font-weight: 700;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }

            .tickers-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .ticker-chip {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-full);
                transition: all 0.2s ease;
            }

            .ticker-chip:hover {
                border-color: var(--brand-secondary);
            }

            .ticker-name {
                font-size: 0.75rem;
                font-weight: 700;
                color: var(--text-primary);
            }

            .remove-btn {
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
                border: none;
                border-radius: var(--radius-full);
                background: transparent;
                color: var(--text-muted);
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .remove-btn:hover {
                background: var(--danger-light);
                color: var(--danger);
            }

            .empty-state {
                padding: 16px;
                text-align: center;
                color: var(--text-muted);
                font-size: 0.75rem;
            }

            .info-text {
                margin-top: 12px;
                padding: 10px 12px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-sm);
                font-size: 0.65rem;
                color: var(--text-muted);
                line-height: 1.5;
            }
        `
    ];

    constructor() {
        super();
        this.trackedTickers = [];
        this.newTicker = '';
        this.expanded = false;
        this.apiBase = '';
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadTickers();
    }

    async _loadTickers() {
        try {
            const response = await fetch(`${this.apiBase}/api/settings/tickers`);
            const data = await response.json();
            if (data.success) {
                this.trackedTickers = data.tickers || [];
            }
        } catch (error) {
            console.error('Error loading tickers:', error);
        }
    }

    _handleInput(e) {
        this.newTicker = e.target.value.toUpperCase();
    }

    _handleKeydown(e) {
        if (e.key === 'Enter') {
            this._addTicker();
        }
    }

    async _addTicker() {
        if (!this.newTicker.trim()) return;

        try {
            const response = await fetch(`${this.apiBase}/api/settings/tickers/${this.newTicker}`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                this.trackedTickers = data.tickers;
                this.newTicker = '';
                this._dispatchChange();
            } else {
                console.error('Error adding ticker:', data.error);
            }
        } catch (error) {
            console.error('Error adding ticker:', error);
        }
    }

    async _removeTicker(ticker) {
        try {
            const response = await fetch(`${this.apiBase}/api/settings/tickers/${ticker}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.success) {
                this.trackedTickers = data.tickers;
                this._dispatchChange();
            }
        } catch (error) {
            console.error('Error removing ticker:', error);
        }
    }

    _toggleExpanded() {
        this.expanded = !this.expanded;
    }

    _dispatchChange() {
        this.dispatchEvent(new CustomEvent('tickers-changed', {
            detail: { tickers: this.trackedTickers },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            <div class="config-card">
                <div class="config-header" @click="${this._toggleExpanded}">
                    <div class="header-left">
                        <div class="header-icon">⚙️</div>
                        <div class="header-text">
                            <span class="header-title">Configuration Tickers</span>
                            <span class="header-subtitle">Gérer les actions à analyser</span>
                        </div>
                    </div>
                    <div class="header-right">
                        <span class="ticker-count">${this.trackedTickers.length} suivis</span>
                        <span class="arrow">›</span>
                    </div>
                </div>

                <div class="config-content">
                    <div class="config-body">
                        <!-- Add Ticker -->
                        <div class="add-section">
                            <div class="add-row">
                                <input
                                    type="text"
                                    class="add-input"
                                    placeholder="Ajouter un ticker (ex: AAPL, MSFT)"
                                    .value="${this.newTicker}"
                                    @input="${this._handleInput}"
                                    @keydown="${this._handleKeydown}"
                                />
                                <button class="add-btn" @click="${this._addTicker}">
                                    + Ajouter
                                </button>
                            </div>
                        </div>

                        <!-- Tracked Tickers -->
                        <div class="tickers-section">
                            <div class="section-label">Tickers suivis</div>
                            ${this.trackedTickers.length === 0 ? html`
                                <div class="empty-state">
                                    Aucun ticker configuré. Ajoutez-en un ci-dessus.
                                </div>
                            ` : html`
                                <div class="tickers-grid">
                                    ${this.trackedTickers.map(ticker => html`
                                        <div class="ticker-chip">
                                            <span class="ticker-name">${ticker}</span>
                                            <button
                                                class="remove-btn"
                                                @click="${(e) => { e.stopPropagation(); this._removeTicker(ticker); }}"
                                                title="Retirer"
                                            >×</button>
                                        </div>
                                    `)}
                                </div>
                            `}
                            <div class="info-text">
                                💡 Les nouveaux tickers seront analysés lors du prochain cycle automatique.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('ticker-config', TickerConfig);
