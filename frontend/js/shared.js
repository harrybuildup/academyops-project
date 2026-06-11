// frontend/js/shared.js

import { API } from './api.js';

// Global Application State
export const state = {
  leads: [],            // Raw leads list cache
  selectedLeadId: null, // Active lead ID in CRUD inspector
  triageLeadId: null,   // Active lead ID in triage simulator
  theme: 'dark'         // Current color theme
};

// Tab Refresh Callbacks Registry (decouples circular imports)
const tabRegistry = {};

/**
 * Register a tab's refresh function
 */
export function registerTab(tabId, refreshFn) {
  tabRegistry[tabId] = refreshFn;
}

/**
 * Execute the registered refresh function for the active tab pane
 */
export function refreshActiveTab() {
  const activeTab = document.querySelector('.tab-pane.active');
  if (activeTab && tabRegistry[activeTab.id]) {
    try {
      tabRegistry[activeTab.id]();
    } catch (e) {
      console.error(`Error refreshing tab ${activeTab.id}:`, e);
    }
  }
}

/**
 * Global Toast Alert Notification System
 */
export function showToast(message, type = 'success', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

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
 * Fetch fresh data cache from the backend API
 */
export async function reloadStateCache() {
  if (!localStorage.getItem('auth_token')) return false;

  const apiStatusIndicator = document.querySelector('.status-indicator');
  const apiStatusText = document.querySelector('.api-status span:last-child');

  try {
    state.leads = await API.getAllLeads();
    if (apiStatusIndicator) apiStatusIndicator.className = 'status-indicator online';
    if (apiStatusText) apiStatusText.textContent = 'API Connected';
    
    // Auto-refresh the active tab
    refreshActiveTab();
    return true;
  } catch (error) {
    console.error('API cache update failed:', error);
    if (apiStatusIndicator) apiStatusIndicator.className = 'status-indicator offline';
    if (apiStatusText) apiStatusText.textContent = 'API Disconnected';
    return false;
  }
}
