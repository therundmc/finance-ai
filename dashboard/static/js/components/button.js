/**
 * Button Component
 * Versatile button for filter tabs, action buttons, and more
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';

export class Button extends BaseComponent {
  static properties = {
    ...super.properties,
    // Content
    label: { type: String },
    icon: { type: String },
    
    // Variant
    variant: { type: String }, // 'filter', 'primary', 'secondary', 'success', 'danger', 'icon'
    
    // State
    active: { type: Boolean, reflect: true },
    disabled: { type: Boolean, reflect: true },
    loading: { type: Boolean },
    
    // Size
    size: { type: String }, // 'sm', 'md', 'lg'
    
    // Style
    fullWidth: { type: Boolean, attribute: 'full-width' }
  };
  
  static styles = [
    sharedStyles,
    css`
      :host {
        display: inline-block;
      }
      
      :host([full-width]) {
        display: block;
      }
      
      :host([disabled]) {
        opacity: 0.5;
        pointer-events: none;
      }
      
      .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 10px 20px;
        border: 2px solid var(--border-color);
        border-radius: var(--radius-full);
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        cursor: pointer;
        transition: all var(--transition-fast);
        white-space: nowrap;
        text-decoration: none;
        line-height: 1;
        user-select: none;
      }
      
      .label {
        display: inline-block;
      }
      
      .icon {
        display: inline-block;
        flex-shrink: 0;
      }
      
      :host([full-width]) .button {
        width: 100%;
      }
      
      .button:hover {
        background: var(--bg-hover);
        border-color: var(--brand-secondary);
        color: var(--brand-secondary);
      }
      
      .button:active {
        transform: scale(0.98);
      }
      
      /* Filter Tab Variant */
      .button.filter {
        padding: 8px 16px;
        font-size: 0.8rem;
      }
      
      .button.filter:hover,
      :host([active]) .button.filter {
        background-color: var(--brand-secondary);
        background-image: linear-gradient(135deg, var(--brand-secondary) 0%, var(--brand-pink) 100%);
        background-size: 100% 100%;
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
      }
      
      /* Primary Variant */
      .button.primary {
        background-color: var(--brand-primary);
        background-image: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
        background-size: 100% 100%;
        color: white;
        border: none;
        box-shadow: 0 2px 8px rgba(255, 51, 102, 0.3);
      }
      
      .button.primary:hover {
        filter: brightness(1.1);
        box-shadow: 0 6px 20px rgba(255, 51, 102, 0.3);
        border: none;
      }
      
      /* Secondary Variant */
      .button.secondary {
        background: var(--bg-secondary);
        border-color: var(--border-color);
        color: var(--text-primary);
      }
      
      .button.secondary:hover {
        background: var(--bg-hover);
        border-color: var(--brand-secondary);
      }
      
      /* Success Variant */
      .button.success {
        background: var(--success-light);
        border-color: var(--success-border);
        color: var(--success);
      }
      
      .button.success:hover {
        background: rgba(6, 214, 160, 0.2);
        border-color: var(--success);
      }
      
      /* Danger Variant */
      .button.danger {
        background: var(--danger-light);
        border-color: var(--danger-border);
        color: var(--danger);
      }
      
      .button.danger:hover {
        background: var(--danger);
        color: white;
        border-color: var(--danger);
      }
      
      /* Icon Only Mode - when no label */
      .button:not(:has(.label)) {
        padding: 10px;
        min-width: 40px;
        height: 40px;
        border-radius: var(--radius-full);
      }
      
      .button.sm:not(:has(.label)) {
        padding: 8px;
        min-width: 32px;
        height: 32px;
      }
      
      /* Icon Only Variant */
      .button.icon {
        padding: 8px;
        width: 32px;
        height: 32px;
        min-width: 32px;
        border-radius: var(--radius-full);
      }
      
      .button.icon .label {
        display: none;
      }
      
      /* Sizes */
      .button.sm {
        padding: 6px 12px;
        font-size: 0.75rem;
      }
      
      .button.sm.icon {
        padding: 6px;
        width: 28px;
        height: 28px;
        min-width: 28px;
      }
      
      .button.lg {
        padding: 14px 28px;
        font-size: 1rem;
      }
      
      .button.lg.icon {
        padding: 12px;
        width: 40px;
        height: 40px;
        min-width: 40px;
      }
      
      /* Icon */
      .icon {
        font-size: 1em;
        flex-shrink: 0;
      }
      
      /* Label */
      .label {
        flex: 1;
      }
      
      :host([full-width]) .label {
        text-align: center;
      }
      
      /* Loading State */
      .spinner {
        width: 14px;
        height: 14px;
        border: 2px solid currentColor;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
      }
      
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      
      .button.loading {
        pointer-events: none;
      }
      
      .button.loading .icon,
      .button.loading .label {
        opacity: 0.5;
      }
    `
  ];
  
  constructor() {
    super();
    this.label = '';
    this.icon = '';
    this.variant = 'secondary';
    this.active = false;
    this.disabled = false;
    this.loading = false;
    this.size = 'md';
    this.fullWidth = false;
  }
  
  _handleClick(e) {
    if (this.disabled || this.loading) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    
    this.emit('click', { originalEvent: e });
  }
  
  render() {
    const classes = [
      'button',
      this.variant,
      this.size,
      this.loading ? 'loading' : ''
    ].filter(Boolean).join(' ');
    
    return html`
      <button
        class=${classes}
        ?disabled=${this.disabled}
        @click=${this._handleClick}
      >
        ${this.loading ? html`<span class="spinner"></span>` : ''}
        ${this.icon ? html`<span class="icon">${this.icon}</span>` : ''}
        ${this.label ? html`<span class="label">${this.label}</span>` : ''}
        <slot></slot>
      </button>
    `;
  }
}

customElements.define('app-button', Button);
