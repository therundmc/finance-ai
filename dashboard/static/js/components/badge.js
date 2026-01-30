/**
 * Badge Component
 * Reusable badge for signals, status, conviction, alerts
 */
import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';

export class AppBadge extends LitElement {
  static properties = {
    variant: { type: String }, // 'signal', 'status', 'conviction', 'alert', 'info'
    type: { type: String },    // For signal: 'acheter'/'vendre'/'conserver', status: 'open'/'closed', etc.
    size: { type: String },    // 'sm', 'md' (default)
    theme: { type: String, reflect: true }
  };

  static styles = css`
    :host {
      display: inline-flex;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 3px 8px;
      border-radius: 999px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      white-space: nowrap;
      transition: all 0.2s ease;
    }

    /* Sizes */
    .badge.sm {
      font-size: 0.55rem;
      padding: 2px 6px;
    }

    .badge.md {
      font-size: 0.65rem;
      padding: 3px 10px;
    }

    /* ===== SIGNAL VARIANTS ===== */
    .badge.signal {
      color: white;
    }

    .badge.signal.acheter,
    .badge.signal.buy {
      background: linear-gradient(135deg, #06d6a0, #00ff88);
    }

    .badge.signal.vendre,
    .badge.signal.sell {
      background: linear-gradient(135deg, #ff3366, #ff6b6b);
    }

    .badge.signal.conserver,
    .badge.signal.hold {
      background: linear-gradient(135deg, #ffb347, #ffc107);
      color: #1a1a1a;
    }

    /* ===== STATUS VARIANTS - same solid gradient style ===== */
    .badge.status.open {
      background: linear-gradient(135deg, #06d6a0, #00ff88);
      color: white;
    }

    .badge.status.closed {
      background: linear-gradient(135deg, #ff3366, #ff6b6b);
      color: white;
    }

    .badge.status.stopped {
      background: linear-gradient(135deg, #ffb347, #ffc107);
      color: #1a1a1a;
    }

    /* ===== CONVICTION VARIANTS ===== */
    .badge.conviction {
      background: var(--bg-tertiary, #2a2520);
      color: var(--text-secondary, #a89f94);
      border: 1px solid var(--border-color, #3a332c);
    }

    .badge.conviction.forte,
    .badge.conviction.high,
    .badge.conviction.strong {
      background: rgba(6, 214, 160, 0.2);
      color: var(--success, #06d6a0);
      border-color: var(--success, #06d6a0);
    }

    .badge.conviction.moyenne,
    .badge.conviction.medium,
    .badge.conviction.moderate {
      background: rgba(255, 179, 71, 0.2);
      color: #ffb347;
      border-color: #ffb347;
    }

    .badge.conviction.faible,
    .badge.conviction.low,
    .badge.conviction.weak {
      background: rgba(255, 51, 102, 0.2);
      color: var(--danger, #ff3366);
      border-color: var(--danger, #ff3366);
    }

    /* ===== ALERT VARIANTS ===== */
    .badge.alert {
      font-weight: 700;
    }

    .badge.alert.sl,
    .badge.alert.stop-loss {
      background: linear-gradient(135deg, rgba(255, 51, 102, 0.3), rgba(255, 107, 107, 0.2));
      color: var(--danger, #ff3366);
    }

    .badge.alert.tp1,
    .badge.alert.tp2,
    .badge.alert.take-profit {
      background: linear-gradient(135deg, rgba(6, 214, 160, 0.3), rgba(0, 255, 136, 0.2));
      color: var(--success, #06d6a0);
    }

    /* ===== INFO VARIANT ===== */
    .badge.info {
      background: var(--bg-tertiary, #2a2520);
      color: var(--text-muted, #666);
    }

    .badge.info.purple {
      background: rgba(124, 58, 237, 0.15);
      color: var(--brand-secondary, #7c3aed);
    }

    .badge.info.pink {
      background: rgba(255, 107, 237, 0.15);
      color: var(--brand-pink, #ff6bed);
    }
  `;

  constructor() {
    super();
    this.variant = 'info';
    this.type = '';
    this.size = 'md';
    this.theme = 'dark';
  }

  render() {
    const classes = [
      'badge',
      this.variant,
      this.type.toLowerCase().replace(/\s+/g, '-'),
      this.size
    ].filter(Boolean).join(' ');

    return html`<span class="${classes}"><slot></slot></span>`;
  }
}

customElements.define('app-badge', AppBadge);
