// ============================================
// FINANCE AI DASHBOARD - APP NEW v4.0
// Lit Components Architecture with Currency Support
// ============================================

// ============================================
// STATE MANAGEMENT
// ============================================
export const AppState = {
    theme: localStorage.getItem('theme') || 'dark',
    currency: localStorage.getItem('displayCurrency') || 'USD',
    section: localStorage.getItem('activeSection') || 'portfolio',
    exchangeRates: { USD: 1, CHF: 0.88, EUR: 0.92, GBP: 0.79 },
    analysesCache: {},
    lastScrollY: 0,
    headerCollapsed: false,
    hideValues: localStorage.getItem('hideValues') === 'true'
};

// Currency symbols
export const CURRENCY_SYMBOLS = {
    USD: '$',
    EUR: '€',
    CHF: 'CHF ',
    GBP: '£'
};

// ============================================
// API HELPERS (with logging)
// ============================================
export const API = {
    async get(endpoint) {
        console.log(`📡 GET ${endpoint}`);
        try {
            const response = await fetch(endpoint);
            const data = await response.json();
            console.log(`✅ GET ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`❌ GET ${endpoint} failed:`, error);
            throw error;
        }
    },

    async post(endpoint, body) {
        console.log(`📡 POST ${endpoint}`, body);
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            console.log(`✅ POST ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`❌ POST ${endpoint} failed:`, error);
            throw error;
        }
    },

    async put(endpoint, body) {
        console.log(`📡 PUT ${endpoint}`, body);
        try {
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            console.log(`✅ PUT ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`❌ PUT ${endpoint} failed:`, error);
            throw error;
        }
    },

    async delete(endpoint) {
        console.log(`📡 DELETE ${endpoint}`);
        try {
            const response = await fetch(endpoint, { method: 'DELETE' });
            const data = await response.json();
            console.log(`✅ DELETE ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`❌ DELETE ${endpoint} failed:`, error);
            throw error;
        }
    }
};

// ============================================
// EXCHANGE RATES
// ============================================
export async function fetchExchangeRates() {
    console.log('💱 Fetching exchange rates...');
    try {
        const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
        if (!response.ok) throw new Error('Failed to fetch rates');
        
        const data = await response.json();
        AppState.exchangeRates = {
            USD: 1,
            CHF: data.rates.CHF || 0.88,
            EUR: data.rates.EUR || 0.92,
            GBP: data.rates.GBP || 0.79
        };
        localStorage.setItem('exchangeRates', JSON.stringify(AppState.exchangeRates));
        console.log('✅ Exchange rates updated:', AppState.exchangeRates);
        return AppState.exchangeRates;
    } catch (error) {
        console.error('❌ Failed to fetch exchange rates:', error);
        // Try to load from localStorage
        const saved = localStorage.getItem('exchangeRates');
        if (saved) {
            AppState.exchangeRates = JSON.parse(saved);
            console.log('📦 Using cached exchange rates:', AppState.exchangeRates);
        }
        return AppState.exchangeRates;
    }
}

