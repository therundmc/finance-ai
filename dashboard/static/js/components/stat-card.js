/**
 * Stat Card Component (unified)
 * Displays a statistic with label and value
 * Supports auto-coloring for P&L values
 * Matches original app theme (variables.css)
 * 
 * Usage:
 * <!-- Basic stat -->
 * <stat-card label="Positions" value="5"></stat-card>
 * 
 * <!-- With currency -->
 * <stat-card label="Valeur" value="12450" currency="USD"></stat-card>
 * 
 * <!-- Auto P&L coloring (positive = green, negative = red) -->
 * <stat-card label="P&L Net" value="1234.56" currency="USD" auto-color></stat-card>
 * <stat-card label="P&L Net" value="-500" currency="EUR" auto-color></stat-card>
 * 
 * <!-- Manual variant -->
 * <stat-card label="Alert" value="3" variant="danger"></stat-card>
 * 
 * <!-- With sign prefix for numbers -->
 * <stat-card label="Change" value="2.5" suffix="%" show-sign></stat-card>
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';

export class StatCard extends BaseComponent {
  static properties = {
    ...super.properties,
    label: { type: String },
    value: { type: String },      // Can be string or number
    currency: { type: String },   // USD, EUR, CHF, GBP - adds symbol prefix
    prefix: { type: String },     // Manual prefix
    suffix: { type: String },     // Manual suffix (%, etc.)
    variant: { type: String },    // primary, success, danger, secondary, neutral
    size: { type: String },       // normal, small
    loading: { type: Boolean },
    autoColor: { type: Boolean, attribute: 'auto-color' },  // Auto green/red based on value
    showSign: { type: Boolean, attribute: 'show-sign' },    // Show +/- prefix
    hideValue: { type: Boolean, attribute: 'hide-value' }   // Hide value with asterisks
  };

  static styles = [
    sharedStyles,
    css`

      :host {
        display: block;
      }


      .stat-card {
        position: relative;
        padding: var(--spacing-sm);
        background: rgba(255,255,255,0.18);
        border-radius: 16px;
        box-shadow: 0 4px 24px 0 rgba(31,38,135,0.18), 0 1.5px 4px 0 rgba(0,0,0,0.10);
        border: 1px solid rgba(120,120,120,0.13);
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        text-align: center;
        overflow: hidden;
        transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
        min-height: 110px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-left: 0;
        margin-right: 0;
      }

      :host([theme="dark"]) .stat-card {
        background: rgba(31, 27, 24, 0.5);
        /* Blend a soft white and a soft dark shadow for realism */
        box-shadow: 0 2px 12px 0 rgba(0,0,0,0.32), 0 1.5px 8px 0 rgba(255,255,255,0.08);
      }

      .stat-card:hover {
        border: 1.5px solid var(--primary, #6c63ff);
      }

      .stat-card.danger .stat-value {
        background: linear-gradient(90deg, #ff3366, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
      }
      .stat-card.danger .currency-symbol {
        -webkit-text-fill-color: #ff3366;
      }
      .stat-card.danger:hover {
        border-color: var(--danger) !important;
        box-shadow: 0 4px 16px rgba(255, 51, 102, 0.25);
      }

      .stat-card.primary .value-text {
        background: linear-gradient(90deg, #ff6bed, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .stat-card.secondary .value-text {
        background: linear-gradient(90deg, #7c3aed, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
      }

      .stat-card.warning .value-text {
        background: linear-gradient(90deg, #ffb347, #ffc107);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
      }

      /* Label */
      .stat-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }

      /* Value */
      .stat-value {
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.3px;
        line-height: 1.2;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2px;
      }

      .currency-symbol {
        font-size: 0.75em;
        opacity: 0.9;
        color: var(--text-secondary);
      }

      /* Small size */
      :host([size="small"]) .stat-card {
        min-height: 60px;
        padding-right: var(--spacing-xs);
        padding-left: var(--spacing-xs);
        padding-top: var(--spacing-sm);
        padding-bottom: var(--spacing-sm);
      }
      :host([size="small"]) .stat-label {
        font-size: 0.6rem;
        margin-bottom: 4px;
      }
      :host([size="small"]) .stat-value {
        font-size: 1rem;
      }

      /* Loading state */
      .loading .stat-value {
        background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        color: transparent;
        border-radius: 4px;
      }

      @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `
  ];

  constructor() {
    super();
    this.label = '';
    this.value = '-';
    this.currency = '';
    this.prefix = '';
    this.suffix = '';
    this.variant = 'neutral';
    this.size = 'normal';
    this.loading = false;
    this.autoColor = false;
    this.showSign = false;
    this.hideValue = false;
  }

  get numericValue() {
    const num = parseFloat(String(this.value).replace(/[^0-9.-]/g, ''));
    return isNaN(num) ? 0 : num;
  }

  get isPositive() {
    return this.numericValue >= 0;
  }

  get computedVariant() {
    if (this.autoColor) {
      return this.isPositive ? 'success' : 'danger';
    }
    return this.variant;
  }

  get currencySymbol() {
    if (!this.currency) return '';
    const symbols = { USD: '$', EUR: '€', CHF: 'CHF ', GBP: '£' };
    return symbols[this.currency] || '';
  }

  get formattedValue() {
    // If hideValue is true, return asterisks
    if (this.hideValue) {
      return '••••••';
    }
    
    let val = this.value;
    
    // If it's a number, format it
    if (!isNaN(parseFloat(val))) {
      const num = parseFloat(val);
      val = Math.abs(num).toFixed(2);
    }
    
    // Build the display string
    let display = '';
    
    // Sign prefix
    if (this.showSign || this.autoColor) {
      display += this.isPositive ? '+' : '-';
    } else if (this.numericValue < 0 && !this.autoColor) {
      display += '-';
      val = String(val).replace('-', '');
    }
    
    // Currency or manual prefix
    display += this.currencySymbol || this.prefix;
    
    // Value (remove negative sign if we already added it)
    display += String(val).replace('-', '');
    
    // Suffix
    display += this.suffix;
    
    return display;
  }

  render() {
    const currSymbol = this.currencySymbol || this.prefix;
    const hasSymbol = !!currSymbol;
    
    // Build value parts
    let signPrefix = '';
    let val = this.value;
    
    if (!this.hideValue) {
      // If it's a number, format it
      if (!isNaN(parseFloat(val))) {
        const num = parseFloat(val);
        // Only use decimals if currency is present or if it's not a whole number
        if (this.currency || num % 1 !== 0) {
          val = Math.abs(num).toFixed(2);
        } else {
          val = Math.abs(num).toString();
        }
      }
      
      // Sign prefix
      if (this.showSign || this.autoColor) {
        signPrefix = this.isPositive ? '+' : '-';
      } else if (this.numericValue < 0 && !this.autoColor) {
        signPrefix = '-';
        val = String(val).replace('-', '');
      }
      
      // Remove negative sign if we already added it
      val = String(val).replace('-', '');
    } else {
      val = '••••••';
    }
    
    return html`
      <div class="stat-card ${this.computedVariant} ${this.loading ? 'loading' : ''}">
        <div class="stat-label">${this.label}</div>
        <div class="stat-value">
          ${signPrefix}<span class="currency-symbol">${currSymbol}</span><span class="value-text">${val}</span>${this.suffix}
        </div>
      </div>
    `;
  }
}

customElements.define('stat-card', StatCard);
