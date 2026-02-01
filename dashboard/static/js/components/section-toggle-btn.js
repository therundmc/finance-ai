/**
 * Section Toggle Button Component
 * Used for main section navigation (Portfolio/Analysis tabs)
 */
import { BaseComponent, html, css, sharedStyles } from './base-component.js';

export class SectionToggleBtn extends BaseComponent {
  static properties = {
    ...super.properties,
    // Content
    label: { type: String },
    icon: { type: String },
    
    // State
    active: { type: Boolean, reflect: true },
    disabled: { type: Boolean, reflect: true }
  };
  
  static styles = [
    sharedStyles,
    css`
      :host {
        flex: 1 1 0%;
        display: block;
        min-width: 0;
      }

      /* Removed sticky/fixed logic, let .main-section-toggle handle positioning */

      :host([disabled]) {
        opacity: 0.5;
        pointer-events: none;
      }

      .toggle-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 10px 18px;
        border: none;
        background: transparent;
        border-radius: var(--radius-full);
        font-size: var(--button-font-size, 0.85rem);
        font-weight: 600;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        font-family: 'Poppins', sans-serif;
        user-select: none;
        box-shadow: none;
        position: relative;
        overflow: hidden;
        background-clip: padding-box;
      }

      .toggle-btn::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        opacity: 0;
        transition: opacity 0.3s ease;
        border-radius: inherit;
      }

      .toggle-btn:hover::before {
        opacity: 1;
      }

      .toggle-btn:hover {
        color: var(--text-primary);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2),
                    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
      }

      :host([active]) .toggle-btn {
        background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
        color: white;
        box-shadow: 0 4px 20px rgba(255, 51, 102, 0.4),
                    0 8px 40px rgba(124, 58, 237, 0.2);
      }

      /* Clair theme fix */
      [data-theme="clair"] section-toggle-btn .toggle-btn,
      section-toggle-btn[theme="clair"] .toggle-btn {
        background: var(--bg-secondary, #f8fafc) !important;
        color: var(--text-primary, #1e293b) !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
      }

      :host([active]) .toggle-btn::before {
        opacity: 0;
      }

      :host([active]) .toggle-btn:hover {
        filter: brightness(1.1);
        box-shadow: 0 6px 25px rgba(255, 51, 102, 0.5),
                    0 10px 45px rgba(124, 58, 237, 0.3);
      }

      .toggle-icon {
        font-size: var(--button-icon-size, 0.9rem);
        flex-shrink: 0;
        position: relative;
        z-index: 1;
      }

      .toggle-label {
        white-space: nowrap;
        position: relative;
        z-index: 1;
      }
    `
  ];
  
  constructor() {
    super();
    this.label = '';
    this.icon = '';
    this.active = false;
    this.disabled = false;
  }
  
  _handleClick(e) {
    if (this.disabled) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    
    this.emit('toggle', { label: this.label });
  }
  
  render() {
    return html`
      <button
        class="toggle-btn"
        ?disabled=${this.disabled}
        @click=${this._handleClick}
      >
        ${this.icon ? html`<span class="toggle-icon">${this.icon}</span>` : ''}
        ${this.label ? html`<span class="toggle-label">${this.label}</span>` : ''}
        <slot></slot>
      </button>
    `;
  }
}

customElements.define('section-toggle-btn', SectionToggleBtn);
