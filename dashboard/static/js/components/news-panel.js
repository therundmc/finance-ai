/**
 * News Panel Component
 * Displays AI-generated news summaries with category tabs
 */
import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';
import { BaseComponent, sharedStyles } from './base-component.js';

export class NewsPanel extends BaseComponent {
  static properties = {
    ...BaseComponent.properties,
    summaries: { type: Object },
    activeCategory: { type: String },
    loading: { type: Boolean },
    expanded: { type: Boolean, reflect: true },
    lastFetch: { type: String },
    apiBase: { type: String, attribute: 'api-base' }
  };

  static styles = [
    sharedStyles,
    css`
      :host {
        display: block;
      }

      .news-panel {
        background: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        transition: all 0.25s ease;
      }

      /* Header */
      .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 14px;
        cursor: pointer;
        user-select: none;
      }

      .panel-header:hover {
        background: var(--bg-tertiary);
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .panel-title {
        font-size: 0.9rem;
        font-weight: 800;
        color: var(--text-primary);
      }

      .last-update {
        font-size: 0.7rem;
        color: var(--text-muted);
      }

      .toggle-icon {
        font-size: 1.2rem;
        color: var(--text-muted);
        transition: transform 0.3s ease;
      }

      :host([expanded]) .toggle-icon {
        transform: rotate(90deg);
        color: var(--brand-secondary);
      }

      /* Content */
      .panel-content {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.35s ease;
      }

      :host([expanded]) .panel-content {
        max-height: 1000px;
        overflow-y: auto;
      }

      .content-inner {
        padding: 12px 14px 24px;
      }

      /* Category Tabs */
      .category-tabs {
        display: flex;
        gap: 6px;
        margin-bottom: 12px;
        flex-wrap: wrap;
      }

      .category-tab {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        background: var(--bg-tertiary);
        border: 2px solid var(--border-color);
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .category-tab:hover {
        border-color: var(--brand-secondary);
        color: var(--brand-secondary);
      }

      .category-tab.active {
        background: linear-gradient(135deg, var(--brand-secondary), var(--brand-pink));
        border-color: transparent;
        color: white;
      }

      .tab-icon {
        font-size: 0.9rem;
      }

      /* Summary Card */
      .summary-card {
        transition: all 0.2s ease;
      }

      .summary-header {
        display: none;
      }

      .summary-icon {
        font-size: 1.2rem;
      }

      .summary-title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
      }

      .summary-count {
        font-size: 0.7rem;
        color: var(--text-muted);
        background: var(--bg-secondary);
        padding: 3px 8px;
        border-radius: 999px;
        margin-left: auto;
      }

      .summary-text {
        font-size: 0.85rem;
        line-height: 1.6;
        color: var(--text-secondary);
      }

      .summary-sources {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed var(--border-color);
        font-size: 0.7rem;
        color: var(--text-muted);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .sources-label {
        font-weight: 600;
        color: var(--text-secondary);
      }

      .fallback-warning {
        margin-top: 10px;
        padding: 6px 10px;
        background: rgba(255, 179, 71, 0.15);
        border-radius: var(--radius-sm);
        font-size: 0.7rem;
        color: #ffb347;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      /* Empty State */
      .empty-state {
        text-align: center;
        padding: 30px 20px;
        color: var(--text-muted);
      }

      .empty-icon {
        font-size: 2.5rem;
        display: block;
        margin-bottom: 10px;
        opacity: 0.5;
      }

      .empty-text {
        font-size: 0.85rem;
        margin: 0;
      }

      /* Skeleton Loading */
      .skeleton {
        background: linear-gradient(90deg,
          var(--bg-secondary) 25%,
          var(--bg-tertiary) 50%,
          var(--bg-secondary) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: var(--radius-sm);
      }

      @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }

      .skeleton-line {
        height: 16px;
        margin-bottom: 8px;
        border-radius: 4px;
      }

      .skeleton-header {
        height: 24px;
        width: 150px;
        margin-bottom: 12px;
      }
    `
  ];

  static CATEGORIES = {
    my_stocks: { label: 'Mes Actions', icon: '📊' },
    market: { label: 'Marché', icon: '🌍' },
    tech: { label: 'Tech', icon: '💻' }
  };

  constructor() {
    super();
    this.summaries = {};
    this.activeCategory = 'my_stocks';
    this.loading = false;
    this.expanded = false;
    this.lastFetch = null;
    this.apiBase = '';
    this._newsEventSource = null; // SSE connection
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadSummaries(); // Initial load
    this._connectNewsStream(); // Start SSE connection
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._disconnectNewsStream(); // Clean up SSE connection
  }

