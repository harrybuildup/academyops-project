// frontend/js/app.js

import { API } from './api.js';
import { initDashboard, refreshDashboard } from './dashboard.js';
import { initCRUD, refreshCRUD } from './crud.js';
import { initKanban, refreshKanban } from './kanban.js';
import { initTriage, refreshTriage } from './triage.js';
import { initABTest, refreshABTest } from './ab_test.js';
import { initMetrics, refreshMetrics } from './metrics.js';
import { initTeam, refreshTeam, getTokenPayload } from './team.js';
import { initCopilot, refreshCopilot } from './copilot.js';
import { state, showToast, reloadStateCache, registerTab } from './shared.js';

// Global UI Elements
const appContainer   = document.getElementById('app-container');
const themeToggleBtn = document.getElementById('theme-toggle');
const refreshAllBtn  = document.getElementById('refresh-all-btn');
const apiStatusIndicator = document.querySelector('.status-indicator');
const apiStatusText  = document.querySelector('.api-status span:last-child');
const tabButtons     = document.querySelectorAll('.nav-item');
const tabPanes       = document.querySelectorAll('.tab-pane');
const currentTabTitle    = document.getElementById('current-tab-title');
const currentTabSubtitle = document.getElementById('current-tab-subtitle');

// Auth DOM elements
const loginOverlay     = document.getElementById('login-overlay');
const loginForm        = document.getElementById('login-form');
const loginUsernameInput = document.getElementById('login-username');
const loginPasswordInput = document.getElementById('login-password');
const loginErrorMsg    = document.getElementById('login-error');
const loginErrorText   = document.getElementById('login-error-text');
const logoutBtn        = document.getElementById('logout-btn');

// Tab titles and subtitles for navigation header
const tabMetadata = {
  'dashboard-tab': {
    title: 'Pipeline & Analytics',
    subtitle: 'Track prospective students and check sales metrics'
  },
  'kanban-tab': {
    title: 'Admissions Kanban Board',
    subtitle: 'Drag and drop leads to advance their pipeline stages'
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
  },
  'metrics-tab': {
    title: 'Advanced Metrics',
    subtitle: 'Deeper analytical views and lead performance trends'
  },
  'copilot-tab': {
    title: 'AI Copilot',
    subtitle: 'Smart suggestions, message drafting, and lead scoring'
  },
  'settings-tab': {
    title: 'Team Settings',
    subtitle: 'Manage administrative roles and operator status'
  }
};

/**
 * Show the authenticated dashboard (hide login, show app)
 */
function showApp() {
  loginOverlay.style.display = 'none';
  appContainer.style.display = 'flex';
  logoutBtn.style.display = 'flex';
}

/**
 * Show the login screen (hide app, show overlay)
 */
function showLogin() {
  appContainer.style.display = 'none';
  loginOverlay.style.display = 'flex';
  logoutBtn.style.display = 'none';
  if (loginErrorMsg) loginErrorMsg.classList.add('hidden');
  if (loginUsernameInput) loginUsernameInput.value = '';
  if (loginPasswordInput) loginPasswordInput.value = '';
}

/**
 * Update role-based sidebar tab visibility
 */
function updateNavVisibility() {
  const payload = getTokenPayload();
  const settingsBtn = document.getElementById('nav-settings-tab');
  if (settingsBtn) {
    if (payload && payload.role === 'Admin') {
      settingsBtn.style.display = 'block';
    } else {
      settingsBtn.style.display = 'none';
    }
  }
}

/**
 * Handle Tab Switching with clean transitions
 */
