/**
 * Base Component with Lit
 * Provides shared utilities and styling for all components
 * Includes theme support (light/dark)
 */
import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit@3/+esm';

// Re-export for other components
export { LitElement, html, css };

// Shared CSS variables (matching original app variables.css)
export const sharedStyles = css`
  :host {
    /* Brand Colors */
    --brand-primary: #ff3366;
    --brand-secondary: #8b5cf6;
    --brand-accent: #06d6a0;
    --brand-warm: #ff9f43;
    --brand-blue: #3b82f6;
    --brand-pink: #ec4899;
    
    /* Light Theme (default) */
    --bg-primary: #fef7f3;
    --bg-secondary: #ffffff;
    --bg-tertiary: #fef3ed;
    --bg-card: #ffffff;
    --bg-hover: #fff0e8;
    --bg-gradient: linear-gradient(145deg, #fff5f0 0%, #f0f4ff 40%, #f0fff8 70%, #fff5f5 100%);
    --bg-gradient-card: linear-gradient(135deg, #ffffff 0%, #fff8f5 100%);
    
    /* Borders */
    --border-color: #fde5d9;
    --border-hover: #fbc9b5;
    
    /* Text */
    --text-primary: #1f1a16;
    --text-secondary: #5c5046;
    --text-muted: #9a8c80;
    
    /* Accents */
    --accent: #ff3366;
    --accent-light: rgba(255, 51, 102, 0.1);
    
    /* States */
    --success: #06d6a0;
    --success-light: rgba(6, 214, 160, 0.12);
    --success-border: rgba(6, 214, 160, 0.35);
    --danger: #ff3366;
    --danger-light: rgba(255, 51, 102, 0.1);
    --danger-border: rgba(255, 51, 102, 0.35);
    --warning: #ffb347;
    --warning-light: rgba(255, 179, 71, 0.12);
    --warning-border: rgba(255, 179, 71, 0.35);
    
    /* Shadows */
    --shadow-sm: 0 2px 8px rgba(255, 51, 102, 0.06);
    --shadow-md: 0 8px 30px rgba(255, 51, 102, 0.1);
    --shadow-lg: 0 20px 50px rgba(255, 51, 102, 0.15);
    --shadow-card: 0 4px 24px rgba(255, 100, 130, 0.08);
    
    /* Spacing */
    --spacing-xs: 8px;
    --spacing-sm: 14px;
    --spacing-md: 22px;
    
    /* Radius */
    --radius-sm: 14px;
    --radius-md: 20px;
    --radius-lg: 28px;
    --radius-full: 9999px;
    
    /* Transitions */
    --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    
    /* Fonts */
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    box-sizing: border-box;
  }
  
  /* Dark Theme - matching original app [data-theme="dark"] */
  :host([theme="dark"]) {
    --bg-primary: #161311;
    --bg-secondary: #1f1b18;
    --bg-tertiary: #2a2520;
    --bg-card: #1f1b18;
    --bg-hover: #322b25;
    --bg-gradient: linear-gradient(145deg, #161311 0%, #1a1520 40%, #131a18 70%, #1a1315 100%);
    --bg-gradient-card: linear-gradient(135deg, #1f1b18 0%, #252018 100%);
    
    --border-color: #3a332c;
    --border-hover: #4d4238;
    
    --text-primary: #faf5f0;
    --text-secondary: #c9bfb5;
    --text-muted: #7a6f65;
    
    --accent: #ff4d7a;
    --accent-light: rgba(255, 77, 122, 0.18);
    
    --success-light: rgba(6, 214, 160, 0.18);
    --success-border: rgba(6, 214, 160, 0.4);
    --danger-light: rgba(255, 77, 122, 0.18);
    --danger-border: rgba(255, 77, 122, 0.4);
    --warning-light: rgba(255, 179, 71, 0.18);
    --warning-border: rgba(255, 179, 71, 0.4);
    
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 8px 30px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.5);
    --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.3);
  }
  
  *, *::before, *::after {
    box-sizing: inherit;
  }
`;

// Base class with shared functionality
export class BaseComponent extends LitElement {
  static properties = {
    theme: { type: String, reflect: true }
  };
  
  constructor() {
    super();
    this.theme = 'light';
  }
  
  // Format currency
  formatCurrency(value, currency = 'USD') {
    const symbols = { USD: '$', EUR: '€', CHF: 'CHF ', GBP: '£' };
    const symbol = symbols[currency] || '$';
    return `${symbol}${value.toFixed(2)}`;
  }
  
  // Format percentage
  formatPercent(value) {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  }
  
  // Emit custom event
  emit(eventName, detail = {}) {
    this.dispatchEvent(new CustomEvent(eventName, {
      detail,
      bubbles: true,
      composed: true
    }));
  }
}
