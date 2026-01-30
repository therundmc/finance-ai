import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export class FormDropdown extends LitElement {
    static properties = {
        label: { type: String },
        name: { type: String },
        value: { type: String },
        options: { type: Array },
        required: { type: Boolean },
        disabled: { type: Boolean },
        theme: { type: String, reflect: true },
        size: { type: String, reflect: true }  // 'normal', 'small'
    };

    static styles = css`
        :host {
            display: block;
            width: 100%;
        }

        .dropdown-wrapper {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .label {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted, #888);
        }

        .dropdown {
            width: 100%;
            padding: 10px 14px;
            background: var(--bg-tertiary, #1a1a2e);
            border: 2px solid var(--border-color, #333);
            border-radius: var(--radius-md, 10px);
            color: var(--text-primary, #fff);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.25s ease;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 36px;
            box-sizing: border-box;
        }

        .dropdown:hover {
            border-color: var(--brand-secondary, #7c3aed);
        }

        .dropdown:focus {
            outline: none;
            border-color: var(--brand-primary, #ff3366);
            box-shadow: 0 0 0 3px rgba(255, 51, 102, 0.15);
        }

        .dropdown:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .dropdown option {
            background: var(--bg-secondary, #16213e);
            color: var(--text-primary, #fff);
            padding: 8px;
        }

        /* Light theme adjustments */
        :host([theme="light"]) .dropdown {
            background-color: var(--bg-primary, #fff);
            color: var(--text-primary, #1a1a2e);
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
        }

        :host([theme="light"]) .dropdown option {
            background: #f5f5f5;
            color: #1a1a2e;
        }

        /* Small size */
        :host([size="small"]) {
            width: auto;
        }

        :host([size="small"]) .dropdown {
            padding: 6px 10px;
            padding-right: 28px;
            font-size: 0.7rem;
            border-radius: 999px;
            background-position: right 8px center;
        }
    `;

    constructor() {
        super();
        this.label = '';
        this.name = '';
        this.value = '';
        this.options = [];
        this.required = false;
        this.disabled = false;
        this.theme = 'dark';
        this.size = 'normal';
    }

    _handleChange(e) {
        this.value = e.target.value;
        this.dispatchEvent(new CustomEvent('change', {
            detail: { value: this.value, name: this.name },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            <div class="dropdown-wrapper">
                ${this.label ? html`<label class="label">${this.label}</label>` : ''}
                <select 
                    class="dropdown"
                    .value=${this.value}
                    ?required=${this.required}
                    ?disabled=${this.disabled}
                    @change=${this._handleChange}
                >
                    ${this.options.map(opt => html`
                        <option value=${opt.value} ?selected=${opt.value === this.value}>
                            ${opt.label}
                        </option>
                    `)}
                </select>
            </div>
        `;
    }
}

customElements.define('form-dropdown', FormDropdown);