  async _loadSummaries() {
    if (this.loading) return;
    
    this.loading = true;
    
    try {
      const response = await fetch(`${this.apiBase}/api/news/summary?category=all`);
      const data = await response.json();
      
      if (data.success && data.summaries) {
        this.summaries = data.summaries;
        this.lastFetch = data.generated_at ? new Date(data.generated_at).toLocaleTimeString('fr-CH', {
          hour: '2-digit',
          minute: '2-digit'
        }) : null;
      }
    } catch (error) {
      console.error('Error loading news summaries:', error);
    } finally {
      this.loading = false;
    }
  }

  _connectNewsStream() {
    // Disconnect existing stream if any
    this._disconnectNewsStream();
    
    // Create new EventSource for SSE
    this._newsEventSource = new EventSource(`${this.apiBase}/api/stream/news`);
    
    this._newsEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.success && data.summaries) {
          console.log('📡 Received news update via SSE');
          this.summaries = data.summaries;
          this.lastFetch = data.generated_at ? new Date(data.generated_at).toLocaleTimeString('fr-CH', {
            hour: '2-digit',
            minute: '2-digit'
          }) : new Date().toLocaleTimeString('fr-CH', {
            hour: '2-digit',
            minute: '2-digit'
          });
          this.requestUpdate();
        }
      } catch (error) {
        console.error('❌ Error processing SSE news update:', error);
      }
    };

    this._newsEventSource.onerror = (error) => {
      console.error('❌ SSE news connection error:', error);
      // Auto-reconnect after 10 seconds
      setTimeout(() => {
        console.log('🔄 Reconnecting to news stream...');
        this._connectNewsStream();
      }, 10000);
    };

    this._newsEventSource.onopen = () => {
      console.log('✅ Connected to news stream (SSE)');
    };
  }

  _disconnectNewsStream() {
    if (this._newsEventSource) {
      this._newsEventSource.close();
      this._newsEventSource = null;
      console.log('⏹️ Disconnected from news stream');
    }
  }

  _toggle() {
    this.expanded = !this.expanded;
  }

  _setCategory(category) {
    this.activeCategory = category;
  }

  _formatLastFetch() {
    if (!this.lastFetch) return '';
    return `Mis à jour à ${this.lastFetch}`;
  }

  render() {
    return html`
      <div class="news-panel">
        <div class="panel-header" @click="${this._toggle}">
          <div class="header-left">
            <span class="panel-title">📰 Actualités</span>
            ${this.lastFetch ? html`
              <span class="last-update">${this._formatLastFetch()}</span>
            ` : ''}
          </div>
          <span class="toggle-icon">›</span>
        </div>
        
        <div class="panel-content">
          <div class="content-inner">
            ${this._renderTabs()}
            ${this.loading ? this._renderSkeleton() : this._renderSummary()}
          </div>
        </div>
      </div>
    `;
  }

  _renderTabs() {
    return html`
      <div class="category-tabs">
        ${Object.entries(NewsPanel.CATEGORIES).map(([key, cat]) => html`
          <button 
            class="category-tab ${this.activeCategory === key ? 'active' : ''}"
            @click="${(e) => { e.stopPropagation(); this._setCategory(key); }}"
          >
            <span class="tab-icon">${cat.icon}</span>
            <span>${cat.label}</span>
          </button>
        `)}
      </div>
    `;
  }

  _renderSummary() {
    const data = this.summaries[this.activeCategory];
    const catInfo = NewsPanel.CATEGORIES[this.activeCategory];
    
    if (!data || !data.summary) {
      return html`
        <div class="empty-state">
          <span class="empty-icon">📰</span>
          <p class="empty-text">Résumés générés chaque matin à 7h</p>
        </div>
      `;
    }

    const sources = data.sources?.join(', ') || '';
    const articleCount = data.article_count || 0;
    const isFallback = data.is_fallback || false;

    return html`
      <div class="summary-card">
        <div class="summary-text">${data.summary}</div>
        ${sources || articleCount ? html`
          <div class="summary-sources">
            <span class="sources-label">${sources ? `Sources: ${sources}` : ''}</span>
            <span class="article-count">${articleCount} article${articleCount > 1 ? 's' : ''}</span>
          </div>
        ` : ''}
        ${isFallback ? html`
          <div class="fallback-warning">
            <span>⚠️</span> Résumé simplifié (IA non disponible)
          </div>
        ` : ''}
      </div>
    `;
  }

  _renderSkeleton() {
    return html`
      <div class="summary-card">
        <div class="skeleton skeleton-header"></div>
        <div class="skeleton skeleton-line" style="width: 100%"></div>
        <div class="skeleton skeleton-line" style="width: 95%"></div>
        <div class="skeleton skeleton-line" style="width: 85%"></div>
        <div class="skeleton skeleton-line" style="width: 70%"></div>
      </div>
    `;
  }
}

customElements.define('news-panel', NewsPanel);
