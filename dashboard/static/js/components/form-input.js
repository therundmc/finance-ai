import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export class FormInput extends LitElement {
    static properties = {
        label: { type: String },
        name: { type: String },
        type: { type: String },
        value: { type: String },
        placeholder: { type: String },
        required: { type: Boolean },
        disabled: { type: Boolean },
        min: { type: String },
        max: { type: String },
        step: { type: String },
        size: { type: String, reflect: true },
        theme: { type: String, reflect: true }
    };

    static styles = css`
        :host {
            display: block;
            width: 100%;
        }

        .input-wrapper {
            display: flex;
            flex-direction: column;
            gap: 4px;
            width: 100%;
            min-width: 0;
        }

        .label {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted, #888);
        }

        .input {
            width: 100%;
            padding: 8px 10px;
            background: var(--bg-tertiary, #1a1a2e);
            border: 2px solid var(--border-color, #333);
            border-radius: var(--radius-md, 8px);
            color: var(--text-primary, #fff);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.25s ease;
            box-sizing: border-box;
            min-width: 0;
            max-width: 100%;
        }

        /* Date input fix for mobile */
        input[type="date"].input {
            -webkit-appearance: none;
            appearance: none;
        }

        input[type="date"].input::-webkit-calendar-picker-indicator {
            filter: invert(0.7);
            cursor: pointer;
        }

        input[type="number"].input {
            -moz-appearance: textfield;
        }

        input[type="number"].input::-webkit-outer-spin-button,
        input[type="number"].input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }

        .input::placeholder {
            color: var(--text-muted, #666);
        }

        .input:hover {
            border-color: var(--brand-secondary, #7c3aed);
        }

        .input:focus {
            outline: none;
            border-color: var(--brand-primary, #ff3366);
            box-shadow: 0 0 0 3px rgba(255, 51, 102, 0.15);
        }

        .input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Textarea variant */
        textarea.input {
            min-height: 80px;
            resize: vertical;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Light theme adjustments */
        :host([theme="light"]) .input {
            background: var(--bg-primary, #fff);
            color: var(--text-primary, #1a1a2e);
        }

        /* Small size variant */
        :host([size="sm"]) .input {
            padding: 4px 10px;
            font-size: 0.65rem;
            height: 26px;
            border-radius: var(--radius-full, 9999px);
        }
    `;

    constructor() {
        super();
        this.label = '';
        this.name = '';
        this.type = 'text';
        this.value = '';
        this.placeholder = '';
        this.required = false;
        this.disabled = false;
        this.min = '';
        this.max = '';
        this.step = '';
        this.size = '';
        this.theme = 'dark';
    }

    _handleInput(e) {
        const newValue = e.target.value;
        this.dispatchEvent(new CustomEvent('input', {
            detail: { value: newValue, name: this.name },
            bubbles: true,
            composed: true
        }));
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
        const isTextarea = this.type === 'textarea';
        
        return html`
            <div class="input-wrapper">
                ${this.label ? html`<label class="label">${this.label}</label>` : ''}
                ${isTextarea ? html`
                    <textarea
                        class="input"
                        .value=${this.value}
                        placeholder=${this.placeholder}
                        ?required=${this.required}
                        ?disabled=${this.disabled}
                        @input=${this._handleInput}
                        @change=${this._handleChange}
                    ></textarea>
                ` : html`
                    <input
                        class="input"
                        type=${this.type}
                        .value=${this.value}
                        placeholder=${this.placeholder}
                        ?required=${this.required}
                        ?disabled=${this.disabled}
                        min=${this.min || ''}
                        max=${this.max || ''}
                        step=${this.step || ''}
                        @input=${this._handleInput}
                        @change=${this._handleChange}
                    />
                `}
            </div>
        `;
    }
}

customElements.define('form-input', FormInput);
