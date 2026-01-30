/**
 * SSE Status Monitor Component
 * Shows real-time connection status for all SSE streams
 * Optional: Add to dashboard for debugging
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';

export class SSEStatusMonitor extends LitElement {
    static properties = {
        connections: { type: Object },
        expanded: { type: Boolean }
    };

    static styles = css`
        :host {
            display: block;
            position: fixed;
            bottom: 16px;
            right: 16px;
            z-index: 10000;
        }

        .monitor {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            min-width: 200px;
        }

        .monitor-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            padding: 4px 8px;
            user-select: none;
        }

        .monitor-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .toggle-icon {
            font-size: 0.75rem;
            color: var(--text-secondary);
            transition: transform 0.2s;
        }

        .expanded .toggle-icon {
            transform: rotate(90deg);
        }

        .monitor-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .expanded .monitor-content {
            max-height: 300px;
            padding-top: 8px;
        }

        .connection-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 8px;
            margin-bottom: 4px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            font-size: 0.7rem;
        }

        .connection-name {
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-dot.connected {
            background: var(--success-color);
        }

        .status-dot.connecting {
            background: #f59e0b;
        }

        .status-dot.disconnected {
            background: var(--danger-color);
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-text {
            color: var(--text-primary);
            font-size: 0.65rem;
        }

        .stats {
            display: flex;
            gap: 8px;
            padding: 8px;
            margin-top: 8px;
            border-top: 1px solid var(--border-color);
        }

        .stat {
            flex: 1;
            text-align: center;
        }

        .stat-value {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-color);
        }

        .stat-label {
            font-size: 0.6rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }
    `;

    constructor() {
        super();
        this.connections = {
            prices: { state: 0, lastUpdate: null, messageCount: 0 },
            news: { state: 0, lastUpdate: null, messageCount: 0 },
            analyses: { state: 0, lastUpdate: null, messageCount: 0 }
        };
        this.expanded = false;
        this._startMonitoring();
    }

    _startMonitoring() {
        // Monitor EventSource connections
        setInterval(() => {
            this.requestUpdate();
        }, 1000);
    }

    _getStateText(state) {
        switch(state) {
            case 0: return 'Connecting';
            case 1: return 'Connected';
            case 2: return 'Disconnected';
            default: return 'Unknown';
        }
    }

    _getStateClass(state) {
        switch(state) {
            case 0: return 'connecting';
            case 1: return 'connected';
            case 2: return 'disconnected';
            default: return 'disconnected';
        }
    }

    _toggle() {
        this.expanded = !this.expanded;
    }

    _getTotalMessages() {
        return Object.values(this.connections).reduce((sum, conn) => sum + conn.messageCount, 0);
    }

    _getConnectedCount() {
        return Object.values(this.connections).filter(conn => conn.state === 1).length;
    }

    render() {
        const totalMessages = this._getTotalMessages();
        const connectedCount = this._getConnectedCount();

        return html`
            <div class="monitor ${this.expanded ? 'expanded' : ''}">
                <div class="monitor-header" @click="${this._toggle}">
                    <div class="monitor-title">
                        📡 SSE Status
                        ${connectedCount > 0 ? html`<span style="color: var(--success-color)">(${connectedCount}/3)</span>` : ''}
                    </div>
                    <span class="toggle-icon">▶</span>
                </div>

                <div class="monitor-content">
                    ${Object.entries(this.connections).map(([name, conn]) => html`
                        <div class="connection-item">
                            <span class="connection-name">${name}</span>
                            <div class="connection-status">
                                <span class="status-dot ${this._getStateClass(conn.state)}"></span>
                                <span class="status-text">${this._getStateText(conn.state)}</span>
                            </div>
                        </div>
                    `)}

                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">${totalMessages}</div>
                            <div class="stat-label">Messages</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">${connectedCount}/3</div>
                            <div class="stat-label">Active</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Public method to update connection state
    updateConnection(name, state, messageCount = null) {
        if (this.connections[name]) {
            this.connections[name].state = state;
            this.connections[name].lastUpdate = new Date();
            if (messageCount !== null) {
                this.connections[name].messageCount = messageCount;
            } else if (state === 1) {
                this.connections[name].messageCount++;
            }
            this.requestUpdate();
        }
    }
}

customElements.define('sse-status-monitor', SSEStatusMonitor);

// Create global instance for easy access
export function createSSEMonitor() {
    const monitor = document.createElement('sse-status-monitor');
    document.body.appendChild(monitor);
    return monitor;
}

// Auto-create in development mode
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        window.sseMonitor = createSSEMonitor();
    });
}
