/**
 * SSE Client Helper
 * Simplified EventSource wrapper with auto-reconnect
 */

export class SSEClient {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectDelay = options.reconnectDelay || 5000;
        this.maxRetries = options.maxRetries || Infinity;
        this.retries = 0;
        this.eventSource = null;
        this.reconnectTimer = null;
        this.isManualClose = false;
        
        // Callbacks
        this.onMessage = options.onMessage || (() => {});
        this.onError = options.onError || (() => {});
        this.onOpen = options.onOpen || (() => {});
    }

    connect() {
        this.isManualClose = false;
        this._createEventSource();
    }

    _createEventSource() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource(this.url);

        this.eventSource.onmessage = (event) => {
            this.retries = 0; // Reset retry counter on successful message
            try {
                const data = JSON.parse(event.data);
                this.onMessage(data, event);
            } catch (error) {
                console.error('❌ SSE message parse error:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error(`❌ SSE connection error for ${this.url}:`, error);
            this.onError(error);
            
            // Don't reconnect if manually closed
            if (this.isManualClose) {
                return;
            }

            // Auto-reconnect with exponential backoff
            if (this.retries < this.maxRetries) {
                this.retries++;
                const delay = Math.min(this.reconnectDelay * this.retries, 30000);
                console.log(`🔄 Reconnecting to SSE in ${delay/1000}s (attempt ${this.retries})...`);
                
                this.reconnectTimer = setTimeout(() => {
                    this._createEventSource();
                }, delay);
            } else {
                console.error(`❌ Max retries (${this.maxRetries}) reached for ${this.url}`);
            }
        };

        this.eventSource.onopen = () => {
            console.log(`✅ SSE connected: ${this.url}`);
            this.retries = 0;
            this.onOpen();
        };
    }

    close() {
        this.isManualClose = true;
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            console.log(`⏹️ SSE disconnected: ${this.url}`);
        }
    }

    get readyState() {
        return this.eventSource ? this.eventSource.readyState : EventSource.CLOSED;
    }

    get isConnected() {
        return this.readyState === EventSource.OPEN;
    }
}

/**
 * SSE Manager - Manages multiple SSE connections
 */
export class SSEManager {
    constructor() {
        this.connections = new Map();
    }

    /**
     * Create and start a new SSE connection
     * @param {string} name - Unique identifier for this connection
     * @param {string} url - SSE endpoint URL
     * @param {Object} options - Connection options
     */
    connect(name, url, options = {}) {
        // Close existing connection if any
        this.disconnect(name);

        const client = new SSEClient(url, options);
        client.connect();
        this.connections.set(name, client);

        return client;
    }

    /**
     * Disconnect a specific SSE connection
     */
    disconnect(name) {
        const client = this.connections.get(name);
        if (client) {
            client.close();
            this.connections.delete(name);
        }
    }

    /**
     * Disconnect all SSE connections
     */
    disconnectAll() {
        for (const [name, client] of this.connections) {
            client.close();
        }
        this.connections.clear();
    }

    /**
     * Get a specific connection
     */
    get(name) {
        return this.connections.get(name);
    }

    /**
     * Check if connection exists and is active
     */
    isConnected(name) {
        const client = this.connections.get(name);
        return client && client.isConnected;
    }
}

// Global SSE manager instance
export const sseManager = new SSEManager();

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    sseManager.disconnectAll();
});
