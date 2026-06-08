// frontend/js/app.js

import { API } from './api.js';
import { initDashboard, refreshDashboard } from './dashboard.js';
import { initCRUD, refreshCRUD } from './crud.js';
import { initTriage, refreshTriage } from './triage.js';
import { initABTest, refreshABTest } from './ab_test.js';

// Global Application State
export const state = {
  leads: [],          // Raw leads list cache
  selectedLeadId: null, // Active lead ID in CRUD inspector
  triageLeadId: null,   // Active lead ID in triage simulator
  theme: 'dark'         // Current color theme
};

// Global UI Elements
const themeToggleBtn = document.getElementById('theme-toggle');
const refreshAllBtn = document.getElementById('refresh-all-btn');
const apiStatusIndicator = document.querySelector('.status-indicator');
const apiStatusText = document.querySelector('.api-status span:last-child');
const tabButtons = document.querySelectorAll('.nav-item');
const tabPanes = document.querySelectorAll('.tab-pane');
const currentTabTitle = document.getElementById('current-tab-title');
const currentTabSubtitle = document.getElementById('current-tab-subtitle');

// Auth DOM elements
const loginOverlay = document.getElementById('login-overlay');
const loginForm = document.getElementById('login-form');
const loginUsernameInput = document.getElementById('login-username');
const loginPasswordInput = document.getElementById('login-password');
const loginErrorMsg = document.getElementById('login-error');
const loginErrorText = document.getElementById('login-error-text');
const logoutBtn = document.getElementById('logout-btn');

// Tab titles and subtitles for navigation header
const tabMetadata = {
  'dashboard-tab': {
    title: 'Pipeline & Analytics',
    subtitle: 'Track prospective students and check sales metrics'
  },
  'leads-tab': {
    title: 'Lead Operations',
    subtitle: 'Create, update, inspect, and manage lead records'
  },
  'triage-tab': {
    title: 'Message Triage',
    subtitle: 'Simulate inbound communications and classify intent'
  },
  'abtest-tab': {
    title: 'A/B Hypothesis Testing',
    subtitle: 'Evaluate enrollment performance differences between sources'
  }
};

/**
 * Global Toast Alert Notification System
 */
