/**
 * Toast Notification Component
 * Beautiful toast notifications matching the app style
 * Appears in top-right corner
 */
import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export class ToastNotification extends LitElement {
    static properties = {
        message: { type: String },
        type: { type: String }, // 'success', 'error', 'info', 'warning'
        duration: { type: Number },
        visible: { type: Boolean, reflect: true }
    };


    static styles = css`
        :host {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 8px;
            pointer-events: none;
        }

        .toast {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: rgba(255,255,255,0.18);
            box-shadow: 0 2px 8px 0 rgba(31,38,135,0.10);
            backdrop-filter: blur(14px) saturate(160%);
            -webkit-backdrop-filter: blur(14px) saturate(160%);
            color: var(--text-primary, #f5f0eb);
            font-size: 0.85rem;
            font-weight: 500;
            font-family: 'Poppins', sans-serif;
            pointer-events: auto;
            animation: slideIn 0.3s ease;
            max-width: 320px;
            margin-left: 0;
            margin-right: 0;
            overflow-x: visible;
        }

        :host([theme="dark"]) .toast {
            background: rgba(31, 27, 24, 0.5);
            box-shadow: 0 2px 8px 0 rgba(0,0,0,0.13);
        }

        .toast.hiding {
            animation: slideOut 0.3s ease forwards;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }

        .toast-message {
            flex: 1;
            line-height: 1.4;
        }

        .toast-close {
            background: none;
            border: none;
            color: var(--text-secondary, #a89f94);
            cursor: pointer;
            padding: 4px;
            font-size: 1rem;
            line-height: 1;
            opacity: 0.7;
            transition: opacity 0.2s ease;
        }

        .toast-close:hover {
            opacity: 1;
        }

        /* Type variants */
        .toast.success {
            border-left: 4px solid var(--success, #06d6a0);
        }

        .toast.success {
            color: var(--success, #06d6a0);
        }

        .toast.error {
            border-left: 4px solid var(--danger, #ff3366);
        }

        .toast.error {
            color: var(--danger, #ff3366);
        }

        .toast.warning {
            border-left: 4px solid var(--brand-warm, #ffb347);
        }

        .toast.warning {
            color: var(--brand-warm, #ffb347);
        }

        .toast.info {
            border-left: 4px solid var(--brand-secondary, #8b5cf6);
        }

        .toast.info {
            color: var(--brand-secondary, #8b5cf6);
        }

        /* Progress bar */
        .toast-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: currentColor;
            opacity: 0.3;
            animation: progress linear forwards;
        }

        .toast.success .toast-progress { background: var(--success, #06d6a0); }
        .toast.error .toast-progress { background: var(--danger, #ff3366); }
        .toast.warning .toast-progress { background: var(--brand-warm, #ffb347); }
        .toast.info .toast-progress { background: var(--brand-secondary, #8b5cf6); }

        @keyframes progress {
            from { width: 100%; }
            to { width: 0%; }
        }
    `;

    constructor() {
        super();
        this._toasts = [];
    }

    show(message, type = 'success', duration = 3000) {
        const id = Date.now();
        const toast = { id, message, type, duration, hiding: false };
        this._toasts = [...this._toasts, toast];
        this.requestUpdate();

        // Auto-remove after duration
        setTimeout(() => {
            this._hideToast(id);
        }, duration);

        return id;
    }

    _hideToast(id) {
        this._toasts = this._toasts.map(t => 
            t.id === id ? { ...t, hiding: true } : t
        );
        this.requestUpdate();

        // Remove from DOM after animation
        setTimeout(() => {
            this._toasts = this._toasts.filter(t => t.id !== id);
            this.requestUpdate();
        }, 300);
    }

    _handleClose(id) {
        this._hideToast(id);
    }

    render() {
        return html`
            ${this._toasts.map(toast => html`
                <div class="toast ${toast.type} ${toast.hiding ? 'hiding' : ''}" style="position: relative;">
                    <span class="toast-message">${toast.message}</span>
                    <button class="toast-close" @click=${() => this._handleClose(toast.id)}>×</button>
                    <div class="toast-progress" style="animation-duration: ${toast.duration}ms;"></div>
                </div>
            `)}
        `;
    }
}

customElements.define('toast-notification', ToastNotification);

// Global toast instance
let toastInstance = null;

export function getToastInstance() {
    if (!toastInstance) {
        toastInstance = document.querySelector('toast-notification');
        if (!toastInstance) {
            toastInstance = document.createElement('toast-notification');
            document.body.appendChild(toastInstance);
        }
    }
    return toastInstance;
}

export function showToast(message, type = 'success', duration = 3000) {
    const instance = getToastInstance();
    return instance.show(message, type, duration);
}
