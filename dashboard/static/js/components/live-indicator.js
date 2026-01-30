/**
 * Live Data Indicator Component
 * Shows pulsing indicator when SSE data is being received
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';

export class LiveIndicator extends LitElement {
    static properties = {
        active: { type: Boolean },
        label: { type: String },
        size: { type: String }
    };

    static styles = css`
        :host {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .indicator-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-secondary);
            transition: all 0.3s ease;
        }

        .indicator-dot.small {
            width: 6px;
            height: 6px;
        }

        .indicator-dot.large {
            width: 10px;
            height: 10px;
        }

        .indicator-dot.active {
            background: var(--success-color);
            box-shadow: 0 0 0 0 var(--success-color);
            animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse-ring {
            0% {
                box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
            }
            50% {
                box-shadow: 0 0 0 4px rgba(34, 197, 94, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
            }
        }

        .indicator-label {
            font-size: 0.7rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }

        .indicator-label.active {
            color: var(--success-color);
        }
    `;

    constructor() {
        super();
        this.active = false;
        this.label = 'LIVE';
        this.size = 'medium';
    }

    render() {
        return html`
            <span class="indicator-dot ${this.size} ${this.active ? 'active' : ''}"></span>
        `;
    }

    // Public method to flash indicator on data update
    flash(duration = 2000) {
        this.active = true;
        setTimeout(() => {
            this.active = false;
        }, duration);
    }
}

customElements.define('live-indicator', LiveIndicator);