export function showToast(message, type = 'success', duration = 4000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '<i class="fa-solid fa-circle-check"></i>';
  if (type === 'error') icon = '<i class="fa-solid fa-circle-exclamation"></i>';
  if (type === 'info') icon = '<i class="fa-solid fa-circle-info"></i>';
  
  toast.innerHTML = `
    ${icon}
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  }, duration);
}

/**
 * Handle Tab Switching with clean transitions
 */
function switchTab(tabId) {
  // If not authenticated, block navigation actions
  if (!localStorage.getItem('auth_token')) return;

  tabButtons.forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  tabPanes.forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.add('active');
    } else {
      pane.classList.remove('active');
    }
  });

  if (tabMetadata[tabId]) {
    currentTabTitle.textContent = tabMetadata[tabId].title;
    currentTabSubtitle.textContent = tabMetadata[tabId].subtitle;
  }

  if (tabId === 'dashboard-tab') {
    refreshDashboard();
  } else if (tabId === 'leads-tab') {
    refreshCRUD();
  } else if (tabId === 'triage-tab') {
    refreshTriage();
  } else if (tabId === 'abtest-tab') {
    refreshABTest();
  }
}

/**
 * Theme Manager (Light / Dark Mode Toggle)
 */
function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  state.theme = savedTheme;
  if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
    themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
  } else {
    document.body.classList.remove('light-mode');
    themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
  }
}

function toggleTheme() {
  if (state.theme === 'dark') {
    state.theme = 'light';
    document.body.classList.add('light-mode');
    themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    showToast('Switched to Light Mode', 'info', 2000);
  } else {
    state.theme = 'dark';
    document.body.classList.remove('light-mode');
    themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    showToast('Switched to Dark Mode', 'info', 2000);
  }
  localStorage.setItem('theme', state.theme);
  
  const activeTab = document.querySelector('.tab-pane.active');
  if (activeTab && activeTab.id === 'dashboard-tab') {
    refreshDashboard();
  }
}

/**
 * Fetch fresh data cache from the backend API
 */
export async function reloadStateCache() {
  if (!localStorage.getItem('auth_token')) return false;

  try {
    state.leads = await API.getAllLeads();
    apiStatusIndicator.className = 'status-indicator online';
    apiStatusText.textContent = 'API Connected';
    return true;
  } catch (error) {
    console.error('API cache update failed:', error);
    apiStatusIndicator.className = 'status-indicator offline';
    apiStatusText.textContent = 'API Disconnected';
    return false;
  }
}

/**
 * Perform login verification
 */
async function handleLoginSubmit(event) {
  event.preventDefault();
  loginErrorMsg.classList.add('hidden');
  
  const username = loginUsernameInput.value.trim();
  const password = loginPasswordInput.value;

  try {
    const res = await API.login(username, password);
    localStorage.setItem('auth_token', res.access_token);
    
    // Hide overlay, display logout, pull cache, initialize app content
    loginOverlay.classList.add('hidden');
    logoutBtn.style.display = 'block';
    
    showToast('Login successful. Welcome back!', 'success');
    
    await reloadStateCache();
    initDashboard();
    initCRUD();
    initTriage();
    initABTest();
    refreshDashboard();
  } catch (error) {
    console.error('Login failed:', error);
    loginErrorText.textContent = error.message || 'Invalid credentials';
    loginErrorMsg.classList.remove('hidden');
  }
}

/**
 * Log out user
 */
function handleLogout() {
  localStorage.removeItem('auth_token');
  showToast('Logged out successfully.', 'info');
  window.location.reload();
}

/**
 * Initialize all features on load
 */
async function initApp() {
  initTheme();
  themeToggleBtn.addEventListener('click', toggleTheme);

  // Setup tab click event listeners
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  // Setup manual refresh button
  refreshAllBtn.addEventListener('click', async () => {
    if (!localStorage.getItem('auth_token')) return;

    refreshAllBtn.disabled = true;
    const icon = refreshAllBtn.querySelector('i');
    icon.classList.add('fa-spin');
    
    const success = await reloadStateCache();
    if (success) {
      showToast('Successfully refreshed data cache.', 'success');
      const activeTabId = document.querySelector('.tab-pane.active').id;
      switchTab(activeTabId);
    } else {
      showToast('Could not fetch fresh data.', 'error');
    }
    
    icon.classList.remove('fa-spin');
    refreshAllBtn.disabled = false;
  });

  // Setup Logout button
  logoutBtn.addEventListener('click', handleLogout);

  // Setup Login Form submission
  loginForm.addEventListener('submit', handleLoginSubmit);

  // Check login state
  const token = localStorage.getItem('auth_token');
  if (token) {
    loginOverlay.classList.add('hidden');
    logoutBtn.style.display = 'block';
    
    const apiUp = await reloadStateCache();
    if (apiUp) {
      initDashboard();
      initCRUD();
      initTriage();
      initABTest();
      refreshDashboard();
    } else {
      showToast('Backend API is currently offline. Verification pending.', 'error');
    }
  } else {
    loginOverlay.classList.remove('hidden');
    logoutBtn.style.display = 'none';
  }

  // Periodically check API connection
  setInterval(async () => {
    const alive = await API.checkHealth();
    if (alive) {
      apiStatusIndicator.className = 'status-indicator online';
      apiStatusText.textContent = 'API Connected';
    } else {
      apiStatusIndicator.className = 'status-indicator offline';
      apiStatusText.textContent = 'API Offline';
    }
  }, 10000);
}

document.addEventListener('DOMContentLoaded', initApp);
