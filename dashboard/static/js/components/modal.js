/**
 * Modal Component
 * Reusable modal dialog with backdrop
 * Supports different types: form, confirmation
 * 
 * Usage:
 * <app-modal
 *   title="Modal Title"
 *   type="form|confirmation"
 *   .open=${true}
 *   theme="dark"
 *   @close=${handleClose}
 *   @submit=${handleSubmit}
 * >
 *   <!-- Modal content goes here -->
 *   <div slot="body">Content</div>
 *   <div slot="footer">Optional footer buttons</div>
 * </app-modal>
 */

import { BaseComponent, html, css, sharedStyles } from './base-component.js';
import './button.js';

export class Modal extends BaseComponent {
  static properties = {
    ...BaseComponent.properties,
    // State
    open: { type: Boolean, reflect: true },
    
    // Content
    title: { type: String },
    type: { type: String }, // 'form', 'confirmation'
    
    // Confirmation type props
    confirmText: { type: String, attribute: 'confirm-text' },
    cancelText: { type: String, attribute: 'cancel-text' },
    confirmVariant: { type: String, attribute: 'confirm-variant' }, // danger, success, primary
    
    // Form type props
    submitText: { type: String, attribute: 'submit-text' },
    
    // Size
    size: { type: String } // 'sm', 'md', 'lg'
  };

  static styles = [
    sharedStyles,
    css`
      :host {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1000;
      }

      :host([open]) {
        display: block;
      }

      /* Backdrop */
      .backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.2s ease;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      /* Modal Container */
      .modal {
        position: relative;
        background: var(--bg-secondary);
        border-radius: var(--radius-lg, 16px);
        border: 2px solid var(--border-color);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        max-height: 85vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        animation: slideUp 0.25s ease;
        width: calc(100% - 24px);
        max-width: 420px;
        margin: 12px;
        box-sizing: border-box;
      }

      .modal.sm {
        max-width: 340px;
      }

      .modal.lg {
        max-width: 520px;
      }

      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translateY(20px) scale(0.98);
        }
        to {
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }

      /* Header */
      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        background: var(--bg-tertiary);
        flex-shrink: 0;
      }

      .modal-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .close-btn {
        background: none;
        border: none;
        font-size: 1.3rem;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 4px 8px;
        line-height: 1;
        border-radius: var(--radius-sm, 6px);
        transition: all 0.2s ease;
      }

      .close-btn:hover {
        background: var(--bg-hover);
        color: var(--text-primary);
      }

      /* Body */
      .modal-body {
        padding: 16px;
        overflow-y: auto;
        overflow-x: hidden;
        flex: 1;
      }

      /* Footer */
      .modal-footer {
        display: flex;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid var(--border-color);
        background: var(--bg-tertiary);
        justify-content: flex-end;
        flex-shrink: 0;
      }

      .modal-footer.center {
        justify-content: center;
      }

      .modal-footer.right {
        justify-content: flex-end;
      }

      .modal-footer app-button {
        flex: 0 0 auto;
        min-width: 100px;
      }

      /* Confirmation type styling */
      .confirmation-message {
        text-align: center;
        padding: 20px 0;
      }

      .confirmation-icon {
        font-size: 3rem;
        margin-bottom: 16px;
      }

      .confirmation-text {
        font-size: 1rem;
        color: var(--text-primary);
        margin-bottom: 8px;
      }

      .confirmation-subtext {
        font-size: 0.85rem;
        color: var(--text-secondary);
      }
    `
  ];

  constructor() {
    super();
    this.open = false;
    this.title = '';
    this.type = 'form';
    this.confirmText = 'Confirmer';
    this.cancelText = 'Annuler';
    this.confirmVariant = 'primary';
    this.submitText = 'Enregistrer';
    this.size = 'md';
    this._isSubmitting = false;
  }

  connectedCallback() {
    super.connectedCallback();
    // Close on escape key
    this._handleEscape = (e) => {
      if (e.key === 'Escape' && this.open) {
        this._handleClose();
      }
    };
    document.addEventListener('keydown', this._handleEscape);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('keydown', this._handleEscape);
    // Ensure body scroll is restored
    document.body.style.overflow = '';
  }

  updated(changedProperties) {
    super.updated?.(changedProperties);
    if (changedProperties.has('open')) {
      // Lock/unlock body scroll
      document.body.style.overflow = this.open ? 'hidden' : '';
      // Reset submitting state when modal opens or closes
      this._isSubmitting = false;
    }
  }

  _handleClose() {
    this.emit('close');
  }

  _handleBackdropClick(e) {
    if (e.target === e.currentTarget) {
      this._handleClose();
    }
  }

  _handleSubmit() {
    // Prevent double submit
    if (this._isSubmitting) {
      console.log('⚠️ Modal: Already submitting, ignoring...');
      return;
    }
    this._isSubmitting = true;
    console.log('📤 Modal: Submit event emitted');
    this.emit('submit');
    // Reset after a short delay (the parent should close the modal anyway)
    setTimeout(() => {
      this._isSubmitting = false;
    }, 500);
  }

  _handleConfirm() {
    // Prevent double confirm
    if (this._isSubmitting) {
      console.log('⚠️ Modal: Already confirming, ignoring...');
      return;
    }
    this._isSubmitting = true;
    console.log('📤 Modal: Confirm event emitted');
    this.emit('confirm');
    setTimeout(() => {
      this._isSubmitting = false;
    }, 500);
  }

  _handleCancel() {
    this.emit('cancel');
    this._handleClose();
  }

  render() {
    if (!this.open) return html``;

    return html`
      <div class="backdrop" @click=${this._handleBackdropClick}>
        <div class="modal ${this.size}">
          <!-- Header -->
          <div class="modal-header">
            <h2 class="modal-title">${this.title}</h2>
            <button class="close-btn" @click=${this._handleClose}>×</button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            ${this.type === 'confirmation' ? this._renderConfirmation() : ''}
            <slot name="body"></slot>
          </div>

          <!-- Footer -->
          ${this._renderFooter()}
        </div>
      </div>
    `;
  }

  _renderConfirmation() {
    return html`
      <div class="confirmation-message">
        <div class="confirmation-icon">
          ${this.confirmVariant === 'danger' ? '⚠️' : 
            this.confirmVariant === 'success' ? '✅' : 'ℹ️'}
        </div>
        <slot name="message"></slot>
      </div>
    `;
  }

  _renderFooter() {
    // Check if custom footer is provided
    const hasCustomFooter = this.querySelector('[slot="footer"]');
    
    if (hasCustomFooter) {
      return html`
        <div class="modal-footer right">
          <slot name="footer"></slot>
        </div>
      `;
    }

    // Default footers based on type
    if (this.type === 'confirmation') {
      return html`
        <div class="modal-footer center">
          <app-button
            variant="secondary"
            label="${this.cancelText}"
            theme="${this.theme}"
            @click=${this._handleCancel}
          ></app-button>
          <app-button
            variant="${this.confirmVariant}"
            label="${this.confirmText}"
            theme="${this.theme}"
            @click=${this._handleConfirm}
          ></app-button>
        </div>
      `;
    }

    // Form type
    return html`
      <div class="modal-footer right">
        <app-button
          variant="secondary"
          label="${this.cancelText}"
          theme="${this.theme}"
          @click=${this._handleCancel}
        ></app-button>
        <app-button
          variant="primary"
          label="${this.submitText}"
          theme="${this.theme}"
          @click=${this._handleSubmit}
        ></app-button>
      </div>
    `;
  }
}

customElements.define('app-modal', Modal);
