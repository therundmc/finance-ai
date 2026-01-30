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
        flex: 1;
        display: block;
      }
      
      :host([disabled]) {
        opacity: 0.5;
        pointer-events: none;
      }
      
      .toggle-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 16px;
        border: none;
        background: transparent;
        border-radius: var(--radius-full);
        font-size: var(--button-font-size, 0.8rem);
        font-weight: 600;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.25s ease;
        width: 100%;
        font-family: 'Poppins', sans-serif;
        user-select: none;
      }
      
      .toggle-btn:hover {
        color: var(--text-primary);
        background: var(--bg-tertiary);
      }
      
      :host([active]) .toggle-btn {
        background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
        color: white;
        box-shadow: 0 2px 8px rgba(255, 51, 102, 0.3);
      }
      
      :host([active]) .toggle-btn:hover {
        filter: brightness(1.1);
      }
      
      .toggle-icon {
        font-size: var(--button-icon-size, 0.9rem);
        flex-shrink: 0;
      }
      
      .toggle-label {
        white-space: nowrap;
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