function switchTab(tabId) {
  // If not authenticated, block navigation
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
  } else if (tabId === 'kanban-tab') {
    refreshKanban();
  } else if (tabId === 'leads-tab') {
    refreshCRUD();
  } else if (tabId === 'triage-tab') {
    refreshTriage();
  } else if (tabId === 'abtest-tab') {
    refreshABTest();
  } else if (tabId === 'metrics-tab') {
    refreshMetrics();
  } else if (tabId === 'copilot-tab') {
    refreshCopilot();
  } else if (tabId === 'settings-tab') {
    refreshTeam();
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
  } else {
    document.body.classList.remove('light-mode');
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
  } else if (activeTab && activeTab.id === 'metrics-tab') {
    refreshMetrics();
  }
}

/**
 * Fully boot the app after successful authentication
 */
async function bootApp() {
  showApp();
  updateNavVisibility();
  await reloadStateCache();
  initDashboard();
  initCRUD();
  initKanban();
  initTeam();
  initTriage();
  initABTest();
  initMetrics();
  initCopilot();
  refreshDashboard();
}

/**
 * Handle login form submit
 */
async function handleLoginSubmit(event) {
  event.preventDefault();
  loginErrorMsg.classList.add('hidden');

  const username = loginUsernameInput.value.trim();
  const password = loginPasswordInput.value;

  try {
    const res = await API.login(username, password);
    localStorage.setItem('auth_token', res.access_token);
    showToast('Login successful. Welcome back!', 'success');
    await bootApp();
  } catch (error) {
    console.error('Login failed:', error);
    loginErrorText.textContent = error.message || 'Invalid credentials';
    loginErrorMsg.classList.remove('hidden');
  }
}

/**
 * Log out user — clear token and show login
 */
function handleLogout() {
  localStorage.clear();
  showToast('Logged out successfully.', 'info');
  showLogin();
}

/**
 * Initialize application on DOMContentLoaded
 */
async function initApp() {
  // Apply saved theme immediately (before any async work)
  initTheme();

  // Wire up theme toggle icon correctly
  const savedTheme = localStorage.getItem('theme') || 'dark';
  themeToggleBtn.innerHTML = savedTheme === 'light'
    ? '<i class="fa-solid fa-sun"></i>'
    : '<i class="fa-solid fa-moon"></i>';
  themeToggleBtn.addEventListener('click', toggleTheme);

  // Tab navigation
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  // Refresh data button
  refreshAllBtn.addEventListener('click', async () => {
    if (!localStorage.getItem('auth_token')) return;
    refreshAllBtn.disabled = true;
    const icon = refreshAllBtn.querySelector('i');
    icon.classList.add('fa-spin');
    const success = await reloadStateCache();
    if (success) {
      showToast('Successfully refreshed data cache.', 'success');
      const activeTabId = document.querySelector('.tab-pane.active')?.id;
      if (activeTabId) switchTab(activeTabId);
    } else {
      showToast('Could not fetch fresh data.', 'error');
    }
    icon.classList.remove('fa-spin');
    refreshAllBtn.disabled = false;
  });

  // Logout button
  logoutBtn.addEventListener('click', handleLogout);

  // Login form
  loginForm.addEventListener('submit', handleLoginSubmit);

  // START: always show login screen first
  showLogin();

  // Check if there's a stored token and verify it server-side
  const token = localStorage.getItem('auth_token');
  if (token) {
    try {
      await API.verifyToken(); // Throws on 401/invalid
      // Valid — boot the app
      await bootApp();
    } catch {
      // Invalid token — clear and keep showing login
      localStorage.removeItem('auth_token');
      showLogin();
      showToast('Session expired. Please log in again.', 'info');
    }
  }
  // (if no token, showLogin() above already ensures login is visible)

  // Periodic API status check
  setInterval(async () => {
    const alive = await API.checkHealth();
    if (apiStatusIndicator && apiStatusText) {
      if (alive) {
        apiStatusIndicator.className = 'status-indicator online';
        apiStatusText.textContent = 'API Connected';
      } else {
        apiStatusIndicator.className = 'status-indicator offline';
        apiStatusText.textContent = 'API Offline';
      }
    }
  }, 10000);
}

document.addEventListener('DOMContentLoaded', initApp);