// ============================================
// AI ANALYSES
// ============================================
export async function fetchAnalyses() {
    console.log('🤖 Fetching AI analyses...');
    try {
        const data = await API.get('/api/latest');
        if (data.latest) {
            AppState.analysesCache = data.latest;
            console.log('✅ Analyses loaded:', Object.keys(AppState.analysesCache).length, 'tickers');
        }
        return AppState.analysesCache;
    } catch (error) {
        console.error('❌ Error fetching analyses:', error);
        return {};
    }
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================
import { showToast as showToastComponent, getToastInstance } from './components/toast-notification.js';

export function showToast(message, type = 'success') {
    return showToastComponent(message, type, 3000);
}

// Make globally available
window.showToast = showToast;

// ============================================
// DOM ELEMENTS
// ============================================
let elements = {};

function cacheElements() {
    elements = {
        themeToggle: document.getElementById('theme-toggle'),
        hideValuesToggle: document.getElementById('hide-values-toggle'),
        currencySelector: document.getElementById('currency-selector'),
        portfolioPage: document.getElementById('portfolio-page'),
        analysisPage: document.getElementById('analysis-page'),
        togglePortfolio: document.getElementById('toggle-portfolio'),
        toggleAnalysis: document.getElementById('toggle-analysis'),
        sectionPortfolio: document.getElementById('section-portfolio'),
        sectionAnalysis: document.getElementById('section-analysis'),
        // Modals
        newPositionModal: document.getElementById('new-position-modal'),
        closePositionModal: document.getElementById('close-position-modal'),
        deletePositionModal: document.getElementById('delete-position-modal'),
        editTargetsModal: document.getElementById('edit-targets-modal')
    };
}

// Current modal state
let currentPositionToDelete = null;
let currentPositionToClose = null;
let currentPositionToEdit = null;
let isSubmitting = false; // Prevent double submit

// ============================================
// THEME MANAGEMENT
// ============================================
function initializeTheme() {
    document.body.classList.toggle('dark', AppState.theme === 'dark');
    updateThemeButton();
    updateComponentThemes();
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', AppState.theme);
    document.body.classList.toggle('dark', AppState.theme === 'dark');
    updateThemeButton();
    updateComponentThemes();
}

function updateThemeButton() {
    if (!elements.themeToggle) return;
    const icon = elements.themeToggle.querySelector('.theme-icon');
    const label = elements.themeToggle.querySelector('.theme-label');
    if (icon) icon.textContent = AppState.theme === 'dark' ? '☀️' : '🌙';
    if (label) label.textContent = AppState.theme === 'dark' ? 'Clair' : 'Sombre';
}

function updateComponentThemes() {
    if (elements.portfolioPage) elements.portfolioPage.theme = AppState.theme;
    if (elements.analysisPage) elements.analysisPage.theme = AppState.theme;
    if (elements.currencySelector) elements.currencySelector.theme = AppState.theme;
    document.querySelectorAll('section-toggle-btn').forEach(btn => {
        btn.theme = AppState.theme;
    });
}

// ============================================
// HIDE VALUES TOGGLE
// ============================================
function initializeHideValues() {
    updateHideValuesButton();
    updateHideValuesState();
}

function toggleHideValues() {
    AppState.hideValues = !AppState.hideValues;
    localStorage.setItem('hideValues', AppState.hideValues);
    updateHideValuesButton();
    updateHideValuesState();
}

function updateHideValuesButton() {
    if (!elements.hideValuesToggle) return;
    const icon = elements.hideValuesToggle.querySelector('.hide-icon');
    if (icon) {
        icon.textContent = AppState.hideValues ? '🙈' : '👁️';
    }
    elements.hideValuesToggle.title = AppState.hideValues ? 'Afficher les valeurs' : 'Masquer les valeurs';
}

function updateHideValuesState() {
    if (elements.portfolioPage) {
        elements.portfolioPage.hideValues = AppState.hideValues;
    }
}

// ============================================
// CURRENCY MANAGEMENT
// ============================================
function initializeCurrency() {
    if (!elements.currencySelector) return;
    
    elements.currencySelector.options = [
        { value: 'USD', label: '$ USD' },
        { value: 'CHF', label: 'CHF' },
        { value: 'EUR', label: '€ EUR' },
        { value: 'GBP', label: '£ GBP' }
    ];
    elements.currencySelector.value = AppState.currency;
    elements.currencySelector.theme = AppState.theme;
}

function setCurrency(currency) {
    console.log('💱 Currency changed to:', currency);
    AppState.currency = currency;
    localStorage.setItem('displayCurrency', currency);
    
    // Update portfolio page - currency only for STATS conversion
    if (elements.portfolioPage) {
        elements.portfolioPage.currency = currency;
        elements.portfolioPage.exchangeRates = AppState.exchangeRates;
    }
    
    showToast(`Devise changée: ${currency}`, 'success');
}

// ============================================
// SECTION TOGGLE
// ============================================
function switchSection(section) {
    AppState.section = section;
    localStorage.setItem('activeSection', section);
    
    // Update toggle buttons
    if (elements.togglePortfolio) elements.togglePortfolio.active = section === 'portfolio';
    if (elements.toggleAnalysis) elements.toggleAnalysis.active = section === 'analysis';
    
    // Update sections visibility
    if (elements.sectionPortfolio) elements.sectionPortfolio.classList.toggle('active', section === 'portfolio');
    if (elements.sectionAnalysis) elements.sectionAnalysis.classList.toggle('active', section === 'analysis');
}

// ============================================
// TICKER DROPDOWN
// ============================================
function populateTickerDropdown() {
    const tickerDropdown = document.getElementById('pos-ticker');
    if (!tickerDropdown) return;
    
    const tickers = Object.keys(AppState.analysesCache).sort();
    
    const options = [{ value: '', label: '-- Sélectionner un ticker --' }];
    tickers.forEach(ticker => {
        const analysis = AppState.analysesCache[ticker];
        const signal = analysis?.structured_data?.signal || '';
        const emoji = signal.includes('ACHAT') ? '🟢' : signal.includes('VENTE') ? '🔴' : '⚪';
        options.push({ value: ticker, label: `${emoji} ${ticker}` });
    });
    
    tickerDropdown.options = options;
    tickerDropdown.value = '';
}

function handleTickerChange(ticker) {
    if (!ticker) {
        // Clear form
        document.getElementById('pos-analysis-id').value = '';
        document.getElementById('pos-entry-price').value = '';
        document.getElementById('pos-stop-loss').value = '';
        document.getElementById('pos-tp1').value = '';
        document.getElementById('pos-tp2').value = '';
        document.getElementById('pos-notes').value = '';
        return;
    }
    
    const analysis = AppState.analysesCache[ticker];
    if (analysis) {
        const structured = analysis.structured_data || {};
        const niveaux = structured.niveaux || {};
        const ind = analysis.indicators || {};
        
        document.getElementById('pos-analysis-id').value = analysis.id || '';
        document.getElementById('pos-entry-price').value = analysis.price?.toFixed(2) || '';
        document.getElementById('pos-stop-loss').value = (niveaux.stop_loss || ind.support)?.toFixed(2) || '';
        document.getElementById('pos-tp1').value = (niveaux.objectif_1 || ind.resistance)?.toFixed(2) || '';
        document.getElementById('pos-tp2').value = niveaux.objectif_2?.toFixed(2) || '';
        document.getElementById('pos-notes').value = analysis.summary || '';
        
        showToast(`Données ${ticker} chargées depuis l'analyse AI`, 'success');
    }
}

// ============================================
// NEW POSITION MODAL
// ============================================
function openNewPositionModal() {
    console.log('📝 Opening new position modal');
    
    if (!elements.newPositionModal) return;
    
    elements.newPositionModal.open = true;
    elements.newPositionModal.theme = AppState.theme;
    
    // Set theme on all form inputs and dropdowns
    const formInputs = elements.newPositionModal.querySelectorAll('form-input, form-dropdown');
    formInputs.forEach(input => input.theme = AppState.theme);
    
    // Populate ticker dropdown from analyses
    populateTickerDropdown();
    
    // Set today's date
    document.getElementById('pos-entry-date').value = new Date().toISOString().split('T')[0];
    
    // Reset form
    document.getElementById('pos-analysis-id').value = '';
    document.getElementById('pos-entry-price').value = '';
    document.getElementById('pos-quantity').value = '1';
    document.getElementById('pos-stop-loss').value = '';
    document.getElementById('pos-tp1').value = '';
    document.getElementById('pos-tp2').value = '';
    document.getElementById('pos-notes').value = '';
}

async function submitNewPosition() {
    // Prevent double submission
    if (isSubmitting) {
        console.log('⚠️ Already submitting, ignoring...');
        return;
    }
    
    const tickerValue = document.getElementById('pos-ticker').value;
    if (!tickerValue) {
        showToast('Veuillez sélectionner un ticker', 'error');
        return;
    }
    
    isSubmitting = true;
    console.log('📤 Submitting new position...');
    
    const data = {
        ticker: tickerValue.toUpperCase(),
        entry_price: parseFloat(document.getElementById('pos-entry-price').value),
        quantity: parseFloat(document.getElementById('pos-quantity').value) || 1,
        entry_date: document.getElementById('pos-entry-date').value,
        stop_loss: parseFloat(document.getElementById('pos-stop-loss').value) || null,
        take_profit_1: parseFloat(document.getElementById('pos-tp1').value) || null,
        take_profit_2: parseFloat(document.getElementById('pos-tp2').value) || null,
        notes: document.getElementById('pos-notes').value || null,
        analysis_id: document.getElementById('pos-analysis-id').value || null
    };

    try {
        const result = await API.post('/api/positions', data);
        
        if (result.success) {
            showToast(`Position ${data.ticker} ouverte!`, 'success');
            elements.newPositionModal.open = false;
            document.getElementById('new-position-form').reset();
            elements.portfolioPage._loadData();
        } else {
            showToast(result.error || 'Erreur lors de la création', 'error');
        }
    } catch (error) {
        showToast('Erreur lors de la création', 'error');
    } finally {
        isSubmitting = false;
    }
}

// ============================================
// CLOSE POSITION MODAL
// ============================================
function openClosePositionModal(position) {
    console.log('🔒 Opening close position modal for:', position.ticker);
    
    currentPositionToClose = position;
    elements.closePositionModal.open = true;
    elements.closePositionModal.theme = AppState.theme;
    
    // Set theme on all form inputs and dropdowns
    const formInputs = elements.closePositionModal.querySelectorAll('form-input, form-dropdown');
    formInputs.forEach(input => input.theme = AppState.theme);
    
    // Populate position info
    document.getElementById('close-ticker').textContent = position.ticker;
    document.getElementById('close-qty-info').textContent = `Qté: ${position.quantity}`;
    
    // Set current price and today's date
    const currentPrice = position.live_data?.price || position.current_price || position.entry_price;
    document.getElementById('close-price').value = currentPrice.toFixed(2);
    document.getElementById('close-date').value = new Date().toISOString().split('T')[0];
    
    // Setup close reason dropdown
    const closeReasonDropdown = document.getElementById('close-reason');
    closeReasonDropdown.options = [
        { value: '', label: 'Sélectionner...' },
        { value: 'take_profit', label: '🎯 Take Profit atteint' },
        { value: 'stop_loss', label: '🛑 Stop Loss atteint' },
        { value: 'manual', label: '✋ Clôture manuelle' },
        { value: 'rebalance', label: '⚖️ Rééquilibrage' },
        { value: 'other', label: '📝 Autre' }
    ];
    closeReasonDropdown.value = '';
    
    // Initialize quantity selector
    initCloseQuantitySelector(position.quantity);
}

function initCloseQuantitySelector(totalQty) {
    const buttons = document.querySelectorAll('.qty-btn');
    const sellQtyDisplay = document.getElementById('sell-qty-display');
    const sellType = document.getElementById('sell-type');
    const sellPercentInput = document.getElementById('close-sell-percent');
    
    // Reset to 100%
    buttons.forEach(btn => {
        const percent = parseInt(btn.dataset.percent);
        btn.style.background = percent === 100 ? 'var(--brand-primary)' : 'var(--bg-tertiary)';
        btn.style.borderColor = percent === 100 ? 'var(--brand-primary)' : 'var(--border-color)';
        btn.style.color = percent === 100 ? 'white' : 'var(--text-primary)';
    });
    
    sellQtyDisplay.textContent = totalQty;
    sellType.textContent = '(vente totale)';
    sellPercentInput.value = '100';
    
    // Setup click handlers
    buttons.forEach(btn => {
        btn.onclick = () => {
            const percent = parseInt(btn.dataset.percent);
            const sellQty = (totalQty * percent / 100).toFixed(2);
            
            // Update active state
            buttons.forEach(b => {
                const p = parseInt(b.dataset.percent);
                b.style.background = p === percent ? 'var(--brand-primary)' : 'var(--bg-tertiary)';
                b.style.borderColor = p === percent ? 'var(--brand-primary)' : 'var(--border-color)';
                b.style.color = p === percent ? 'white' : 'var(--text-primary)';
            });
            
            sellQtyDisplay.textContent = sellQty;
            sellType.textContent = percent === 100 ? '(vente totale)' : '(vente partielle)';
            sellPercentInput.value = percent.toString();
        };
    });
}

async function submitClosePosition() {
    if (!currentPositionToClose || isSubmitting) {
        console.log('⚠️ No position to close or already submitting');
        return;
    }
    
    isSubmitting = true;
    console.log('📤 Submitting close position...');

    const sellPercent = parseInt(document.getElementById('close-sell-percent').value);
    const exitPrice = parseFloat(document.getElementById('close-price').value);
    const exitDate = document.getElementById('close-date').value;
    const closeReason = document.getElementById('close-reason').value;
    const closeNotes = document.getElementById('close-notes').value;
    
    // Determine which API endpoint to use
    const isPartialClose = sellPercent < 100;
    const endpoint = isPartialClose 
        ? `/api/positions/${currentPositionToClose.id}/partial-close`
        : `/api/positions/${currentPositionToClose.id}/close`;
    
    const data = {
        exit_price: exitPrice,
        exit_date: exitDate,
        status: closeReason === 'stop_loss' ? 'stopped' : 'closed',
        close_reason: closeReason,
        close_notes: closeNotes
    };
    
    if (isPartialClose) {
        data.sell_percent = sellPercent;
    }

    try {
        const result = await API.post(endpoint, data);
        
        if (result.success) {
            const action = isPartialClose ? `${sellPercent}% vendu` : 'clôturée';
            showToast(`Position ${currentPositionToClose.ticker} ${action}!`, 'success');
            elements.closePositionModal.open = false;
            document.getElementById('close-position-form').reset();
            currentPositionToClose = null;
            elements.portfolioPage._loadData();
        } else {
            showToast(result.error || 'Erreur lors de la clôture', 'error');
        }
    } catch (error) {
        showToast('Erreur lors de la clôture', 'error');
    } finally {
        isSubmitting = false;
    }
}

// ============================================
// EDIT TARGETS MODAL
// ============================================
function openEditTargetsModal(position) {
    console.log('✏️ Opening edit targets modal for:', position.ticker);
    
    currentPositionToEdit = position;
    elements.editTargetsModal.open = true;
    elements.editTargetsModal.theme = AppState.theme;
    
    // Set theme on all form inputs
    const formInputs = elements.editTargetsModal.querySelectorAll('form-input');
    formInputs.forEach(input => input.theme = AppState.theme);
    
    // Populate current values
    document.getElementById('edit-targets-ticker').textContent = position.ticker;
    document.getElementById('edit-stop-loss').value = position.stop_loss?.toFixed(2) || '';
    document.getElementById('edit-tp1').value = position.take_profit_1?.toFixed(2) || '';
    document.getElementById('edit-tp2').value = position.take_profit_2?.toFixed(2) || '';
}

async function submitEditTargets() {
    if (!currentPositionToEdit || isSubmitting) {
        console.log('⚠️ No position to edit or already submitting');
        return;
    }
    
    isSubmitting = true;
    console.log('📤 Submitting edit targets...');

    const data = {
        stop_loss: parseFloat(document.getElementById('edit-stop-loss').value) || null,
        take_profit_1: parseFloat(document.getElementById('edit-tp1').value) || null,
        take_profit_2: parseFloat(document.getElementById('edit-tp2').value) || null
    };

    try {
        const result = await API.put(`/api/positions/${currentPositionToEdit.id}`, data);
        
        if (result.success) {
            showToast(`Objectifs de ${currentPositionToEdit.ticker} mis à jour!`, 'success');
            elements.editTargetsModal.open = false;
            document.getElementById('edit-targets-form').reset();
            currentPositionToEdit = null;
            elements.portfolioPage._loadData();
        } else {
            showToast(result.error || 'Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        showToast('Erreur lors de la mise à jour', 'error');
    } finally {
        isSubmitting = false;
    }
}

// ============================================
// DELETE POSITION MODAL
// ============================================
function openDeletePositionModal(position) {
    console.log('🗑️ Opening delete position modal for:', position.ticker);
    
    currentPositionToDelete = position;
    elements.deletePositionModal.open = true;
    elements.deletePositionModal.theme = AppState.theme;
    document.getElementById('delete-position-ticker').textContent = 
        `Position: ${position.ticker} (${position.quantity} × $${position.entry_price.toFixed(2)})`;
}

async function submitDeletePosition() {
    if (!currentPositionToDelete || isSubmitting) {
        console.log('⚠️ No position to delete or already submitting');
        return;
    }
    
    isSubmitting = true;
    console.log('📤 Submitting delete position...');

    try {
        const result = await API.delete(`/api/positions/${currentPositionToDelete.id}`);
        
        if (result.success) {
            showToast(`Position ${currentPositionToDelete.ticker} supprimée`, 'success');
            elements.deletePositionModal.open = false;
            currentPositionToDelete = null;
            elements.portfolioPage._loadData();
        } else {
            showToast('Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        showToast('Erreur lors de la suppression', 'error');
    } finally {
        isSubmitting = false;
    }
}

// ============================================
// INLINE EDIT HANDLER
// ============================================
async function handleInlineEdit(position, field, value) {
    console.log('✏️ Inline edit:', position.ticker, field, value);
    
    const data = {};
    data[field] = value ? parseFloat(value) : null;
    
    try {
        const result = await API.put(`/api/positions/${position.id}`, data);
        
        if (result.success) {
            showToast(`${field.toUpperCase()} mis à jour`, 'success');
            elements.portfolioPage._loadData();
        } else {
            showToast(result.error || 'Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        showToast('Erreur lors de la mise à jour', 'error');
    }
}

// ============================================
// SCROLL COLLAPSE HEADER
// ============================================
function setupScrollCollapse() {
    const header = document.getElementById('main-header');
    if (!header) return;
    
    let ticking = false;
    
    // Hysteresis thresholds to prevent glitching
    const COLLAPSE_THRESHOLD = 80;  // Collapse when scrolling down past this
    const EXPAND_THRESHOLD = 30;    // Expand when scrolling up past this
    
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrollY = window.scrollY;
                let shouldCollapse = AppState.headerCollapsed;
                
                // Apply hysteresis: different thresholds for collapse vs expand
                if (!AppState.headerCollapsed && scrollY > COLLAPSE_THRESHOLD) {
                    shouldCollapse = true;
                } else if (AppState.headerCollapsed && scrollY < EXPAND_THRESHOLD) {
                    shouldCollapse = false;
                }
                
                if (shouldCollapse !== AppState.headerCollapsed) {
                    AppState.headerCollapsed = shouldCollapse;
                    header.classList.toggle('collapsed', shouldCollapse);
                }
                
                AppState.lastScrollY = scrollY;
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
}

// ============================================
// EVENT LISTENERS SETUP
// ============================================
function setupEventListeners() {
    // Scroll collapse
    setupScrollCollapse();
    
    // Theme toggle
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Hide values toggle
    if (elements.hideValuesToggle) {
        elements.hideValuesToggle.addEventListener('click', toggleHideValues);
    }
    
    // Currency selector
    if (elements.currencySelector) {
        elements.currencySelector.addEventListener('change', (e) => {
            setCurrency(e.detail.value);
        });
    }
    
    // Section toggles
    if (elements.togglePortfolio) {
        elements.togglePortfolio.addEventListener('toggle', () => switchSection('portfolio'));
    }
    if (elements.toggleAnalysis) {
        elements.toggleAnalysis.addEventListener('toggle', () => switchSection('analysis'));
    }
    
    // Portfolio page events
    if (elements.portfolioPage) {
        elements.portfolioPage.addEventListener('new-position', openNewPositionModal);
        
        elements.portfolioPage.addEventListener('position-edit', (e) => {
            openEditTargetsModal(e.detail.position);
        });
        
        elements.portfolioPage.addEventListener('position-close', (e) => {
            openClosePositionModal(e.detail.position);
        });
        
        elements.portfolioPage.addEventListener('position-delete', (e) => {
            openDeletePositionModal(e.detail.position);
        });
    }
    
    // Ticker dropdown change
    const tickerDropdown = document.getElementById('pos-ticker');
    if (tickerDropdown) {
        tickerDropdown.addEventListener('change', (e) => {
            handleTickerChange(e.detail.value);
        });
    }
    
    // New position modal
    if (elements.newPositionModal) {
        elements.newPositionModal.addEventListener('close', () => {
            elements.newPositionModal.open = false;
            document.getElementById('new-position-form')?.reset();
        });
        
        elements.newPositionModal.addEventListener('submit', submitNewPosition);
    }
    
    // Close position modal
    if (elements.closePositionModal) {
        elements.closePositionModal.addEventListener('close', () => {
            elements.closePositionModal.open = false;
            document.getElementById('close-position-form')?.reset();
            currentPositionToClose = null;
        });
        
        elements.closePositionModal.addEventListener('submit', submitClosePosition);
    }
    
    // Delete position modal
    if (elements.deletePositionModal) {
        elements.deletePositionModal.addEventListener('close', () => {
            elements.deletePositionModal.open = false;
            currentPositionToDelete = null;
        });
        
        elements.deletePositionModal.addEventListener('confirm', submitDeletePosition);
    }
    
    // Edit targets modal
    if (elements.editTargetsModal) {
        elements.editTargetsModal.addEventListener('close', () => {
            elements.editTargetsModal.open = false;
            document.getElementById('edit-targets-form')?.reset();
            currentPositionToEdit = null;
        });
        
        elements.editTargetsModal.addEventListener('submit', submitEditTargets);
    }
}

// ============================================
// INITIALIZATION
// ============================================
// SSE CONNECTIONS
// ============================================
import { SSEClient } from './sse-client.js';

let analysesSSE = null;

function startAnalysesStream() {
    if (analysesSSE) return;
    
    analysesSSE = new SSEClient('/api/stream/analyses', {
        onMessage: (data) => {
            if (data.success && data.latest) {
                console.log('📡 Received new analyses via SSE');
                AppState.analysesCache = data.latest;
                // Update analysis page with new data - properly update latestAnalyses property
                const analysisPage = document.getElementById('analysis-page');
                if (analysisPage) {
                    // Convert latest object to array and set the property
                    analysisPage.latestAnalyses = Object.values(data.latest);
                    // Also update favorites if present
                    if (data.favorites) {
                        analysisPage.favorites = data.favorites;
                    }
                    // Update tickers list
                    const tickerSet = new Set();
                    analysisPage.latestAnalyses.forEach(a => tickerSet.add(a.ticker));
                    analysisPage.analyses.forEach(a => tickerSet.add(a.ticker));
                    analysisPage.tickers = Array.from(tickerSet).sort();
                    console.log('✅ Analysis page updated with', analysisPage.latestAnalyses.length, 'analyses');
                }
            }
        },
        onError: (error) => {
            console.log('SSE analyses stream error (will auto-reconnect)');
        },
        onOpen: () => {
            console.log('✅ Analyses stream connected');
        }
    });
    
    analysesSSE.connect();
}

function stopAnalysesStream() {
    if (analysesSSE) {
        analysesSSE.close();
        analysesSSE = null;
    }
}

// ============================================
export async function initApp() {
    console.log('🚀 Finance AI Dashboard v4.0 (SSE Real-time)');
    
    // Cache DOM elements
    cacheElements();
    
    // Initialize theme
    initializeTheme();
    
    // Initialize hide values
    initializeHideValues();
    
    // Initialize currency selector
    initializeCurrency();
    
    // Restore saved section (portfolio or analysis)
    switchSection(AppState.section);
    
    // Fetch exchange rates
    await fetchExchangeRates();
    
    // Pass exchange rates AND currency to portfolio page
    if (elements.portfolioPage) {
        elements.portfolioPage.currency = AppState.currency;
        elements.portfolioPage.exchangeRates = AppState.exchangeRates;
    }
    
    // Initialize toast component
    getToastInstance();
    
    // Fetch AI analyses for ticker dropdown
    await fetchAnalyses();
    
    // Setup all event listeners
    setupEventListeners();
    
    // Start SSE streams for real-time updates
    startAnalysesStream();
    
    // Refresh exchange rates every hour (fallback)
    setInterval(fetchExchangeRates, 3600000);
    
    console.log('✅ App initialized with SSE');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAnalysesStream();
});

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
